# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	columns = [
		{
			'fieldname': 'posting_date',
			'label': _('Date'),
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'nepali_date',
			'label': _('Nepali Date'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'invoice_no',
			'label': _('Invoice No'),
			'fieldtype': 'Link',
			'options': 'Sales Invoice'
		},
		{
			'fieldname': 'customer',
			'label': _('Customer'),
			'fieldtype': 'Link',
			'options': 'Customer'
		},
		{
			'fieldname': 'customer_group',
			'label': _('Customer Group'),
			'fiedltype': 'Link',
			'options': 'Customer Group'
		},
		{
			'fiedlname': 'project',
			'label': _('Project'),
			'fieldtype': 'Link',
			'options': 'Project'
		},
		{
			'fieldname': 'cost_center',
			'label': _('Cost Center'),
			'fiedltype': 'Link',
			'options': 'Cost Center'
		},
		{
			'fieldname': 'vat_no',
			'label': _('Vat/Pan No.'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'owner',
			'label': 'Owner',
			'fieldtype': 'Data',
		},
		{
			'fieldname': 'qty',
			'label': _('Quantity'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'total',
			'label': _('Total'),
			'fiedltype': 'Currency'
		},
		{
			'fiedlname': 'discount',
			'label': _('Discount'),
			'fieldtype': 'Currency'
		},
        {
            'fieldname': 'gross_total',
            'label': _('Gross Amount'),
            'fieldtype': 'Currency'
        },
		{
			'fiedlname': 'net_total',
			'label': _('Net Amount'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'vat',
			'label': _('VAT'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'tds',
			'label': _('TDS'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'total_taxes_and_charges',
			'label': _('Total Tax and Charges'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'total_advance',
			'label': _('Total Advance'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'grand_total',
			'label': _('Grand Total'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'rounded_total',
			'label': _('Rounded Total'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'outstanding_amount',
			'label': _('Outstanding Amount'),
			'fieldtype': 'Currency'
		}
	]
	
	data = []
	conditions = {"docstatus": 1, "is_return": 0}
	if filters.get("company"):
		conditions["company"] = filters["company"]
	if filters.get("from_date") and filters.get("to_date"):
		conditions["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]
	elif filters.get("from_date"):
		conditions["posting_date"] = [">=", filters["from_date"]]
	elif filters.get("to_date"):
		conditions["posting_date"] = ["<=", filters["to_date"]]
	if filters.get("nepali_date"):
		nepali_date_filter = f"%{filters['nepali_date']}%"
		conditions["nepali_date"] = ["like", nepali_date_filter]
	if filters.get("customer"):
		conditions["customer"] = filters["customer"]
	if filters.get("customer_group"):
		conditions["customer_group"] = filters["customer_group"]
	if filters.get("owner"):
		conditions["owner"] = filters["owner"]
	if filters.get("cost_center"):
		conditions["cost_center"] = filters["cost_center"]
	if filters.get("project"):
		conditions["project"] = filters["project"]
	if filters.get("document_number"):
		conditions["name"] = filters["document_number"]


	sales_invoice = frappe.db.get_list("Sales Invoice", filters = conditions, fields=['*'])
	for sale in sales_invoice:
		items = frappe.db.get_all("Sales Invoice Item", filters={"parent":sale.name}, fields=['*'])
		taxes = frappe.db.get_all("Sales Taxes and Charges", filters={"parent":sale.name}, fields=['*'])
		total_qty = 0
		total_rate = 0
		vat = 0
		tds = 0
		invoice_total = sale.grand_total
		net_total = sale.net_total if sale.net_total else invoice_total
		for item in items:
			total_qty += item.qty	
			total_rate += item.rate
		for tax in taxes:
			if tax.rate == 13:
				vat = tax.tax_amount
			elif tax.rate in [1.5, 15]:
				tds = tax.tax_amount
		data.append([sale.posting_date, sale.nepali_date, sale.name, sale.customer, sale.customer_group, sale.project, sale.cost_center, sale.vat_number, sale.owner, total_qty, sale.total, sale.discount_amount,sale.total, net_total, vat, tds, sale.total_taxes_and_charges, sale.total_advance, sale.grand_total, sale.rounded_total, sale.outstanding_amount])
	return columns, data
    