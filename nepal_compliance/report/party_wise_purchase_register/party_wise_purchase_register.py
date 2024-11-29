import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    columns, data = [], []
    columns = [
        _("Invoice Date") + ":Date:150",
        _("Nepali Date") + ":Data:150",
        _("Supplier") + ":Link/Supplier:150",
        _("Invoice Number") + ":Link/Purchase Invoice:120",
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

    query = """
        SELECT
            pi.posting_date,
            pi.nepali_date,
            pi.supplier,
            pi.name AS invoice_number,
            item.item_code,
            item.item_name,
            item.qty,
            item.rate,
            (item.qty * item.rate) AS amount,
            pi.taxes_and_charges_added,
            pi.discount_amount,
            pi.total,
            pi.net_total,
            pi.grand_total,
            pi.total_advance,
            pi.outstanding_amount,
            pi.status
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` item ON item.parent = pi.name
        {0}
        ORDER BY pi.posting_date DESC
    """.format(conditions)
    
    result = frappe.db.sql(query, as_dict=True)
    overall_totals = {
        "qty": 0,
        "rate": 0,  
        "amount": 0,
        "outstanding": 0,
        "taxes_and_charges_added": 0,
        "discount_amount": 0
    }

    invoice_totals = {}
    current_invoice = None

    overall_totals = {
        "qty": 0,
        "rate": 0,
        "amount": 0,
        "outstanding": 0,
    }
    for row in result:
        if current_invoice != row.invoice_number:
            if current_invoice:
                data.append([
                    "","", "", "", "", "Total", 
                    invoice_totals[current_invoice]["qty"],
                    invoice_totals[current_invoice]["rate"], 
                    invoice_totals[current_invoice]["amount"],
                    invoice_totals[current_invoice]["taxes_and_charges_added"],
                    invoice_totals[current_invoice] ["discount_amount"],
                    "", "", "", "",
                    invoice_totals[current_invoice]["outstanding"],
                    ""
                ])
                overall_totals["qty"] += invoice_totals[current_invoice]["qty"]
                overall_totals["amount"] += invoice_totals[current_invoice]["amount"]
                overall_totals["outstanding"] += invoice_totals[current_invoice]["outstanding"]
                overall_totals["rate"] += invoice_totals[current_invoice]["rate"] 
                overall_totals["taxes_and_charges_added"] += invoice_totals[current_invoice]["taxes_and_charges_added"]
                overall_totals["discount_amount"] += invoice_totals[current_invoice]["discount_amount"] 

            current_invoice = row.invoice_number
            invoice_totals[current_invoice] = {
                "qty": 0,
                "amount": 0,
                "outstanding": 0,
                "rate": 0, 
                "taxes_and_charges_added": 0,
                "discount_amount": 0
            }

        data.append([
            row.posting_date,
            row.nepali_date,
            row.supplier,
            row.invoice_number,
            row.item_code,
            row.item_name,
            row.qty,
            row.rate,
            row.amount,
            "",
            "",
            row.total,
            row.net_total,
            row.grand_total,
            row.total_advance,
            "",
            row.status
        ])
        invoice_totals[current_invoice]["qty"] += flt(row.qty)
        invoice_totals[current_invoice]["amount"] += flt(row.amount)
        invoice_totals[current_invoice]["outstanding"] = flt(row.outstanding_amount)
        invoice_totals[current_invoice]["rate"] += flt(row.rate)  
        invoice_totals[current_invoice]["taxes_and_charges_added"] = flt(row.taxes_and_charges_added)
        invoice_totals[current_invoice]["discount_amount"] = flt(row.discount_amount)

    if current_invoice:
        data.append([
            "", "", "", "", "", "Total", 
            invoice_totals[current_invoice]["qty"],
            invoice_totals[current_invoice]["rate"], 
            invoice_totals[current_invoice]["amount"],
            invoice_totals[current_invoice]["taxes_and_charges_added"],
            invoice_totals[current_invoice]["discount_amount"],
            "", "", "","",
            invoice_totals[current_invoice]["outstanding"],
            ""
        ])
    
        overall_totals["qty"] += invoice_totals[current_invoice]["qty"]
        overall_totals["amount"] += invoice_totals[current_invoice]["amount"]
        overall_totals["outstanding"] += invoice_totals[current_invoice]["outstanding"]
        overall_totals["rate"] += invoice_totals[current_invoice]["rate"]  
        overall_totals["taxes_and_charges_added"] += invoice_totals[current_invoice]["taxes_and_charges_added"]
        overall_totals["discount_amount"] += invoice_totals[current_invoice]["discount_amount"]

    data.append([
        "", "", "", "", "", "Overall Total", 
        overall_totals["qty"],
        overall_totals["rate"], 
        overall_totals["amount"],
        overall_totals["taxes_and_charges_added"],
        overall_totals["discount_amount"],
        "", "", "", "",
        overall_totals["outstanding"],
        ""
    ])

    return columns, data