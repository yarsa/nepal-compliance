# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters or {})
    return columns, data

def get_columns():
    return [
        {"label": _("मिति"), "fieldname": "nepali_date", "fieldtype": "Data", "width": 150},
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
        conditions.append("si.nepali_date BETWEEN %(from)s AND %(to)s")
        values["from"] = filters.get("from_nepali_date")
        values["to"] = filters.get("to_nepali_date")
    elif filters.get("from_nepali_date"):
        conditions.append("si.nepali_date >= %(from)s")
        values["from"] = filters.get("from_nepali_date")
    elif filters.get("to_nepali_date"):
        conditions.append("si.nepali_date <= %(to)s")
        values["to"] = filters.get("to_nepali_date")

    query = f"""
        SELECT
            si.name as invoice,
            si.rounded_total,
            si.nepali_date,
            si.customer_name,
            si.tax_id as pan,
            si.total,
            si.total_taxes_and_charges as total_tax,
            si.posting_date
        FROM `tabSales Invoice` si
        WHERE {' AND '.join(conditions)}
        ORDER BY si.posting_date
    """

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    for inv in invoices:
        customer_country = frappe.db.get_value("Customer", inv.customer_name, "territory") or ""
        is_export = customer_country.strip().lower() not in ("", "nepal")

        # Fetch all items for this invoice with necessary fields
        item_filters = {"parent": inv.invoice}
        items = frappe.get_all("Sales Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "item_code", "qty", "uom", "item_name"])

        item_codes = [item["item_code"] for item in items]
        asset_items = frappe.get_all("Item", filters={"item_code": ["in", item_codes], "is_fixed_asset": 1}, pluck="item_code")

        # Calculate and append data per item
        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))

            if item.get("is_nontaxable_item"):
                tax_exempt_item = amt
                taxable_amount_item = 0.0
                tax_amount_item = 0.0
            else:
                tax_exempt_item = 0.0
                if item["item_code"] in asset_items:
                    # Capital asset: taxable amount and tax assumed zero here as per your business logic
                    taxable_amount_item = 0.0
                    tax_amount_item = 0.0
                else:
                    taxable_amount_item = amt
                    tax_amount_item = taxable_amount_item * 0.13  # 13% tax rate

            data.append({
                "nepali_date": inv.nepali_date or inv.posting_date,
                "invoice": inv.invoice,
                "customer_name": inv.customer_name,
                "pan": inv.pan,
                "name": item.get("item_name") or item.get("item_code"),
                "qty": flt(item.get("qty")),
                "uom": item.get("uom") or "",
                "total": flt(inv.rounded_total),
                "tax_exempt": flt(tax_exempt_item),
                "taxable_amount": flt(taxable_amount_item),
                "tax_amount": flt(tax_amount_item)
            })

    return data
