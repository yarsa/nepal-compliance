# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = [
		{'fieldname': 'posting_date','label': _('Date'),'fieldtype': 'Date'},
		{'fieldname': 'nepali_date','label': _('Nepali Date'),'fieldtype': 'Data'},
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
		{'fieldname': 'expense_account', 'label': _('Expense Account'), 'fieldtype': 'Link', 'options': 'Account'},
		{'fieldname': 'distribute_charges_based_on', 'label': _('Distributed Charge Based On'), 'fieldtype': 'Data'},
		{'fieldname': 'grand_total','label': _('Total Tax and Charges'),'fieldtype': 'Currency','options': 'Company:company:default_currency'}
	]
	data = []
	conditions = {"docstatus":["IN", [1, 0]]}
	if filters.get("company"):
		conditions["company"] = filters["company"]
	if filters.get("supplier"):
		conditions["supplier"] = filters["supplier"]
	if filters.get("posting_date"):
		conditions["posting_date"] = filters["posting_date"]
	if filters.get("nepali_date"):
		nepali_date_filter = f"%{filters['nepali_date']}%"
		conditions["nepali_date"] = ["like", nepali_date_filter]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]
	elif filters.get("from_date"):
		conditions["posting_date"] = [">=", filters["from_date"]]
	elif filters.get("to_date"):
		conditions["posting_date"] = ["<=", filters["to_date"]]
	if filters.get("distribute_charges_based_on"):
		conditions["distribute_charges_based_on"] = filters["distribute_charges_based_on"]
	if filters.get("expense_account"):
		conditions["expense_account"] = filters["expense_account"]
	if filters.get("receipt_document_type"):
		conditions["receipt_document_type"] = filters["receipt_document_type"]
	if filters.get("document_number"):
		conditions["name"] = filters["document_number"]
	landed_cost = frappe.db.get_list("Landed Cost Voucher", filters = conditions, fields=['*'])
	for land in landed_cost:
		items = frappe.db.get_all("Landed Cost Item", filters = {"parent": land.name}, fields=['*'])
		receipts = frappe.db.get_all("Landed Cost Purchase Receipt", filters = {"parent": land.name}, fields=['*'])
		taxes = frappe.db.get_all("Landed Cost Taxes and Charges", filters = {"parent": land.name}, fields=['*'])
		for item in items:
			for r in receipts:
				grand_totals = 0
			for t in taxes: 
				data.append([land.posting_date, land.nepali_date, land.name, item.receipt_document_type, item.receipt_document, item.item_code, item.description, item.qty, item.rate, item.amount, item.applicable_charges, r.supplier, t.expense_account, land.distribute_charges_based_on, land.total_taxes_and_charges])
	return columns, data