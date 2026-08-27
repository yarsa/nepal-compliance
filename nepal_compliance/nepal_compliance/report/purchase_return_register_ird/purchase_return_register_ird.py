# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _
from nepal_compliance.utils import get_vat_breakup

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Data", "width": 200},
        {"label": _("प्रज्ञापनपत्र नं."), "fieldname": "customs_declaration_number", "fieldtype": "Data", "width": 130},
        {"label": _("आपूर्तिकर्ताको नाम"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 160},
        {"label": _("आपूर्तिकर्ताको स्थायी लेखा नम्बर"), "fieldname": "pan", "fieldtype": "Data", "width": 120},
        {"label": _("खरिद/पैठारी फिर्ता गरिएका वस्तु वा सेवाको विवरण"), "fieldname": "reason", "fieldtype": "Data", "width": 200},
        {"label": _("खरिद/पैठारी फिर्ता गरिएका वस्तु वा सेवाको परिमाण"), "fieldname": "qty", "fieldtype": "Float", "width": 120},
        {"label": _("वस्तु वा सेवाको एकाइ"), "fieldname": "uom", "fieldtype": "Data", "width": 100},
        {"label": _("जम्मा फिर्ता मूल्य (रु)"), "fieldname": "total", "fieldtype": "Float", "width": 120},
        {"label": _("कर छुट हुने वस्तु वा सेवाको फिर्ता मूल्य (रु)"), "fieldname": "tax_exempt", "fieldtype": "Float", "width": 100},
        {"label": _("करयोग्य फिर्ता (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य फिर्ता (पूंजीगत बाहेक) कर (रु)"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य पैठारी फिर्ता (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_import_non_capital_amount", "fieldtype": "Float", "width": 140},
        {"label": _("करयोग्य पैठारी फिर्ता (पूंजीगत बाहेक) कर (रु)"), "fieldname": "taxable_import_non_capital_tax", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य फिर्ता मूल्य (रु)"), "fieldname": "capital_taxable_amount", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य फिर्ता कर (रु)"), "fieldname": "capital_taxable_tax", "fieldtype": "Float", "width": 140},
    ]

def get_data(filters):
    conditions = ["pi.docstatus = 1 and pi.is_return = 1"]
    values = {}

    if filters.get("company"):
        conditions.append("pi.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    if filters.get("return_invoice"):
        conditions.append("pi.name = %(return_invoice)s")
        values["return_invoice"] = filters.get("return_invoice")


    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        conditions.append("pi.posting_date BETWEEN %(from)s AND %(to)s")
        values["from"] = filters.get("from_nepali_date")
        values["to"] = filters.get("to_nepali_date")
    elif filters.get("from_nepali_date"):
        conditions.append("pi.posting_date >= %(from)s")
        values["from"] = filters.get("from_nepali_date")
    elif filters.get("to_nepali_date"):
        conditions.append("pi.posting_date <= %(to)s")
        values["to"] = filters.get("to_nepali_date")

    conditions_sql = " AND ".join(conditions)
    query = """
        SELECT
            pi.name as invoice, pi.bill_no, pi.customs_declaration_number, pi.reason, pi.rounded_total, pi.grand_total, pi.posting_date, pi.supplier_name, pi.supplier, pi.tax_id as invoice_pan,
            pi.total, pi.company
        FROM `tabPurchase Invoice` pi
        WHERE {conditions}
        ORDER BY pi.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = get_vat_breakup("Purchase Invoice", {inv.invoice: inv.company for inv in invoices})

    for inv in invoices:
        supplier_country = frappe.db.get_value("Supplier", inv.supplier_name, "country") or ""
        is_import = supplier_country.strip().lower() != "nepal"

        pan = inv.invoice_pan or frappe.db.get_value("Supplier", inv.supplier, "tax_id")

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = tax_import_nc = tax_capital = 0.0

        item_filters = {"parent": inv.invoice}

        items = frappe.get_all("Purchase Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "asset_category", "qty", "uom", "item_code", "item_name"])

        item_vat_map = vat_breakup.get(inv.invoice, {}).get("item_vat", {})

        for item in items:
            amt = flt(item.get("net_amount"))
            item_vat = flt(item_vat_map.get(item.get("item_code") or item.get("item_name")))

            if item.get("is_nontaxable_item") or not item_vat:
                tax_exempt += amt
                continue

            if item.get("asset_category"):
                capital_taxable_amount += amt
                tax_capital += item_vat
            else:
                if is_import:
                    taxable_import_nc += amt
                    tax_import_nc += item_vat
                else:
                    taxable_domestic_nc += amt
                    tax_domestic_nc += item_vat

        data.append({
            "posting_date": inv.posting_date,
            "invoice": inv.bill_no if inv.bill_no else inv.invoice,
            "customs_declaration_number": inv.customs_declaration_number if is_import else "",
            "supplier_name": inv.supplier_name,
            "pan": pan,
            "reason": inv.reason or "",
			"qty": abs(sum(item.qty for item in items if item.qty)) if items else 0.0, 
            "uom": item.uom if items else "",
            "total": abs(inv.rounded_total or inv.grand_total),
            "tax_exempt": abs(tax_exempt),
            "taxable_amount": abs(taxable_domestic_nc),
            "tax_amount": abs(tax_domestic_nc),
            "taxable_import_non_capital_amount": abs(taxable_import_nc),
            "taxable_import_non_capital_tax": abs(tax_import_nc),
            "capital_taxable_amount": abs(capital_taxable_amount),
            "capital_taxable_tax": abs(tax_capital)
        })

    return data
