# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    columns, data = [], []
    columns = [
        _("Date") + ":Date:150",
        _("Customer") + ":Link/Customer:150",
        _("VAT/PAN Number") + ":Data:120",
        _("Invoice Number") + ":Link/Sales Invoice:200",
        _("Item Code") + ":Link/Item:120",
        _("Item Name") + ":Data:150",
        _("Qty") + ":Float:60",
        _("Rate") + ":Currency:80",
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
    conditions = ["si.docstatus IN (1, 2)"]
    values = []
    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        conditions.append("si.posting_date >= %s AND si.posting_date <= %s")
        values.extend([filters["from_nepali_date"], filters["to_nepali_date"]])
    elif filters.get("from_nepali_date"):
        conditions.append("si.posting_date >= %s")
        values.append(filters["from_nepali_date"])
    elif filters.get("to_nepali_date"):
        conditions.append("si.posting_date <= %s")
        values.append(filters["to_nepali_date"])

    if filters.get("status"):
        conditions.append("si.status = %s")
        values.append(filters["status"])

    if filters.get("customer"):
        conditions.append("si.customer = %s")
        values.append(filters["customer"])

    if filters.get("invoice_number"):
        conditions.append("si.name = %s")
        values.append(filters["invoice_number"])

    query = f"""
        SELECT
            si.posting_date,
            si.customer,
            COALESCE(NULLIF(si.vat_number, ''), NULLIF(si.tax_id, '')) AS vat_pan_number,
            si.name AS invoice_number,
            item.item_code,
            item.item_name,
            item.qty,
            item.rate,
            (item.qty * item.rate) AS amount,
            si.total_taxes_and_charges,
            si.discount_amount,
            si.total,
            si.net_total,
            si.grand_total,
            si.total_advance,
            si.outstanding_amount,
            si.status
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` item ON item.parent = si.name
        WHERE { " AND ".join(conditions) }
        ORDER BY si.posting_date DESC
    """
    
    result = frappe.db.sql(query, values=values, as_dict=True)
    invoice_totals = {}
    current_invoice = None

    overall_totals = {
        "qty": 0,
        "rate": 0,  
        "amount": 0,
        "total_taxes_and_charges": 0,
        "discount_amount": 0,
        "total": 0,
        "net_total": 0,
        "grand_total": 0,
        "total_advance": 0,
        "outstanding": 0, 
    }

    for row in result:
        if current_invoice != row.invoice_number:
            if current_invoice:
                data.append([
                    "", "", "", "", "", "Total",
                    invoice_totals[current_invoice]["qty"],
                    invoice_totals[current_invoice]["rate"], 
                    invoice_totals[current_invoice]["amount"],
                    invoice_totals[current_invoice]["total_taxes_and_charges"],
                    invoice_totals[current_invoice] ["discount_amount"],
                    invoice_totals[current_invoice]["total"],
                    invoice_totals[current_invoice]["net_total"],
                    invoice_totals[current_invoice]["grand_total"],
                    invoice_totals[current_invoice]["total_advance"],
                    invoice_totals[current_invoice]["outstanding"],
                    ""
                ])
                overall_totals["qty"] += invoice_totals[current_invoice]["qty"]
                overall_totals["amount"] += invoice_totals[current_invoice]["amount"]
                overall_totals["rate"] += invoice_totals[current_invoice]["rate"] 
                overall_totals["total_taxes_and_charges"] += invoice_totals[current_invoice]["total_taxes_and_charges"]
                overall_totals["discount_amount"] += invoice_totals[current_invoice]["discount_amount"]
                overall_totals["total"] += invoice_totals[current_invoice]["total"]
                overall_totals["net_total"] += invoice_totals[current_invoice]["net_total"]
                overall_totals["grand_total"] += invoice_totals[current_invoice]["grand_total"]
                overall_totals["total_advance"] += invoice_totals[current_invoice]["total_advance"]
                overall_totals["outstanding"] += invoice_totals[current_invoice]["outstanding"]

            current_invoice = row.invoice_number
            invoice_totals[current_invoice] = {
                "qty": 0,
                "amount": 0,
                "rate": 0, 
                "total_taxes_and_charges": 0,
                "discount_amount": 0,
                "total": 0,
                "net_total": 0,
                "grand_total": 0,
                "total_advance": 0,
                "outstanding": 0
            }

        data.append([
            row.posting_date,
            row.customer,
            row.vat_pan_number,
            row.invoice_number,
            row.item_code,
            row.item_name,
            row.qty,
            row.rate,
            row.amount,
            "","","","","","","",
            row.status
        ])
        invoice_totals[current_invoice]["qty"] += flt(row.qty)
        invoice_totals[current_invoice]["amount"] += flt(row.amount)
        invoice_totals[current_invoice]["rate"] += flt(row.rate)  
        invoice_totals[current_invoice]["total_taxes_and_charges"] = flt(row.total_taxes_and_charges)
        invoice_totals[current_invoice]["discount_amount"] = flt(row.discount_amount)
        invoice_totals[current_invoice]["total"] = flt(row.total)
        invoice_totals[current_invoice]["net_total"] = flt(row.net_total)
        invoice_totals[current_invoice]["grand_total"] = flt(row.grand_total)
        invoice_totals[current_invoice]["total_advance"] = flt(row.total_advance)
        invoice_totals[current_invoice]["outstanding"] = flt(row.outstanding_amount)


    if current_invoice:
        data.append([
            "", "", "", "", "", "Total", 
            invoice_totals[current_invoice]["qty"],
            invoice_totals[current_invoice]["rate"], 
            invoice_totals[current_invoice]["amount"],
            invoice_totals[current_invoice]["total_taxes_and_charges"],
            invoice_totals[current_invoice]["discount_amount"],
            invoice_totals[current_invoice]["total"],
            invoice_totals[current_invoice]["net_total"],
            invoice_totals[current_invoice]["grand_total"],
            invoice_totals[current_invoice]["total_advance"],
            invoice_totals[current_invoice]["outstanding"],
            ""
        ])
    
        overall_totals["qty"] += invoice_totals[current_invoice]["qty"]
        overall_totals["amount"] += invoice_totals[current_invoice]["amount"]
        overall_totals["outstanding"] += invoice_totals[current_invoice]["outstanding"]
        overall_totals["rate"] += invoice_totals[current_invoice]["rate"]  
        overall_totals["total_taxes_and_charges"] += invoice_totals[current_invoice]["total_taxes_and_charges"]
        overall_totals["discount_amount"] += invoice_totals[current_invoice]["discount_amount"]
        overall_totals["total"] += invoice_totals[current_invoice]["total"]
        overall_totals["net_total"] += invoice_totals[current_invoice]["net_total"]
        overall_totals["grand_total"] += invoice_totals[current_invoice]["grand_total"]
        overall_totals["total_advance"] += invoice_totals[current_invoice]["total_advance"]

    data.append([
        "", "", "", "", "", "Overall Total", 
        overall_totals["qty"],
        overall_totals["rate"], 
        overall_totals["amount"],
        overall_totals["total_taxes_and_charges"],
        overall_totals["discount_amount"],
        overall_totals["total"],
        overall_totals["net_total"],
        overall_totals["grand_total"],
        overall_totals["total_advance"],
        overall_totals["outstanding"],
        ""
    ])

    return columns, data