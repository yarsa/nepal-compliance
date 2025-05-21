# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from datetime import datetime
import calendar
from frappe import _

def execute(filters=None):
    columns, data = [], []
    nepali_month = filters.get("nepali_month")
    nepali_year = filters.get("nepali_year")

    if not nepali_month:
        month_pattern = "%"

    else:
	    nepali_month_map = {
		    "Baishakh": "01", "Jestha": "02", "Ashadh": "03", "Shrawan": "04",
		    "Bhadra": "05", "Ashwin": "06", "Kartik": "07", "Mangsir": "08",
		    "Poush": "09", "Magh": "10", "Falgun": "11", "Chaitra": "12"
	    }

	    month_number = nepali_month_map.get(nepali_month)
	    if not month_number:
		    frappe.throw(_("Invalid Nepali Month selected."))

	    month_pattern = f"%-{month_number}-%"
    
    columns = [
        _("Invoice Date") + ":Date:150",
        _("Customer") + ":Link/Customer:150",
        _("VAT/PAN Number") + ":Data:120",
        _("Invoice Number") + ":Link/Sales Invoice:200",
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
    conditions = ""
    from_nepali_date, to_nepali_date = None, None

    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        from_nepali_date = filters["from_nepali_date"]
        to_nepali_date = filters["to_nepali_date"]
        conditions += " AND si.nepali_date BETWEEN %(from_nepali_date)s AND %(to_nepali_date)s"

    if filters.get("customer"):
        conditions += " AND si.customer = %(customer)s"

    query = """
        SELECT
            si.nepali_date,
            si.customer,
            si.vat_number,
            si.name AS invoice_number,
            SUM(item.qty) AS total_qty,
            SUM(item.qty * item.rate) AS total_amount,
            si.total_taxes_and_charges AS total_taxes_and_charges,
            si.discount_amount AS discount_amount,
            si.total AS total,
            si.net_total AS net_total,
            si.grand_total AS grand_total,
            si.total_advance AS total_advance,
            si.outstanding_amount AS outstanding_amount,
            si.status
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` item ON item.parent = si.name
        WHERE
			si.docstatus = 1
            AND si.nepali_date LIKE %(month_pattern)s
            {conditions}
        GROUP BY
            si.name
        ORDER BY
            si.posting_date DESC
    """.format(conditions=conditions)

    values = {
	    "month_pattern": month_pattern,
	    "from_nepali_date": filters.get("from_nepali_date"),
	    "to_nepali_date": filters.get("to_nepali_date"),
	    "customer": filters.get("customer")
	}
    result = frappe.db.sql(query, values=values, as_dict=True)


    for row in result:
        data.append([     
            row.nepali_date,                          
            row.customer,
            row.vat_number,                 
            row.invoice_number,
            row.total_qty,                           
            row.total_amount,                         
            row.total_taxes_and_charges,              
            row.discount_amount,                      
            row.total,                                
            row.net_total,                            
            row.grand_total,                          
            row.total_advance,                        
            row.outstanding_amount,                   
            row.status                               
        ])
    return columns, data