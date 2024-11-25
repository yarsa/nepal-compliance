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
			'fieldname': 'customer_address',
			'label': _('Customer Address'),
			'fiedltype': 'Data'
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
			'label': _('Vat No'),
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
			'fieldname': 'rate',
			'label': _('Rate'),
			'fieldtype': 'float'
		},
		{
			'fieldname': 'total',
			'label': _('Total'),
			'fiedltype': 'Data'
		},
		{
			'fiedlname': 'discount',
			'label': _('Discount'),
			'fieldtype': 'Currency'
		},
		{
			'fiedlname': 'net_total',
			'label': _('Net Total'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'charge_type',
			'label': _('Charge Type'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'account_head',
			'label': _('Account Head'),
			'fieldtype': 'link',
			'options': 'Account'
		},
		{
			'fieldname': 'vat',
			'label': _('VAT'),
			'fieldtype': 'Float'
		},
		{
			'fieldname': 'tds',
			'label': _('TDS'),
			'fieldtype': 'Float'
		},
		{
			'fieldname': 'total_taxes_and_charges',
			'label': _('Total Tax and Charges'),
			'fieldtype': 'Float'
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
			'fieldname': 'total_advance',
			'label': _('Total Advance'),
			'fieldtype': 'Currency'
		},
		{
			'fieldname': 'outstanding_amount',
			'label': _('Outstanding Amount'),
			'fieldtype': 'Currency'
		}
	]
	
	data = []
	conditions = {"docstatus": 1, "is_return": 1}
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
	if filters.get("returned_invoice"):
		conditions["name"] = filters["returned_invoice"]


	sales_invoice = frappe.db.get_list("Sales Invoice", filters = conditions, fields=['*'])
	for sale in sales_invoice:
		items = frappe.db.get_all("Sales Invoice Item", filters={"parent":sale.name}, fields=['*'])
		taxes = frappe.db.get_all("Sales Taxes and Charges", filters={"parent":sale.name}, fields=['*'])
		total_qty = 0
		total_rate = 0
		net_total = sale.net_total if sale.net_total else 0
		for item in items:
			total_qty += item.qty	
			total_rate += item.rate
		for tax in taxes:
			vat = tax.rate if tax.rate == 13 else ''
			tds = tax.rate if (tax.rate == 1.5 or tax.rate == 15) else ''
			data.append([sale.posting_date, '', sale.name, sale.customer, sale.customer_group, sale.customer_address, sale.project, sale.cost_center, '', sale.owner, total_qty, total_rate, '',sale.discount_amount, net_total, tax.charge_type, tax.account_head, vat, tds, sale.total_taxes_and_charges, sale.grand_total, sale.rounded_total, sale.total_advance, sale.outstanding_amount])
	return columns, data
    