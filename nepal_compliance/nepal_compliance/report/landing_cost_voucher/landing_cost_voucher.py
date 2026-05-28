# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{'fieldname': 'posting_date','label': _('Date'),'fieldtype': 'Date'},
		{'fieldname': 'voucher_no','label': _('Voucher Number'),'fieldtype': 'Link','options': 'Landed Cost Voucher'},
		{'fieldname': 'receipt_document_type','label': _('Voucher type'),'fieldtype': 'Select','options': '\nPurchase Invoice\nPurchase Receipt',},
		{'fieldname': 'receipt_document','label': _('Voucher'),'fieldtype': 'Dynamic Link','options': 'receipt_document_type'},
		{'fieldname': 'item_code','label': _('Item Code'),'fieldtype': 'Link','options': 'Item'},
		{'fieldname': 'description','label': _('Description'),'fieldtype': 'Text Editor'},
		{'fieldname': 'qty','label': _('Quantity'),'fieldtype': 'Float'},
		{'fieldname': 'rate','label': _('Rate'),'fieldtype': 'Currency'},
		{'fieldname': 'amount','label': _('Amount'),'fieldtype': 'Currency'},
		{'fieldname': 'applicable_charges','label': _('Applicable Charges'),'fieldtype': 'Currency'},
		{'fieldname': 'supplier','label': _('Supplier'),'fieldtype': 'Link','options': 'Supplier'},
		{'fieldname': 'supplier_vat_number', 'label': _('VAT/PAN Number'), 'fieldtype': 'Data'},
		{'fieldname': 'expense_account', 'label': _('Expense Account'), 'fieldtype': 'Link', 'options': 'Account'},
		{'fieldname': 'distribute_charges_based_on', 'label': _('Distributed Charge Based On'), 'fieldtype': 'Data'},
		{'fieldname': 'grand_total','label': _('Total Tax and Charges'),'fieldtype': 'Currency','options': 'Company:company:default_currency'}
	]
	query = """
    SELECT DISTINCT lc.*
    FROM `tabLanded Cost Voucher` lc
    LEFT JOIN `tabLanded Cost Purchase Receipt` lcc ON lc.name = lcc.parent
	LEFT JOIN `tabLanded Cost Taxes and Charges` lctc ON lc.name = lctc.parent
    WHERE lc.docstatus = 1
	"""

	conditions = []
	values = []

	if filters.get("company"):
		conditions.append("lc.company = %s")
		values.append(filters["company"])
	if filters.get("supplier"):
		conditions.append("lcc.supplier = %s")
		values.append(filters["supplier"])
	if filters.get("distribute_charges_based_on"):
		conditions.append("lc.distribute_charges_based_on = %s")
		values.append(filters["distribute_charges_based_on"])
	if filters.get("expense_account"):
		conditions.append("lctc.expense_account = %s")
		values.append(filters["expense_account"])
	if filters.get("receipt_document_type"):
		conditions.append("lcc.receipt_document_type = %s")
		values.append(filters["receipt_document_type"])
	if filters.get("document_number"):
		conditions.append("lc.name = %s")
		values.append(filters["document_number"])
	if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
		conditions.append("lc.posting_date BETWEEN %s AND %s")
		values.extend([filters["from_nepali_date"], filters["to_nepali_date"]])
	elif filters.get("from_nepali_date"):
		conditions.append("lc.posting_date >= %s")
		values.append(filters["from_nepali_date"])
	elif filters.get("to_nepali_date"):
		conditions.append("lc.posting_date <= %s")
		values.append(filters["to_nepali_date"])


	if conditions:
		query += " AND " + " AND ".join(conditions)

	query += " ORDER BY modified DESC"

	landed_cost = frappe.db.sql(query, values, as_dict=True)
	data = []
	for land in landed_cost:
		items = frappe.db.get_all("Landed Cost Item", filters = {"parent": land.name}, fields=['*'])
		receipts = frappe.db.get_all("Landed Cost Purchase Receipt", filters = {"parent": land.name}, fields=['*'])
		taxes = frappe.db.get_all("Landed Cost Taxes and Charges", filters = {"parent": land.name}, fields=['*'])
		for item in items:
			for r in receipts:
				supplier_vat_number = frappe.db.get_value("Supplier", r.supplier, "supplier_vat_number")
				grand_totals = 0
			for t in taxes: 
				data.append([land.posting_date, land.name, item.receipt_document_type, item.receipt_document, item.item_code, item.description, item.qty, item.rate, item.amount, item.applicable_charges, r.supplier, supplier_vat_number, t.expense_account, land.distribute_charges_based_on, land.total_taxes_and_charges])
	return columns, data