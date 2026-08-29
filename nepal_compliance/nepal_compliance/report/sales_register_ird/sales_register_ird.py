# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _
from nepal_compliance.utils import distribute_item_vat, get_vat_breakup, is_exempt_report_item, item_taxable_amount, resolve_report_vat_source

def execute(filters=None):
    """Run the IRD Sales Register and return columns plus rows."""
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    """Column definitions for the IRD Sales Register."""
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
    """Build sales register rows from submitted invoices in the filter range."""
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

    conditions_sql = " AND ".join(conditions)

    query = """
        SELECT
            si.name as invoice, si.rounded_total, si.posting_date, si.customer_name, si.tax_id as invoice_pan, si.customer, si.company,
            si.total, si.net_total, si.grand_total, si.customs_declaration_number, si.customs_declaration_date_bs,
            si.taxable_amount as stored_taxable_amount, si.item_vat_detail as stored_item_vat_detail,
            c.territory as customer_country
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON si.customer = c.name
        WHERE {conditions}
        ORDER BY si.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = get_vat_breakup("Sales Invoice", {inv.invoice: inv.company for inv in invoices})

    for inv in invoices:
        customer_country = (inv.customer_country or "").strip()
        is_export = customer_country.lower() not in ("", "nepal")

        pan = inv.invoice_pan or frappe.db.get_value("Customer", inv.customer, "tax_id")
        
        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = 0.0

        item_filters = {"parent": inv.invoice}

        items = frappe.get_all("Sales Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "item_code", "item_name"])

        item_codes = [item["item_code"] for item in items]
        asset_items = frappe.get_all("Item", filters={"item_code": ["in", item_codes], "is_fixed_asset": 1}, pluck="item_code")

        item_vat_map, stored, breakup = resolve_report_vat_source(inv, vat_breakup)
        row_vat = distribute_item_vat(items, item_vat_map)

        for item, item_vat in zip(items, row_vat, strict=True):
            net = flt(item.get("net_amount"))

            is_exempt = is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup)
            if is_exempt and (item.get("is_nontaxable_item") or not is_export):
                tax_exempt += net
                continue

            amt = item_taxable_amount(item, item_vat, item_vat_map)
            if item["item_code"] in asset_items:
                capital_taxable_amount += amt
            else:
                if is_export:
                    taxable_import_nc += amt
                else:
                    taxable_domestic_nc += amt
                    tax_domestic_nc += item_vat

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
