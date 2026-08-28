# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
import redis

class NepalComplianceSettings(Document):
    def validate(self):
        """Validate each configured VAT account row (child validate is not auto-run by Frappe)."""
        for row in self.get("vat_accounts") or []:
            row.validate()

    def on_update(self):
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
        updated = []
        for row in self.get("vat_accounts") or []:
            if not row.company:
                continue
            for doctype, account in (
                ("Sales Taxes and Charges Template", row.sales_vat_account),
                ("Purchase Taxes and Charges Template", row.purchase_vat_account),
            ):
                if not account:
                    continue
                for template_name in frappe.get_all(doctype, filters={"company": row.company}, pluck="name"):
                    if self._repoint_template_vat_rows(doctype, template_name, account):
                        updated.append(template_name)
        if updated:
            frappe.msgprint(
                _("VAT rows in the following tax templates were updated to the configured accounts: {0}").format(
                    ", ".join(frappe.bold(name) for name in updated)
                ),
                indicator="green",
                alert=True,
            )

    @staticmethod
    def _repoint_template_vat_rows(doctype, template_name, vat_account):
        template = frappe.get_doc(doctype, template_name)
        vat_rows = [tax for tax in template.taxes if tax.account_head and "vat" in tax.account_head.lower()]
        if not vat_rows:
            return False

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

        if changed:
            template.save(ignore_permissions=True)
        return changed