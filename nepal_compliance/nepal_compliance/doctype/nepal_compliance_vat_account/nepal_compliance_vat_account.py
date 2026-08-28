# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.model.document import Document


class NepalComplianceVATAccount(Document):
	def validate(self):
		"""Require the selected VAT accounts to belong to the row's company and be Tax ledgers."""
		for fieldname, label in (
			("sales_vat_account", _("Sales VAT Account")),
			("purchase_vat_account", _("Purchase VAT Account")),
		):
			account = self.get(fieldname)
			if not account:
				continue
			account_company, account_type, is_group = frappe.get_cached_value(
				"Account", account, ["company", "account_type", "is_group"]
			)
			if account_company != self.company:
				frappe.throw(
					_("Row {0}: {1} {2} does not belong to Company {3}").format(
						self.idx, label, frappe.bold(account), frappe.bold(self.company)
					),
					title=_("Invalid Account"),
				)
			if is_group:
				frappe.throw(
					_("Row {0}: {1} {2} is a Group Account. Please select a ledger account.").format(
						self.idx, label, frappe.bold(account)
					),
					title=_("Invalid Account"),
				)
			if account_type != "Tax":
				frappe.throw(
					_(
						"Row {0}: {1} {2} has Account Type '{3}'. Please select an account with Account Type 'Tax'."
					).format(self.idx, label, frappe.bold(account), account_type or _("None")),
					title=_("Invalid Account"),
				)
