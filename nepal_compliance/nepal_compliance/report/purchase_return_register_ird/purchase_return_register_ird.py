# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import flt

from nepal_compliance.ird_checks import check_columns, check_summary, decorate_rows
from nepal_compliance.ird_country import is_foreign_country, resolve_ird_country
from nepal_compliance.ird_filters import (
    apply_ird_posting_date_filters,
    invoice_link_fields,
)
from nepal_compliance.utils import (
    allocate_legacy_ird_tax,
    distribute_item_vat,
    get_vat_breakup,
    invoice_ird_total,
    is_exempt_report_item,
    item_taxable_amount,
    legacy_ird_item_is_exempt,
    resolve_report_vat_source,
    use_legacy_ird_report_calculation,
)

ITEM_QUERY_BATCH_SIZE = 500


def execute(filters=None):
    """Run the IRD Purchase Return Register and return columns plus rows."""
    columns = check_columns(get_columns())
    data = decorate_rows(get_data(filters), "Purchase Invoice", filters)
    return columns, data, None, None, [check_summary(data)]

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
    legacy = use_legacy_ird_report_calculation()
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
            pi.name as invoice, pi.bill_no, pi.customs_declaration_number, pi.reason, pi.rounded_total, pi.grand_total, pi.summary_grand_total, pi.posting_date, pi.supplier_name, pi.supplier, pi.tax_id as invoice_pan,
            pi.total, pi.total_taxes_and_charges as total_tax, pi.company,
            pi.taxable_amount as stored_taxable_amount, pi.item_vat_detail as stored_item_vat_detail,
            pi.is_pan_or_abbreviated_bill,
            pi.ird_party_country as stored_party_country,
            supplier_address.country as address_country,
            s.tax_id as supplier_tax_id
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
        LEFT JOIN `tabAddress` supplier_address ON supplier_address.name = pi.supplier_address
        WHERE {conditions}
        ORDER BY pi.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = (
        {}
        if legacy
        else get_vat_breakup("Purchase Invoice", {inv.invoice: inv.company for inv in invoices})
    )

    invoice_names = [inv.invoice for inv in invoices]
    items_by_invoice = {}
    for start in range(0, len(invoice_names), ITEM_QUERY_BATCH_SIZE):
        batch_names = invoice_names[start:start + ITEM_QUERY_BATCH_SIZE]
        batch_items = frappe.get_all(
            "Purchase Invoice Item",
            filters={"parent": ["in", batch_names]},
            fields=[
                "parent",
                "is_nontaxable_item",
                "net_amount",
                "amount",
                "asset_category",
                "qty",
                "uom",
                "item_code",
                "item_name",
                "item_tax_template",
            ],
            limit_page_length=0,
        )
        for item in batch_items:
            items_by_invoice.setdefault(item.parent, []).append(item)

    for inv in invoices:
        supplier_country = resolve_ird_country(inv.stored_party_country, inv.address_country)
        is_import = is_foreign_country(supplier_country)

        pan = inv.invoice_pan or inv.supplier_tax_id

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = tax_import_nc = tax_capital = 0.0

        items = items_by_invoice.get(inv.invoice, [])

        item_vat_map, stored, breakup = (
            ({}, False, {})
            if legacy
            else resolve_report_vat_source(inv, vat_breakup)
        )
        row_vat = [0.0] * len(items) if legacy else distribute_item_vat(items, item_vat_map)

        for item, item_vat in zip(items, row_vat, strict=True):
            net = flt(item.get("net_amount"))
            if inv.is_pan_or_abbreviated_bill:
                tax_exempt += net
                continue

            is_exempt = (
                legacy_ird_item_is_exempt(item, inv.total_tax)
                if legacy
                else is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup)
            )
            if is_exempt:
                tax_exempt += net
                continue

            amt = net if legacy else item_taxable_amount(item, item_vat, item_vat_map)
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

        if legacy:
            tax_domestic_nc, tax_import_nc, tax_capital = allocate_legacy_ird_tax(
                (taxable_domestic_nc, taxable_import_nc, capital_taxable_amount),
                inv.total_tax,
            )

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
            "total": abs(
                (flt(inv.rounded_total) or flt(inv.grand_total))
                if legacy
                else invoice_ird_total(inv)
            ),
            "tax_exempt": abs(tax_exempt),
            "taxable_amount": abs(taxable_domestic_nc),
            "tax_amount": abs(tax_domestic_nc),
            "taxable_import_non_capital_amount": abs(taxable_import_nc),
            "taxable_import_non_capital_tax": abs(tax_import_nc),
            "capital_taxable_amount": abs(capital_taxable_amount),
            "capital_taxable_tax": abs(tax_capital)
        })

    return data
