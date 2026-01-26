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
            'fieldname': 'vat_no',
            'label': _('Vat/Pan No'),
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
			'fieldname': 'discount',
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
            'fieldlname': 'warehouse',
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
    query = """
    SELECT DISTINCT pi.*
    FROM `tabPurchase Invoice` pi
    LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
    WHERE pi.docstatus = 1 AND pi.is_return = 0
    """
    conditions = []
    values = []

    if filters.get("company"):
        conditions.append("pi.company = %s")
        values.append(filters["company"])

    if filters.get("supplier"):
        conditions.append("pi.supplier = %s")
        values.append(filters["supplier"])

    if filters.get("bill_no"):
        conditions.append("pi.bill_no LIKE %s")
        values.append(f"%{filters['bill_no']}%")

    if filters.get("bill_date"):
        conditions.append("pi.bill_date = %s")
        values.append(filters["bill_date"])

    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        conditions.append("pi.posting_date >= %s AND posting_date <= %s")
        values.extend([filters["from_nepali_date"], filters["to_nepali_date"]])
    elif filters.get("from_nepali_date"):
        conditions.append("pi.posting_date >= %s")
        values.append(filters["from_nepali_date"])
    elif filters.get("to_nepali_date"):
        conditions.append("pi.posting_date <= %s")
        values.append(filters["to_nepali_date"])

    if filters.get("warehouse"):
        conditions.append("pii.warehouse = %s")
        values.append(filters["warehouse"])

    if filters.get("document_number"):
        conditions.append("pi.name = %s")
        values.append(filters["document_number"]) 

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY modified DESC"

    purchase_invoice = frappe.db.sql(query, values, as_dict=True)
    for purchase in purchase_invoice:
        items = frappe.get_all("Purchase Invoice Item", filters={"parent":purchase.name}, fields=['*'])
        tax = frappe.get_all("Purchase Taxes and Charges", filters={"parent":purchase.name}, fields=['*'])
        total = 0
        total_qty = 0
        total_rate = 0
        gross_amount = 0
        sum_gross_amount = 0
        vat = 0
        tds = 0
        sum_vat = 0
        invoice_total = purchase.grand_total
        net_total = purchase.net_total if purchase.additional_discount_percentage or purchase.discount_amount else invoice_total
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
        data.append([purchase.posting_date, purchase.name, purchase.supplier, purchase.bill_no, purchase.vat_number, total_qty, purchase.total, purchase.discount_amount, gross_amount, net_total, item.warehouse, vat, tds, invoice_total, purchase.outstanding_amount, purchase.total_taxes_and_charges])
        # data.append(['', '', '', '', '', '', '', '', '', '', '', 'Total', total_qty, total_rat, total, sum_gross_amount, purchase.grand_total, '', '', sum_vat, purchase.total, purchase.outstanding_amount, purchase.taxes_and_charges_added])  
    return columns, data 
