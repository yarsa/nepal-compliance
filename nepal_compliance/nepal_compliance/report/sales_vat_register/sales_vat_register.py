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
			'fieldtype': 'Link',
			'options': 'Customer Group'
		},
		{
			'fieldname': 'project',
			'label': _('Project'),
			'fieldtype': 'Link',
			'options': 'Project'
		},
		{
			'fieldname': 'cost_center',
			'label': _('Cost Center'),
			'fieldtype': 'Link',
			'options': 'Cost Center'
		},
		{
			'fieldname': 'vat_no',
			'label': _('Vat/Pan No.'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'owner',
			'label': _('Owner'),
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
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'discount',
			'label': _('Discount'),
			'fieldtype': 'Currency'
		},
        {
            'fieldname': 'gross_total',
            'label': _('Gross Amount'),
            'fieldtype': 'Currency'
        },
		{
			'fieldname': 'net_total',
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
	query = """
		SELECT DISTINCT si.*
		FROM `tabSales Invoice` si
		LEFT JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		WHERE si.docstatus = 1 AND si.is_return = 0
	"""
	conditions = []
	values = []

	if filters.get("company"):
		conditions.append("si.company = %s")
		values.append(filters["company"])

	if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
		conditions.append("si.posting_date >= %s AND si.posting_date <= %s")
		values.extend([filters["from_nepali_date"], filters["to_nepali_date"]])
	elif filters.get("from_nepali_date"):
		conditions.append("si.posting_date >= %s")
		values.append(filters["from_nepali_date"])
	elif filters.get("to_nepali_date"):
		conditions.append("si.posting_date <= %s")
		values.append(filters["to_nepali_date"])

	if filters.get("customer"):
		conditions.append("si.customer = %s")
		values.append(filters["customer"])
	if filters.get("customer_group"):
		conditions.append("si.customer_group = %s")
		values.append(filters["customer_group"])
	if filters.get("owner"):
		conditions.append("si.owner = %s")
		values.append(filters["owner"])
	if filters.get("cost_center"):
		conditions.append("si.cost_center = %s")
		values.append(filters["cost_center"])
	if filters.get("project"):
		conditions.append("si.project = %s")
		values.append(filters["project"])
	if filters.get("document_number"):
		conditions.append("si.name = %s")
		values.append(filters["document_number"])

	if conditions:
		query += " AND " + " AND ".join(conditions)

	query += " ORDER BY si.modified DESC"

	sales_invoice = frappe.db.sql(query, values, as_dict=True)
	for sale in sales_invoice:
		items = frappe.get_all("Sales Invoice Item", filters={"parent":sale.name}, fields=['*'])
		taxes = frappe.get_all("Sales Taxes and Charges", filters={"parent":sale.name}, fields=['*'])
		total_qty = 0
		total_rate = 0
		vat = 0
		tds = 0
		invoice_total = sale.grand_total
		net_total = sale.net_total if sale.net_total else invoice_total
		gross_total = sale.total + (sale.discount_amount or 0)
		for item in items:
			total_qty += item.qty	
			total_rate += item.rate
		for tax in taxes:
			if tax.rate == 13:
				vat = tax.tax_amount_after_discount_amount if tax.tax_amount_after_discount_amount is not None else tax.tax_amount
			elif tax.rate in [1.5, 15]:
				tds = tax.tax_amount_after_discount_amount if tax.tax_amount_after_discount_amount is not None else tax.tax_amount
		data.append([sale.posting_date, sale.name, sale.customer, sale.customer_group, sale.project, sale.cost_center, sale.vat_number if sale.vat_number else sale.tax_id, sale.owner, total_qty, sale.total, sale.discount_amount, gross_total, net_total, vat, tds, sale.total_taxes_and_charges, sale.total_advance, sale.grand_total, sale.rounded_total, sale.outstanding_amount])
	return columns, data
