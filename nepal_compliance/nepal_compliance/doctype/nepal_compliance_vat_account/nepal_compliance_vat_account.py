# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.model.document import Document


class NepalComplianceVATAccount(Document):
	def validate(self):
		"""Require the selected accounts and tax templates to belong to the row's company.

		Accounts must be ledgers rather than groups, and all but the TDS Receivable Account must be Tax ledgers.
		"""
		for fieldname, label in (
			("sales_vat_account", _("Sales VAT Account")),
			("purchase_vat_account", _("Purchase VAT Account")),
			("excise_account", _("Excise Duty Account")),
			("tds_receivable_account", _("TDS Receivable Account")),
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
			if account_type != "Tax" and fieldname != "tds_receivable_account":
				frappe.throw(
					_(
						"Row {0}: {1} {2} has Account Type '{3}'. Please select an account with Account Type 'Tax'."
					).format(self.idx, label, frappe.bold(account), account_type or _("None")),
					title=_("Invalid Account"),
				)

		for fieldname, doctype, label in (
			("default_sales_tax_template", "Sales Taxes and Charges Template", _("Default Sales Tax Template")),
			("default_purchase_tax_template", "Purchase Taxes and Charges Template", _("Default Purchase Tax Template")),
		):
			template = self.get(fieldname)
			if not template:
				continue
			if frappe.get_cached_value(doctype, template, "company") != self.company:
				frappe.throw(
					_("Row {0}: {1} {2} does not belong to Company {3}").format(
						self.idx, label, frappe.bold(template), frappe.bold(self.company)
					),
					title=_("Invalid Tax Template"),
				)
