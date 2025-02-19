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
            'fieldname': 'bill_date',
            'label': _('Supplier Invoice Date'),
            'fieldtype': 'Date'
        },
        {
            'fieldname': 'vat_no',
            'label': _('Vat/Pan No'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'total',
            'label': _(''),
            'fieldtype': 'Data',
            'width': 150
        },
        {
            'fieldname': 'qty',
            'label': _('Quantity'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'amount',
            'label': _('Amount'),
            'fieltype': 'Currency'
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
            'fieldname': 'warehouse',
            'label': _('Warehouse'),
            'fieldtype': 'Data'
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
            'fieldname': 'tax_and_charges_added',
            'label': _('Tax and Charges Added'),
            'fieldtype': 'Currency'
        },
        {
          'fieldname': 'return_against',
          'label': _('Return Against'),
          'fieldtype': 'Link',
          'options': 'Purchase Invoice'
        }

    ]
    data = []
    conditions = {"docstatus": 1, "is_return": 1}
    if filters.get("company"):
        conditions["company"] = filters["company"]
    if filters.get("supplier"):
        conditions["supplier"] = filters["supplier"]
    if filters.get("bill"):
        bill_no_filter = f"%{filters['bill']}%"
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
    if filters.get("return_invoice"):
        conditions["name"] = filters["return_invoice"]
         
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
            vat = gross_amount * 13/100
            sum_vat += vat
            total_rate += item.rate
            total_qty += item.qty
        for t in tax:
            if t.rate == 13:
                vat = t.tax_amount 
            elif t.rate in [1.5, 15]:
                tds += t.tax_amount
        for item in items:
            data.append([purchase.posting_date, purchase.nepali_date, purchase.name, purchase.supplier, purchase.bill_no,purchase.bill_date, purchase.vat_number, '', item.qty, item.amount, item.discount_amount if item.discount_amount !=0 else '', item.amount, item.net_amount, item.warehouse, '', '', '', '','', purchase.return_against])
        data.append(['', '', '', '', '', '', '', 'Total', total_qty, total, purchase.discount_amount, total, net_total, '', vat, tds, purchase.grand_total,purchase.outstanding_amount, purchase.total_taxes_and_charges, ''])
    return columns, data

