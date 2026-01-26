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

    query = f"""
        SELECT
            si.name as invoice,
            si.rounded_total,
            si.grand_total,
            si.posting_date,
            si.customer_name,
            si.tax_id as pan,
            si.customer,
            si.total,
            si.total_taxes_and_charges as total_tax,
            si.posting_date
        FROM `tabSales Invoice` si
        WHERE {' AND '.join(conditions)}
        ORDER BY si.posting_date
    """

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    grand_qty = grand_total = grand_tax_exempt = grand_taxable = grand_tax = 0.0

    for inv in invoices:
        item_filters = {"parent": inv.invoice}
        items = frappe.get_all("Sales Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "item_code", "qty", "uom", "item_name", "item_tax_template"])

        item_codes = [item["item_code"] for item in items]
        asset_items = frappe.get_all("Item", filters={"item_code": ["in", item_codes], "is_fixed_asset": 1}, pluck="item_code")

        total_invoice = tax_exempt_total = taxable_total = total_qty = 0.0
        taxable_item_net_amounts = []

        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))
            item_tax_template = item.get("item_tax_template")
            is_nontaxable = item.get("is_nontaxable_item") or (flt(inv.total_tax) == 0 and not item_tax_template)
            qty = flt(item.get("qty") or 0)

            total_qty += abs(qty)

            if is_nontaxable or item["item_code"] in asset_items:
                tax_exempt_total += amt
            else:
                taxable_total += amt
                taxable_item_net_amounts.append((item, amt))

        total_tax = flt(inv.total_tax)
        for item, amt in taxable_item_net_amounts:
            share = (amt / taxable_total) if taxable_total else 0
            item["calculated_tax"] = share * total_tax

        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))
            qty = flt(item.get("qty") or 0)
            item_tax_template = item.get("item_tax_template")
            is_nontaxable = item.get("is_nontaxable_item") or (flt(inv.total_tax) == 0 and not item_tax_template)
            is_fixed_asset = item["item_code"] in asset_items

            tax_exempt_item = taxable_amount_item = tax_amount_item = 0.0
            if is_nontaxable or is_fixed_asset:
                tax_exempt_item = amt
            else:
                taxable_amount_item = amt
                tax_amount_item = next(
                    (i[0]["calculated_tax"] for i in taxable_item_net_amounts if i[0] == item), 0.0)

            data.append({
                "posting_date": inv.posting_date or "",
                "invoice": inv.invoice,
                "customer_name": inv.customer_name,
                "pan": inv.pan or frappe.db.get_value("Customer", inv.customer, "tax_id"),
                "name": item.get("item_name") or item.get("item_code"),
                "qty": abs(qty),
                "uom": item.get("uom") or "",
                "total": abs(flt(amt)),
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
            "tax_amount": abs(flt(total_tax))
        })

        grand_qty += abs(total_qty)
        grand_total += abs(flt(inv.rounded_total or inv.grand_total))
        grand_tax_exempt += abs(flt(tax_exempt_total))
        grand_taxable += abs(flt(taxable_total))
        grand_tax += abs(flt(total_tax))

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
