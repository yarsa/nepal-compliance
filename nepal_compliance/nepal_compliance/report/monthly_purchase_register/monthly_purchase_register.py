# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    
    columns = [
        _("Invoice Date") + ":Date:150",
        _("Nepali Date") + ":Data:150",
        _("Supplier") + ":Link/Supplier:150",
        _("Invoice Number") + ":Link/Purchase Invoice:120",
        _("Qty") + ":Float:60",
        _("Amount") + ":Currency:100",
        _("Tax and Charges Added") + ":Currency:120",
        _("Discount") + ":Currency:120",
        _("Total") + ":Currency:120",
        _("Net Total") + ":Currency:120",
        _("Grand Total") + ":Currency:120",
        _("Total Advance") + ":Currency:120",
        _("Outstanding Amount") + ":Currency:120",
        _("Status") + ":Data:80",
    ]
    conditions = "pi.docstatus = 1"
    from_date, to_date, from_nepali_date, to_nepali_date, nepali_date = None, None, None, None, None
    
    if filters.get("from_date") and filters.get("to_date"):
        from_date = filters["from_date"]
        to_date = filters["to_date"]
        conditions += " AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s" 
    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        from_nepali_date = filters["from_nepali_date"]
        to_nepali_date = filters["to_nepali_date"]
        conditions += " AND pi.nepali_date BETWEEN %(from_nepali_date)s AND %(to_nepali_date)s"
    
    query = """
        SELECT
            pi.posting_date,
            pi.nepali_date,
            pi.supplier,
            pi.name AS invoice_number,
            SUM(item.qty) AS total_qty,
            SUM(item.qty * item.rate) AS total_amount,
            pi.taxes_and_charges_added AS taxes_and_charges_added,
            pi.discount_amount AS discount_amount,
            pi.total AS total,
            pi.net_total AS net_total,
            pi.grand_total AS grand_total,
            pi.total_advance AS total_advance,
            pi.outstanding_amount AS outstanding_amount,
            pi.status
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` item ON item.parent = pi.name
        WHERE
			{0}
        GROUP BY
            pi.name
        ORDER BY
            pi.posting_date DESC
    """.format(conditions)

    result = frappe.db.sql(query, values={'from_date': from_date, 'to_date': to_date,'from_nepali_date': from_nepali_date, 'to_nepali_date': to_nepali_date}, as_dict=True)

    for row in result:
        data.append([
            row.posting_date,                         
            row.nepali_date,                          
            row.supplier,                             
            row.invoice_number,                      
            row.total_qty,                            
            row.total_amount,                         
            row.taxes_and_charges_added,              
            row.discount_amount,                      
            row.total,                                
            row.net_total,                            
            row.grand_total,                          
            row.total_advance,                        
            row.outstanding_amount,                   
            row.status                                
        ])

    return columns, data
