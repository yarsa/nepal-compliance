# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _
from nepal_compliance.ird_filters import apply_ird_posting_date_filters, invoice_link_fields
from nepal_compliance.utils import distribute_item_vat, get_vat_breakup, is_exempt_report_item, item_taxable_amount, resolve_report_vat_source

def execute(filters=None):
    """Run the IRD Purchase Return Register and return columns plus rows."""
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    """Column definitions for the IRD Purchase Return Register."""
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
    """Build purchase return register rows from submitted returns in the filter range."""
    filters = filters or {}
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

    apply_ird_posting_date_filters(filters, conditions, values, "pi.posting_date")

    conditions_sql = " AND ".join(conditions)
    query = """
        SELECT
            pi.name as invoice, pi.bill_no, pi.customs_declaration_number, pi.reason, pi.rounded_total, pi.grand_total, pi.posting_date, pi.supplier_name, pi.supplier, pi.tax_id as invoice_pan,
            pi.total, pi.company, pi.taxable_amount as stored_taxable_amount, pi.item_vat_detail as stored_item_vat_detail,
            s.country as supplier_country, s.tax_id as supplier_tax_id
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
        WHERE {conditions}
        ORDER BY pi.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = get_vat_breakup("Purchase Invoice", {inv.invoice: inv.company for inv in invoices})

    for inv in invoices:
        supplier_country = (inv.supplier_country or "").strip()
        is_import = supplier_country.lower() != "nepal"

        pan = inv.invoice_pan or inv.supplier_tax_id

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = tax_import_nc = tax_capital = 0.0

        item_filters = {"parent": inv.invoice}

        items = frappe.get_all("Purchase Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "asset_category", "qty", "uom", "item_code", "item_name"])

        item_vat_map, stored, breakup = resolve_report_vat_source(inv, vat_breakup)
        row_vat = distribute_item_vat(items, item_vat_map)

        for item, item_vat in zip(items, row_vat, strict=True):
            net = flt(item.get("net_amount"))

            if is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup):
                tax_exempt += net
                continue

            amt = item_taxable_amount(item, item_vat, item_vat_map)
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
            **invoice_link_fields("Purchase Invoice", inv.invoice),
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
