# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 200},
        {"label": _("खरिदकर्ताको नाम"), "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
        {"label": _("खरिदकर्ताको स्थायी लेखा नम्बर"), "fieldname": "pan", "fieldtype": "Data", "width": 120},
        {"label": _("जम्मा बिक्री / निकासी (रु)"), "fieldname": "total", "fieldtype": "Float", "width": 120},
        {"label": _("स्थानीय कर छुटको बिक्री  मूल्य (रु)"), "fieldname": "tax_exempt", "fieldtype": "Float", "width": 100},
        {"label": _("करयोग्य बिक्री मूल्य (रु)"), "fieldname": "taxable_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य बिक्री कर (रु)"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 120},
        {"label": _("निकासी गरेको वस्तु वा सेवाको मूल्य (रु)"), "fieldname": "Value of Exported Goods or Services", "fieldtype": "Float", "width": 140},
        {"label": _("निकासी गरेको देश"), "fieldname": "export_country", "fieldtype": "Data", "width": 140},
        {"label": _("निकासी प्रज्ञापनपत्र नम्बर"), "fieldname": "Export Declaration Number", "fieldtype": "Data", "width": 140},
        {"label": _("निकासी प्रज्ञापनपत्र मिति"), "fieldname": "Export Declaration Date", "fieldtype": "Data", "width": 140},
    ]

def get_data(filters):
    conditions = ["si.docstatus = 1 and si.is_return = 0"]
    values = {}

    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values["customer"] = filters.get("customer")

    if filters.get("document_number"):
        conditions.append("si.name = %(document_number)s")
        values["document_number"] = filters.get("document_number")

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
            si.name as invoice, si.rounded_total, si.posting_date, si.customer_name, si.tax_id as invoice_pan, si.customer,
            si.total, si.net_total, si.grand_total, si.total_taxes_and_charges as total_tax, si.customs_declaration_number, si.customs_declaration_date_bs
        FROM `tabSales Invoice` si
        WHERE {' AND '.join(conditions)}
        ORDER BY si.posting_date
    """

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    for inv in invoices:
        customer_country = frappe.db.get_value("Customer", inv.customer_name, "territory") or ""
        is_export = customer_country.strip().lower() not in ("", "nepal")

        pan = inv.invoice_pan or frappe.db.get_value("Customer", inv.customer, "tax_id")
        
        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0

        item_filters = {"parent": inv.invoice}
        
        items = frappe.get_all("Sales Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "item_code", "item_tax_template"])
        
        item_codes = [item["item_code"] for item in items]
        asset_items = frappe.get_all("Item", filters={"item_code": ["in", item_codes], "is_fixed_asset": 1}, pluck="item_code")
        
        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))

            item_tax_template = item.get("item_tax_template")

            is_nontaxable = (
                item.get("is_nontaxable_item") or (flt(inv.total_tax) == 0 and not item_tax_template))

            if is_nontaxable:
                tax_exempt += amt
                continue

            if item["item_code"] in asset_items:
                capital_taxable_amount += amt
            else:
                if is_export:
                    taxable_import_nc += amt
                else:
                    taxable_domestic_nc += amt

        total_taxable = taxable_domestic_nc + taxable_import_nc + capital_taxable_amount
        total_tax = flt(inv.total_tax)

        if total_tax == 0 or total_taxable == 0:
            tax_domestic_nc = tax_import_nc = tax_capital = 0
        else:
            tax_domestic_nc = (taxable_domestic_nc / total_taxable) * total_tax

        data.append({
            "posting_date": inv.posting_date,
            "invoice": inv.invoice,
            "customer_name": inv.customer_name,
            "pan": pan,
            "total": inv.rounded_total or inv.grand_total,
            "tax_exempt": tax_exempt,
            "taxable_amount": taxable_domestic_nc,
            "tax_amount": tax_domestic_nc,
            "Value of Exported Goods or Services": inv.net_total if is_export and inv.net_total else inv.total if is_export else 0.0,
            "export_country": customer_country if is_export else "",
            "Export Declaration Number": inv.customs_declaration_number if is_export else "",
            "Export Declaration Date": inv.customs_declaration_date_bs if is_export else "",
        })

    return data
