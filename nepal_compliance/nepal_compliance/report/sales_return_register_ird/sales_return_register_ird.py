# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _
from nepal_compliance.utils import distribute_item_vat, get_vat_breakup, is_exempt_report_item, item_taxable_amount, resolve_report_vat_source

def execute(filters=None):
    """Run the IRD Sales Return Register and return columns plus rows."""
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data

def get_columns():
    """Column definitions for the IRD Sales Return Register."""
    return [
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
        {"label": _("खरिदकर्ताको नाम"), "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": _("खरिदकर्ताको स्थायी लेखा नम्बर"), "fieldname": "pan", "fieldtype": "Data", "width": 120},
        {"label": _("वस्तु वा सेवाको नाम"), "fieldname": "name", "fieldtype": "Data", "width": 200},
        {"label": _("वस्तु वा सेवाको परिमाण"), "fieldname": "qty", "fieldtype": "Float", "width": 120},
        {"label": _("वस्तु वा सेवाको एकाइ"), "fieldname": "uom", "fieldtype": "Data", "width": 100},
        {"label": _("जम्मा फिर्ता मूल्य (रु)"), "fieldname": "total", "fieldtype": "Float", "width": 120},
        {"label": _("स्थानीय कर छुटको फिर्ता  मूल्य (रु)"), "fieldname": "tax_exempt", "fieldtype": "Float", "width": 100},
        {"label": _("करयोग्य फिर्ता मूल्य (रु)"), "fieldname": "taxable_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य फिर्ता कर (रु)"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 120}
    ]

def get_data(filters):
    """Build sales return register rows from submitted returns in the filter range."""
    conditions = ["si.docstatus = 1", "si.is_return = 1"]
    values = {}

    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("return_invoice"):
        conditions.append("si.name = %(return_invoice)s")
        values["return_invoice"] = filters.get("return_invoice")

    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        conditions.append("si.posting_date BETWEEN %(from)s AND %(to)s")
        values["from"] = filters.get("from_nepali_date")
        values["to"] = filters.get("to_nepali_date")
    elif filters.get("from_nepali_date"):
        conditions.append("si.posting_date >= %(from)s")
        values["from"] = filters.get("from_nepali_date")
    elif filters.get("to_nepali_date"):
        conditions.append("si.posting_date <= %(to)s")
        values["to"] = filters.get("to_nepali_date")

    conditions_sql = " AND ".join(conditions)

    query = """
        SELECT
            si.name as invoice,
            si.rounded_total,
            si.grand_total,
            si.posting_date,
            si.customer_name,
            si.tax_id as pan,
            si.customer,
            si.company,
            si.total,
            si.taxable_amount as stored_taxable_amount,
            si.vat_amount as stored_vat_amount,
            si.item_vat_detail as stored_item_vat_detail,
            si.posting_date
        FROM `tabSales Invoice` si
        WHERE {conditions}
        ORDER BY si.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = get_vat_breakup("Sales Invoice", {inv.invoice: inv.company for inv in invoices})

    grand_qty = grand_total = grand_tax_exempt = grand_taxable = grand_tax = 0.0

    for inv in invoices:
        item_filters = {"parent": inv.invoice}
        items = frappe.get_all("Sales Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "item_code", "qty", "uom", "item_name"])

        item_vat_map, stored, breakup = resolve_report_vat_source(inv, vat_breakup)
        total_vat = flt(inv.get("stored_vat_amount")) if stored else flt(breakup.get("total_vat"))

        tax_exempt_total = taxable_total = total_qty = 0.0

        row_vat = distribute_item_vat(items, item_vat_map)

        for item, item_vat in zip(items, row_vat, strict=True):
            net = flt(item.get("net_amount"))
            qty = flt(item.get("qty") or 0)
            is_nontaxable = is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup)

            total_qty += abs(qty)

            tax_exempt_item = taxable_amount_item = tax_amount_item = 0.0
            if is_nontaxable:
                tax_exempt_item = net
                tax_exempt_total += net
            else:
                taxable_amount_item = item_taxable_amount(item, item_vat, item_vat_map)
                tax_amount_item = item_vat
                taxable_total += taxable_amount_item

            data.append({
                "posting_date": inv.posting_date or "",
                "invoice": inv.invoice,
                "customer_name": inv.customer_name,
                "pan": inv.pan or frappe.db.get_value("Customer", inv.customer, "tax_id"),
                "name": item.get("item_name") or item.get("item_code"),
                "qty": abs(qty),
                "uom": item.get("uom") or "",
                "total": abs(flt(net)),
                "tax_exempt": abs(flt(tax_exempt_item)),
                "taxable_amount": abs(flt(taxable_amount_item)),
                "tax_amount": abs(flt(tax_amount_item)),
            })

        data.append({
            "posting_date": "",
            "invoice": "",
            "customer_name": "जम्मा",
            "pan": "",
            "name": "",
            "qty": abs(total_qty),
            "uom": "",
            "total": abs(flt(inv.rounded_total or inv.grand_total)),
            "tax_exempt": abs(flt(tax_exempt_total)),
            "taxable_amount": abs(flt(taxable_total)),
            "tax_amount": abs(total_vat)
        })

        grand_qty += abs(total_qty)
        grand_total += abs(flt(inv.rounded_total or inv.grand_total))
        grand_tax_exempt += abs(flt(tax_exempt_total))
        grand_taxable += abs(flt(taxable_total))
        grand_tax += abs(total_vat)

    data.append({
        "posting_date": "",
        "invoice": "",
        "customer_name": "कुल जम्मा",
        "pan": "",
        "name": "",
        "qty": grand_qty,
        "uom": "",
        "total": grand_total,
        "tax_exempt": grand_tax_exempt,
        "taxable_amount": grand_taxable,
        "tax_amount": grand_tax
    })

    return data
