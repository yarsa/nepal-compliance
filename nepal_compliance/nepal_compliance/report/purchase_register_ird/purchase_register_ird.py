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
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Data", "width": 200},
        {"label": _("प्रज्ञापनपत्र नं."), "fieldname": "customs_declaration_number", "fieldtype": "Data", "width": 130},
        {"label": _("आपूर्तिकर्ताको नाम"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 160},
        {"label": _("आपूर्तिकर्ताको स्थायी लेखा नम्बर"), "fieldname": "pan", "fieldtype": "Data", "width": 120},
        {"label": _("जम्मा खरिद मूल्य (रु)"), "fieldname": "total", "fieldtype": "Float", "width": 120},
        {"label": _("कर छुट हुने वस्तु वा सेवाको खरिद / पैठारी मूल्य (रु)"), "fieldname": "tax_exempt", "fieldtype": "Float", "width": 100},
        {"label": _("करयोग्य खरिद (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य खरिद (पूंजीगत बाहेक) कर (रु)"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य पैठारी (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_import_non_capital_amount", "fieldtype": "Float", "width": 140},
        {"label": _("करयोग्य पैठारी (पूंजीगत बाहेक) कर (रु)"), "fieldname": "taxable_import_non_capital_tax", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य खरिद / पैठारी मूल्य (रु)"), "fieldname": "capital_taxable_amount", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य खरिद / पैठारी कर (रु)"), "fieldname": "capital_taxable_tax", "fieldtype": "Float", "width": 140},
    ]

def get_data(filters):
    conditions = ["pi.docstatus = 1 and pi.is_return = 0"]
    values = {}

    if filters.get("company"):
        conditions.append("pi.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    if filters.get("document_number"):
        conditions.append("pi.name = %(document_number)s")
        values["document_number"] = filters.get("document_number")

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
            pi.name as invoice, pi.bill_no, pi.customs_declaration_number, pi.rounded_total, pi.grand_total, pi.posting_date,
            pi.supplier_name, pi.tax_id as invoice_pan, pi.total, pi.total_taxes_and_charges as total_tax, pi.supplier,
            s.country as supplier_country, s.tax_id as supplier_tax_id
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
        WHERE {conditions}
        ORDER BY pi.posting_date
    """
    
    query = query.replace("{conditions}", conditions_sql)
    
    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    invoice_names = [inv.invoice for inv in invoices]
    if invoice_names:
        all_items = frappe.get_all(
            "Purchase Invoice Item",
            filters={"parent": ["in", invoice_names]},
            fields=["parent", "is_nontaxable_item", "net_amount", "amount", "asset_category", "item_tax_template"],
            limit_page_length=0
        )
        items_by_invoice = {}
        for item in all_items:
            items_by_invoice.setdefault(item.parent, []).append(item)
    else:
        items_by_invoice = {}

    for inv in invoices:
        supplier_country = (inv.supplier_country or "nepal").strip().lower()
        is_import = supplier_country != "nepal"

        pan = inv.invoice_pan or inv.supplier_tax_id

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0

        items = items_by_invoice.get(inv.invoice, [])

        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))

            item_tax_template = item.get("item_tax_template")

            is_nontaxable = (
                item.get("is_nontaxable_item") or 
                (flt(inv.total_tax) == 0 and not item_tax_template)
            )

            if is_nontaxable:
                tax_exempt += amt
                continue

            if item.get("asset_category"):
                capital_taxable_amount += amt
            else:
                if is_import:
                    taxable_import_nc += amt
                else:
                    taxable_domestic_nc += amt

        total_taxable = taxable_domestic_nc + taxable_import_nc + capital_taxable_amount
        total_tax = flt(inv.total_tax)

        if total_tax == 0 or total_taxable == 0:
            tax_domestic_nc = tax_import_nc = tax_capital = 0
        else:
            tax_domestic_nc = (taxable_domestic_nc / total_taxable) * total_tax
            tax_import_nc = (taxable_import_nc / total_taxable) * total_tax
            tax_capital = (capital_taxable_amount / total_taxable) * total_tax

        data.append({
            "posting_date": inv.posting_date,
            "invoice": inv.bill_no if inv.bill_no else inv.invoice,
            "customs_declaration_number": inv.customs_declaration_number if is_import else "",
            "supplier_name": inv.supplier_name,
            "pan": pan,
            "total": inv.rounded_total or inv.grand_total,
            "tax_exempt": tax_exempt,
            "taxable_amount": taxable_domestic_nc,
            "tax_amount": tax_domestic_nc,
            "taxable_import_non_capital_amount": taxable_import_nc,
            "taxable_import_non_capital_tax": tax_import_nc,
            "capital_taxable_amount": capital_taxable_amount,
            "capital_taxable_tax": tax_capital
        })

    return data
