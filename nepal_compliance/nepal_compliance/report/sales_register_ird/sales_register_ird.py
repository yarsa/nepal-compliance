# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import flt

from nepal_compliance.ird_checks import (
    check_columns,
    check_summary,
    decorate_rows,
    filter_summary_rows,
    report_permission_condition,
)
from nepal_compliance.ird_country import is_foreign_country, resolve_ird_country
from nepal_compliance.ird_sequence import append_sequence_gaps
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


def get_sales_register_summary(rows):
    """Build colored summary cards for the Sales Register."""
    rows = [row for row in (rows or []) if not row.get("is_compliance_issue")]
    total = len(rows)
    tax_exempt = sum(1 for r in rows if flt(r.get("tax_exempt")) > 0)
    taxable = sum(1 for r in rows if flt(r.get("taxable_amount")) > 0)
    zero_value = sum(
        1
        for r in rows
        if r.get("invoice_name") and flt(r.get("total")) == 0
    )
    export = sum(
        1 for r in rows if flt(r.get("Value of Exported Goods or Services")) > 0
    )

    return [
        {
            "value": total,
            "label": _("Total Sales"),
            "datatype": "Int",
            "indicator": "Blue",
            "ird_view": "all",
        },
        {
            "value": tax_exempt,
            "label": _("कर छुटको बिक्री"),
            "datatype": "Int",
            "indicator": "Grey",
            "ird_view": "tax_exempt",
        },
        {
            "value": taxable,
            "label": _("करयोग्य बिक्री"),
            "datatype": "Int",
            "indicator": "Blue",
            "ird_view": "taxable",
        },
        {
            "value": export,
            "label": _("निकासी"),
            "datatype": "Int",
            "indicator": "Orange",
            "ird_view": "export",
        },
        {
            "value": zero_value,
            "label": _("Zero Value Sales"),
            "datatype": "Int",
            "indicator": "Grey",
            "ird_view": "zero_value",
        },
    ]


def execute(filters=None):
    """Run the IRD Sales Register and return columns, rows, and summary."""
    columns = check_columns(get_columns())
    data = decorate_rows(get_data(filters), "Sales Invoice", filters)
    data = append_sequence_gaps(data, filters, is_return=False)
    summary = get_sales_register_summary(data)
    summary.append(check_summary(data))
    return columns, filter_summary_rows(data, filters), None, None, summary


def get_columns():
    """Column definitions for the IRD Sales Register."""
    return [
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 150},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Data", "width": 200},
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
    filters = filters or {}
    legacy = use_legacy_ird_report_calculation()
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

    apply_ird_posting_date_filters(filters, conditions, values, "si.posting_date")

    conditions_sql = " AND ".join(conditions) + report_permission_condition(
        "Sales Invoice", "si"
    )

    query = """
        SELECT
            si.name as invoice, si.rounded_total, si.posting_date, si.customer_name, si.tax_id as invoice_pan, si.customer, si.company,
            si.total, si.net_total, si.grand_total, si.summary_grand_total, si.total_taxes_and_charges as total_tax,
            si.customs_declaration_number, si.customs_declaration_date_bs,
            si.taxable_amount as stored_taxable_amount, si.item_vat_detail as stored_item_vat_detail,
            si.ird_party_country as stored_party_country,
            billing_address.country as address_country,
            c.tax_id as customer_tax_id
        FROM `tabSales Invoice` si
        LEFT JOIN `tabCustomer` c ON si.customer = c.name
        LEFT JOIN `tabAddress` billing_address ON billing_address.name = si.customer_address
        WHERE {conditions}
        ORDER BY si.posting_date
    """

    query = query.replace("{conditions}", conditions_sql)

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    vat_breakup = (
        {}
        if legacy
        else get_vat_breakup("Sales Invoice", {inv.invoice: inv.company for inv in invoices})
    )

    invoice_names = [inv.invoice for inv in invoices]
    all_items = []
    for start in range(0, len(invoice_names), ITEM_QUERY_BATCH_SIZE):
        all_items.extend(
            frappe.get_all(
            "Sales Invoice Item",
                filters={
                    "parent": [
                        "in",
                        invoice_names[start : start + ITEM_QUERY_BATCH_SIZE],
                    ]
                },
                fields=[
                    "parent",
                    "is_nontaxable_item",
                    "net_amount",
                    "amount",
                    "item_code",
                    "item_name",
                    "item_tax_template",
                ],
                limit_page_length=0,
            )
        )
    items_by_invoice = {}
    for item in all_items:
        items_by_invoice.setdefault(item.parent, []).append(item)

    item_codes = list({item.item_code for item in all_items if item.item_code})
    asset_items = set()
    for start in range(0, len(item_codes), ITEM_QUERY_BATCH_SIZE):
        asset_items.update(
            frappe.get_all(
                "Item",
                filters={
                    "name": [
                        "in",
                        item_codes[start : start + ITEM_QUERY_BATCH_SIZE],
                    ],
                    "is_fixed_asset": 1,
                },
                pluck="name",
            )
        )

    for inv in invoices:
        customer_country = resolve_ird_country(inv.stored_party_country, inv.address_country)
        is_export = is_foreign_country(customer_country)

        pan = inv.invoice_pan or inv.customer_tax_id

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = 0.0

        items = items_by_invoice.get(inv.invoice, [])

        item_vat_map, stored, breakup = (
            ({}, False, {})
            if legacy
            else resolve_report_vat_source(inv, vat_breakup)
        )
        row_vat = [0.0] * len(items) if legacy else distribute_item_vat(items, item_vat_map)

        for item, item_vat in zip(items, row_vat, strict=True):
            net = flt(item.get("net_amount"))

            is_exempt = (
                legacy_ird_item_is_exempt(item, inv.total_tax)
                if legacy
                else is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup)
            )
            if is_exempt and (legacy or item.get("is_nontaxable_item") or not is_export):
                tax_exempt += net
                continue

            amt = net if legacy else item_taxable_amount(item, item_vat, item_vat_map, 4)
            if item["item_code"] in asset_items:
                capital_taxable_amount += amt
            else:
                if is_export:
                    taxable_import_nc += amt
                else:
                    taxable_domestic_nc += amt
                    tax_domestic_nc += item_vat

        if legacy:
            tax_domestic_nc, _tax_import, _tax_capital = allocate_legacy_ird_tax(
                (taxable_domestic_nc, taxable_import_nc, capital_taxable_amount),
                inv.total_tax,
            )

        data.append({
            "posting_date": inv.posting_date,
            "invoice": inv.invoice,
            **invoice_link_fields("Sales Invoice", inv.invoice),
            "customer_name": inv.customer_name,
            "pan": pan,
            "total": (flt(inv.rounded_total) or flt(inv.grand_total)) if legacy else invoice_ird_total(inv),
            "tax_exempt": tax_exempt,
            "taxable_amount": taxable_domestic_nc,
            "tax_amount": tax_domestic_nc,
            "Value of Exported Goods or Services": inv.net_total if is_export and inv.net_total else inv.total if is_export else 0.0,
            "export_country": customer_country if is_export else "",
            "Export Declaration Number": inv.customs_declaration_number if is_export else "",
            "Export Declaration Date": inv.customs_declaration_date_bs if is_export else "",
        })

    return data
