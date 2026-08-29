# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.core.doctype.user_permission.user_permission import get_user_permissions
from frappe.model.document import Document
from frappe.utils import flt
import redis


class NepalComplianceSettings(Document):
    def validate(self):
        """Validate each configured VAT account row (child validate is not auto-run by Frappe)."""
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
        """Repoint VAT rows in each company's tax templates to the configured accounts."""
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
                    result = self._repoint_template_vat_rows(
                        doctype, template_name, account, row.company
                    )
                    if result == "updated":
                        updated.append(template_name)
                    elif result == "skipped":
                        skipped.append(template_name)
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
