# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.core.doctype.user_permission.user_permission import get_user_permissions
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.model.document import Document
from frappe.utils import cint, flt
import redis

from nepal_compliance.form_layout import apply_form_layout, get_extra_field_candidates
from nepal_compliance.tax_templates import (
    EXCISE_VARIANTS,
    VARIANTS,
    get_item_rate_excise_account,
    is_managed_template,
    set_default_tax_template,
    sync_nepal_tax_templates,
)
from nepal_compliance.utils import (
    get_or_create_vat_exempt_template,
    sync_managed_vat_taxable_templates,
)


class NepalComplianceSettings(Document):
    def onload(self):
        # Customize Form can change the default too, so show the one in effect.
        self.sales_invoice_print_format = frappe.get_meta("Sales Invoice").default_print_format or None
        # The form posts __onload back when it saves, which tells a form save
        # (compared against the value shown here) from a save in code.
        self.set_onload("shows_sales_invoice_print_format", 1)

    def validate(self):
        """Validate each configured VAT account row (child validate is not auto-run by Frappe)."""
        self._validate_party_tax_id_rules()
        self._validate_essentials_extra_fields()
        self._validate_print_rows()
        seen_companies = set()
        for row in self.get("vat_accounts") or []:
            if row.company:
                if row.company in seen_companies:
                    frappe.throw(
                        _("Row {0}: VAT accounts are already configured for Company {1}. Each company can have only one row.").format(
                            row.idx, frappe.bold(row.company)
                        ),
                        title=_("Duplicate Company"),
                    )
                seen_companies.add(row.company)
            row.validate()

    def _validate_party_tax_id_rules(self):
        """Require complete, unique party rules when the Tax ID check is enabled."""
        if not self.get("enable_party_tax_id_check"):
            return

        tables = (
            ("customer_tax_id_rules", "customer_type", "customer_group", _("Customer")),
            ("supplier_tax_id_rules", "supplier_type", "supplier_group", _("Supplier")),
        )
        for table, type_field, group_field, label in tables:
            rows = self.get(table) or []
            if not rows:
                frappe.throw(
                    _("Add at least one {0} Type or Group for the Tax ID check.").format(label)
                )

            seen = set()
            for row in rows:
                value_field = type_field if row.match_by == "Type" else group_field
                value = row.get(value_field)
                if row.match_by not in ("Type", "Group") or not value:
                    frappe.throw(
                        _("Row {0}: select a valid {1} Type or Group.").format(
                            row.idx, label
                        )
                    )
                key = (row.match_by, value)
                if key in seen:
                    frappe.throw(
                        _("Row {0}: duplicate {1} rule {2}.").format(
                            row.idx, label, frappe.bold(value)
                        )
                    )
                seen.add(key)

    def _validate_print_rows(self):
        """One print format per company, and one stamp and signature row per format and company."""
        seen = set()
        for row in self.get("company_print_formats") or []:
            if row.company in seen:
                frappe.throw(
                    _("Row {0}: Company {1} already has a print format.").format(row.idx, frappe.bold(row.company)),
                    title=_("Duplicate Company"),
                )
            seen.add(row.company)
            if frappe.db.get_value("Print Format", row.print_format, "doc_type") != "Sales Invoice":
                frappe.throw(
                    _("Row {0}: {1} is not a Sales Invoice print format.").format(row.idx, frappe.bold(row.print_format))
                )
        seen = set()
        for row in self.get("print_seals") or []:
            key = (row.print_format, row.company or "")
            if key in seen:
                frappe.throw(
                    _("Row {0}: {1} already has stamp and signature settings for {2}.").format(
                        row.idx, frappe.bold(row.print_format), row.company or _("every company")
                    ),
                    title=_("Duplicate Row"),
                )
            seen.add(key)

    def _validate_essentials_extra_fields(self):
        """Allow each extra Nepal Essentials field once, and only a field that form can show."""
        candidates, seen = {}, set()
        for row in self.get("essentials_extra_fields") or []:
            if row.document_type not in candidates:
                candidates[row.document_type] = get_extra_field_candidates(row.document_type)
            label = candidates[row.document_type].get(row.fieldname)
            if not label:
                frappe.throw(
                    _("Row {0}: {1} cannot be added to Nepal Essentials on {2}.").format(
                        row.idx, frappe.bold(row.fieldname), row.document_type
                    )
                )
            if (row.document_type, row.fieldname) in seen:
                frappe.throw(
                    _("Row {0}: {1} is already added for {2}.").format(row.idx, frappe.bold(label), row.document_type)
                )
            seen.add((row.document_type, row.fieldname))
            row.field_label = label

    def _form_layout_changed(self):
        """Whether the Nepal Essentials tab setting or its extra fields changed in this save."""

        def layout(doc):
            rows = doc.get("essentials_extra_fields") or []
            return cint(doc.get("use_nepal_essentials_tab")), [(r.document_type, r.fieldname) for r in rows]

        before = self.get_doc_before_save()
        return before is None or layout(before) != layout(self)

    def _removed_essentials_fields(self):
        """Extra Nepal Essentials fields taken off the list in this save, by doctype."""
        before = self.get_doc_before_save()
        current = {(r.document_type, r.fieldname) for r in self.get("essentials_extra_fields") or []}
        removed = {}
        for row in (before and before.get("essentials_extra_fields")) or []:
            if (row.document_type, row.fieldname) not in current:
                removed.setdefault(row.document_type, []).append(row.fieldname)
        return removed

    def on_update(self):
        """Clear cached date settings and sync VAT accounts into company tax templates."""
        cache = frappe.cache()
        for key in (
            "nepal_compliance:bs_enabled",
            "nepal_compliance:date_format",
        ):
            try:
                cache.delete_key(key)
            except redis.exceptions.RedisError:
                frappe.log_error(f"Failed to clear cache key: {key}", "Nepal Compliance")
        self.sync_vat_accounts_to_templates()
        self.sync_sales_invoice_print_format()
        if self._form_layout_changed():
            apply_form_layout(self, self._removed_essentials_fields())

    def sync_sales_invoice_print_format(self):
        """Make the chosen format Sales Invoice's default print format.

        Writes the same Property Setter as Customize Form. A form save is
        compared against the default it showed, so clearing the field removes a
        default set in Customize Form. A save from code that never loaded the
        form only writes a changed value, so it cannot undo that default.
        """
        from_form = (self.get("__onload") or {}).get("shows_sales_invoice_print_format")
        if not from_form and not self.has_value_changed("sales_invoice_print_format"):
            return
        print_format = self.sales_invoice_print_format or None
        if print_format == (frappe.get_meta("Sales Invoice").default_print_format or None):
            return
        if print_format:
            make_property_setter(
                "Sales Invoice", None, "default_print_format", print_format, "Data", for_doctype=True
            )
        else:
            delete_property_setter("Sales Invoice", "default_print_format")
        frappe.clear_cache(doctype="Sales Invoice")

    def sync_vat_accounts_to_templates(self):
        """Sync each company's tax templates with the configured accounts.

        Repoints VAT rows in existing templates, repairs the managed Nepal
        templates that exist (they are created only from the Create Tax
        Templates button), and applies the chosen default for each side.
        """
        updated = []
        skipped = []
        for row in self.get("vat_accounts") or []:
            if not row.company:
                continue
            for doctype, account in (
                ("Sales Taxes and Charges Template", row.sales_vat_account),
                ("Purchase Taxes and Charges Template", row.purchase_vat_account),
            ):
                if not account:
                    continue
                for template_name in frappe.get_list(
                    doctype, filters={"company": row.company}, pluck="name"
                ):
                    if is_managed_template(doctype, template_name):
                        # sync_nepal_tax_templates owns these; the generic
                        # reconciler below would repoint an edited rate or drop a
                        # deliberate second row.
                        continue
                    result = self._repoint_template_vat_rows(
                        doctype, template_name, account, row.company
                    )
                    if result == "updated":
                        updated.append(template_name)
                    elif result == "skipped":
                        skipped.append(template_name)
                side = "sales" if doctype.startswith("Sales") else "purchase"
                sync_managed_vat_taxable_templates(row.company, account, side)
                get_or_create_vat_exempt_template(row.company, account, side)
            sync_nepal_tax_templates(
                row.company,
                row.sales_vat_account,
                row.purchase_vat_account,
                row.get("excise_account"),
            )
            for template_side, template in (
                ("sales", row.get("default_sales_tax_template")),
                ("purchase", row.get("default_purchase_tax_template")),
            ):
                set_default_tax_template(row.company, template_side, template)
        if updated:
            frappe.msgprint(
                _("VAT rows in the following tax templates were updated to the configured accounts: {0}").format(
                    ", ".join(frappe.bold(name) for name in updated)
                ),
                indicator="green",
                alert=True,
            )
        if skipped:
            frappe.msgprint(
                _(
                    "{0} tax template(s) were not updated because you do not have write access for their company."
                ).format(len(skipped)),
                indicator="orange",
                alert=True,
            )

    @staticmethod
    def _is_vat_tax_row(tax, vat_account):
        """True when the tax row is the configured VAT ledger or a named VAT row."""
        if not tax.account_head:
            return False
        if tax.account_head == vat_account:
            return True
        return "vat" in tax.account_head.lower()

    @staticmethod
    def _user_may_write_company_template(template, company):
        """Whether this user may save a tax template for the configured company.

        Direct DocType write is preferred. Otherwise a company-scoped delegation
        applies: the user can write Nepal Compliance Settings, the template
        belongs to the VAT-account row's company, and User Permissions (when
        present) include that company.
        """
        if frappe.has_permission(template.doctype, "write", doc=template):
            return "direct"
        if not frappe.has_permission("Nepal Compliance Settings", "write"):
            return None
        if getattr(template, "company", None) != company:
            return None
        company_perms = get_user_permissions().get("Company") or []
        if company_perms:
            allowed = {perm.get("doc") for perm in company_perms}
            if template.company not in allowed:
                return None
        return "delegated"

    @classmethod
    def _save_company_template(cls, template, company):
        """Save a tax template using write permission or company-scoped delegation."""
        mode = cls._user_may_write_company_template(template, company)
        if mode == "direct":
            template.save()
            return True
        if mode == "delegated":
            # Company-scoped delegation: Settings writers may update templates
            # only for companies they just configured, subject to User Permissions.
            template.save(ignore_permissions=True)
            return True
        return False

    @classmethod
    def _repoint_template_vat_rows(cls, doctype, template_name, vat_account, company):
        """Update matching VAT rows on one template. Returns updated/skipped/unchanged."""
        template = frappe.get_doc(doctype, template_name)
        vat_rows = [tax for tax in template.taxes if cls._is_vat_tax_row(tax, vat_account)]
        if not vat_rows:
            return "unchanged"

        changed = False
        primary = next((tax for tax in vat_rows if tax.account_head == vat_account), vat_rows[0])
        if primary.account_head != vat_account:
            primary.account_head = vat_account
            changed = True

        for tax in vat_rows:
            if tax is primary:
                continue
            # Only remove rows that are exact duplicates of the primary VAT row.
            # Rows with a different charge type, rate or amount serve a distinct
            # purpose (e.g. a manual VAT adjustment) and must be preserved.
            is_duplicate = (
                tax.charge_type == primary.charge_type
                and flt(tax.rate) == flt(primary.rate)
                and flt(tax.get("tax_amount")) == flt(primary.get("tax_amount"))
            )
            if is_duplicate:
                template.taxes.remove(tax)
                changed = True

        if not changed:
            return "unchanged"
        if not cls._save_company_template(template, company):
            return "skipped"
        return "updated"


@frappe.whitelist()
def create_nepal_tax_templates(company: str, variants: str | list | None = None):
    """Create the chosen managed Nepal tax templates for one configured company."""
    frappe.has_permission("Nepal Compliance Settings", "write", throw=True)
    frappe.has_permission("Company", "read", doc=company, throw=True)
    variants = frappe.parse_json(variants) if variants else list(VARIANTS)
    unknown = set(variants) - set(VARIANTS)
    if unknown:
        frappe.throw(_("Unknown tax template variant: {0}").format(", ".join(sorted(unknown))))

    settings = frappe.get_single("Nepal Compliance Settings")
    row = next((r for r in settings.get("vat_accounts") or [] if r.company == company), None)
    if not row or not (row.sales_vat_account or row.purchase_vat_account):
        frappe.throw(
            _("Set the VAT accounts for Company {0} in the VAT Accounts table and save first.").format(
                frappe.bold(company)
            ),
            title=_("VAT Accounts Missing"),
        )
    excise_account = row.get("excise_account")
    folds_excise = not excise_account or not row.get("record_excise_separately")
    if folds_excise and "excise_inclusive" in variants:
        frappe.throw(
            _("Company {0} adds excise to the item rates (no excise licence), which needs prices that exclude tax. Untick Excise + VAT 13%, price includes tax.").format(
                frappe.bold(company)
            ),
            title=_("Inclusive Excise Not Supported"),
        )
    if not excise_account and set(variants) & set(EXCISE_VARIANTS):
        excise_account = get_item_rate_excise_account(
            company, create_beside=row.purchase_vat_account or row.sales_vat_account
        )

    return sync_nepal_tax_templates(
        company,
        row.sales_vat_account,
        row.purchase_vat_account,
        excise_account,
        variants=variants,
        create=True,
    )
