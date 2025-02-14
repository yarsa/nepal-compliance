# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _

def execute(filters=None):
    columns = [
        _("Invoice No") + ":Text:200",
        _("Date") + ":Date:150",
        _("Nepali_Date") + ":Data:150",
        _("Customer/Supplier") + ":Data:200",
        _("Sales Amount") + ":Currency:150",
        _("VAT Collected (Sales)") + ":Currency:150",
        _("Purchase Amount") + ":Currency:150",
        _("VAT Paid (Purchase)") + ":Currency:150",
        _("Net VAT Payable/Receivable") + ":Currency:250"
    ]
    data = []
    
    total_sales_vat = 0
    total_purchase_vat = 0
    total_net_vat = 0

    conditions = "si.docstatus = 1"
    purchase_conditions = "pi.docstatus = 1"
    from_date, to_date, from_nepali_date, to_nepali_date = None, None, None, None

    if filters.get("from_date") and filters.get("to_date"):
        from_date = filters["from_date"]
        to_date = filters["to_date"]
        conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
        purchase_conditions += " AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"

    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        from_nepali_date = filters["from_nepali_date"]
        to_nepali_date = filters["to_nepali_date"]
        conditions += " AND si.nepali_date BETWEEN %(from_nepali_date)s AND %(to_nepali_date)s"
        purchase_conditions += " AND pi.nepali_date BETWEEN %(from_nepali_date)s AND %(to_nepali_date)s"

    sales_invoices_query = """
        SELECT si.name AS invoice_no, si.posting_date, si.nepali_date, si.customer AS customer, si.rounded_total AS sales_amount, 
               SUM(stc.tax_amount) AS sales_vat
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Taxes and Charges` stc ON stc.parent = si.name
        WHERE {conditions}
        GROUP BY si.name
        ORDER BY si.posting_date, si.nepali_date ASC
    """.format(conditions=conditions)

    purchase_invoices_query = """
        SELECT pi.name AS invoice_no, pi.posting_date, pi.nepali_date, pi.supplier AS supplier, pi.grand_total AS purchase_amount, 
               SUM(ptc.tax_amount) AS purchase_vat
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabPurchase Taxes and Charges` ptc ON ptc.parent = pi.name
        WHERE {purchase_conditions}
        GROUP BY pi.name
        ORDER BY pi.posting_date, pi.nepali_date ASC
    """.format(purchase_conditions=purchase_conditions)

    try:
        sales_invoices = frappe.db.sql(sales_invoices_query, values={
            'from_date': from_date, 
            'to_date': to_date, 
            'from_nepali_date': from_nepali_date, 
            'to_nepali_date': to_nepali_date
        }, as_dict=True)

        purchase_invoices = frappe.db.sql(purchase_invoices_query, values={
            'from_date': from_date, 
            'to_date': to_date, 
            'from_nepali_date': from_nepali_date, 
            'to_nepali_date': to_nepali_date
        }, as_dict=True)
    except Exception as e:
        print(f"Error in SQL execution: {str(e)}")
        raise

    for sale in sales_invoices:
        purchase = next((p for p in purchase_invoices if p['invoice_no'] == sale['invoice_no']), None)

        if purchase:
            purchase_vat = purchase['purchase_vat'] if purchase['purchase_vat'] is not None else 0
            net_vat = sale['sales_vat'] - purchase_vat
            invoice_link = f'<a href="/app/sales-invoice/{sale["invoice_no"]}" target="_blank">{sale["invoice_no"]}</a>'
            data.append([
                invoice_link, 
                sale['posting_date'],
                sale['nepali_date'],
                sale['customer'],
                sale['sales_amount'],
                sale['sales_vat'],
                purchase['purchase_amount'],
                purchase_vat,
                net_vat
            ])
            total_sales_vat += sale['sales_vat'] or 0
            total_purchase_vat += purchase_vat 
            total_net_vat += net_vat or 0
        else:
            net_vat = sale['sales_vat']
            invoice_link = f'<a href="/app/sales-invoice/{sale["invoice_no"]}" target="_blank">{sale["invoice_no"]}</a>'
            data.append([
                invoice_link,
                sale['posting_date'],
                sale['nepali_date'],
                sale['customer'],
                sale['sales_amount'],
                sale['sales_vat'],
                0,
                0,
                net_vat
            ])
            total_sales_vat += sale['sales_vat'] or 0
            total_net_vat += net_vat or 0
        
    for purchase in purchase_invoices:
        if not any(sale['invoice_no'] == purchase['invoice_no'] for sale in sales_invoices):
            purchase_vat = purchase['purchase_vat'] if purchase['purchase_vat'] is not None else 0
            invoice_link = f'<a href="/app/purchase-invoice/{purchase["invoice_no"]}" target="_blank">{purchase["invoice_no"]}</a>'
            data.append([
                invoice_link,
                purchase['posting_date'],
                purchase['nepali_date'],
                purchase['supplier'],
                0,
                0,
                purchase['purchase_amount'],
                purchase_vat,
                purchase_vat
            ])
            total_purchase_vat += purchase_vat
            total_net_vat -= purchase_vat
    data.append([
        _("Total"),
        "", "", "", "",
        total_sales_vat,
        "",
        total_purchase_vat,
        total_net_vat
    ])
    return columns, data