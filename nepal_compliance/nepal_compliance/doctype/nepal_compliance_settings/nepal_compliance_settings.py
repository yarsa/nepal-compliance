# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.model.document import Document
import redis

class NepalComplianceSettings(Document):
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
        changed = False
        kept = False
        for tax in list(vat_rows):
            if not kept:
                if tax.account_head != vat_account:
                    tax.account_head = vat_account
                    changed = True
                kept = True
            else:
                template.taxes.remove(tax)
                changed = True
        if changed:
            template.save(ignore_permissions=True)
        return changed