# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    
    columns = [
        {
            'fieldname': 'date',
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
            'options': 'Purchase Invoice'
        },
        {
            'fieldname': 'supplier',
            'label': _('Supplier Name'),
            'fieldtype': 'Link',
            'options': 'Supplier'
        },
        {
            'fieldname': 'bill_no',
            'label': _('Supplier Invoice No'),
            'fieldtype': 'Data'
        },
    	{
            'fieldtype': 'supplier_invoice_date',
		    'label': _('Supplier Invoice Date'),
		    'fieldtype': 'Date'
	    },
        {
            'fieldname': 'vat_no',
            'label': _('Vat No'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'qty',
            'label': _('Quantity'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'amount',
            'label': _('Amount'),
            'fieldtype': 'Currency'
        },
        {
			'fiedlname': 'discount',
			'label': _('Discount'),
			'fieldtype': 'Currency'
		},
        {
            'fieldname': 'gross_amount',
            'label': _('Gross Amount'),
            'fieldtype': 'Currency'
        },
        {
            'fieldname': 'net_amount',
            'label': _('Net Amount'),
            'fieldtype': 'Currency'
        },
        {
            'fiedlname': 'warehouse',
            'label': _('Warehouse'),
            'fiedltype': 'Link',
            'options': 'warehouse'
        },
        {
            'fieldname': 'vat',
            'label': _('13% VAT'),
            'fieldtype': 'Currency'
        },
		{
			'fieldname': 'tds',
			'label': _('TDS'),
			'fieldtype': 'Currency'
		},
        {
            'fieldname': 'invoice_total',
            'label': _('Invoice Total'),
            'fieldtype': 'Currency'
        },
        {
            'fieldname': 'outstanding_amount',
            'label': _('Outstanding Amount'),
            'fieldtype': 'Currency'
        },
        {
            'fieldname': 'total_tax_and_charges',
            'label': _('Total Tax and Charges'),
            'fieldtype': 'Currency'
        },

    ]
    data = []
    conditions = {"docstatus": 1, "is_return": 0}
    if filters.get("company"):
        conditions["company"] = filters["company"]
    if filters.get("supplier"):
        conditions["supplier"] = filters["supplier"]
    if filters.get("bill_no"):
        bill_no_filter = f"%{filters['bill_no']}%"
        conditions["bill_no"] = ["like", bill_no_filter]
    if filters.get("bill_date"):
        conditions["bill_date"] = filters["bill_date"]
    if filters.get("due_date"):
        conditions["due_date"] = filters["due_date"]
    if filters.get("from_date") and filters.get("to_date"):
	    conditions["posting_date"] = ["between", [filters["from_date"], filters["to_date"]]]
    elif filters.get("from_date"):
	    conditions["posting_date"] = [">=", filters["from_date"]]
    elif filters.get("to_date"):
	    conditions["posting_date"] = ["<=", filters["to_date"]]
    if filters.get("nepali_date"):
        nepali_date_filter = f"%{filters['nepali_date']}%"
        conditions["nepali_date"] = ["like", nepali_date_filter]
    if filters.get("warehouse"):
	    conditions["warehouse"] = filters["warehouse"]
    if filters.get("document_number"):
        conditions["name"] = filters["document_number"]   
         
    purchase_invoice = frappe.db.get_list("Purchase Invoice", filters = conditions, fields=['*'])
    for purchase in purchase_invoice:
        items = frappe.db.get_all("Purchase Invoice Item", filters={"parent":purchase.name}, fields=['*'])
        tax = frappe.db.get_all("Purchase Taxes and Charges", filters={"parent":purchase.name}, fields=['*'])
        total = 0
        total_qty = 0
        total_rate = 0
        gross_amount = 0
        sum_gross_amount = 0
        vat = 0
        tds = 0
        sum_vat = 0
        invoice_total = purchase.grand_total
        net_total = purchase.net_total if purchase.additional_discount_percentage else invoice_total
        for item in items:
            total += item.amount
            gross_amount += item.amount
            sum_gross_amount += gross_amount
            total_qty += item.qty
            total_rate += item.rate
        for t in tax:
            if t.rate == 13:
                vat = t.tax_amount 
            elif t.rate in [1.5, 15]:
                tds += t.tax_amount
        data.append([purchase.posting_date, purchase.nepali_date, purchase.name, purchase.supplier, purchase.bill_no, purchase.bill_date, '', total_qty, purchase.total, purchase.discount_amount, gross_amount, net_total, item.warehouse, vat, tds, invoice_total, purchase.outstanding_amount, purchase.total_taxes_and_charges])
        # data.append(['', '', '', '', '', '', '', '', '', '', '', 'Total', total_qty, total_rat, total, sum_gross_amount, purchase.grand_total, '', '', sum_vat, purchase.total, purchae.outstanding_amount, purchase.taxes_and_charges_added])  
    return columns, data 
