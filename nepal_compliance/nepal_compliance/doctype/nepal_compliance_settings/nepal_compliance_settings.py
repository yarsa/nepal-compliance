# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.core.doctype.user_permission.user_permission import get_user_permissions
from frappe.model.document import Document
from frappe.utils import flt
import redis

from nepal_compliance.tax_templates import (
    EXCISE_VARIANTS,
    VARIANTS,
    is_managed_template,
    set_default_tax_template,
    sync_nepal_tax_templates,
)
from nepal_compliance.utils import (
    get_or_create_vat_exempt_template,
    sync_managed_vat_taxable_templates,
)


class NepalComplianceSettings(Document):
    def validate(self):
        """Validate each configured VAT account row (child validate is not auto-run by Frappe)."""
        self._validate_party_tax_id_rules()
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
    if not row.get("excise_account") and set(variants) & set(EXCISE_VARIANTS):
        frappe.throw(
            _("Company {0} has no Excise Duty Account, so the Excise + VAT templates cannot be made. Set one and save first, or leave the excise templates unticked.").format(
                frappe.bold(company)
            ),
            title=_("Excise Account Missing"),
        )

    return sync_nepal_tax_templates(
        company,
        row.sales_vat_account,
        row.purchase_vat_account,
        row.get("excise_account"),
        variants=variants,
        create=True,
    )
