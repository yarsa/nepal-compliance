# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate

from nepal_compliance.ird_country import is_foreign_country, resolve_ird_country
from nepal_compliance.ird_filters import (
    apply_ird_posting_date_filters,
    invoice_link_fields,
    is_prior_fy_bill,
    resolve_ird_fiscal_year_start,
)
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs
from nepal_compliance.utils import (
    distribute_item_vat,
    get_vat_breakup,
    invoice_ird_total,
    is_exempt_report_item,
    item_taxable_amount,
    resolve_report_vat_source,
)


def _bill_posting_date_meta(bill_date, posting_date):
    """Return BS month-mismatch flag and absolute day gap for bill vs posting date."""
    if not bill_date or not posting_date:
        return {"bill_month_mismatch": 0, "bill_posting_day_diff": None}
    bill = getdate(bill_date)
    posting = getdate(posting_date)
    bill_bs = ad_to_bs(bill)
    posting_bs = ad_to_bs(posting)
    return {
        "bill_month_mismatch": int(
            (bill_bs["year"], bill_bs["month"]) != (posting_bs["year"], posting_bs["month"])
        ),
        "bill_posting_day_diff": abs(date_diff(posting, bill)),
    }


def _has_bs_month_mismatch(row) -> bool:
    """True when row is flagged as BS month mismatch."""
    return bool(int(row.get("bill_month_mismatch") or 0))


def get_purchase_register_summary(rows, prior_fy_count=0):
    """Build colored summary cards for the main Purchase Register table."""
    rows = [r for r in (rows or []) if not r.get("is_prior_fy") and not r.get("is_section")]
    total = len(rows)
    same_bs_month = sum(1 for r in rows if r.get("bill_date") and not _has_bs_month_mismatch(r))
    diff_bs_month = sum(1 for r in rows if r.get("bill_date") and _has_bs_month_mismatch(r))
    tax_exempt = sum(1 for r in rows if flt(r.get("tax_exempt")) > 0)
    taxable = sum(1 for r in rows if flt(r.get("taxable_amount")) > 0)
    taxable_import = sum(1 for r in rows if flt(r.get("taxable_import_non_capital_amount")) > 0)
    capital = sum(1 for r in rows if flt(r.get("capital_taxable_amount")) > 0)

    summary = [
        {
            "value": total,
            "label": _("Total Purchases"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": same_bs_month,
            "label": _("Same BS Month (Entry vs Bill)"),
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "value": diff_bs_month,
            "label": _("Different BS Month (Entry vs Bill)"),
            "datatype": "Int",
            "indicator": "Orange",
        },
        {
            "value": tax_exempt,
            "label": _("कर छुट हुने खरिद"),
            "datatype": "Int",
            "indicator": "Grey",
        },
        {
            "value": taxable,
            "label": _("करयोग्य खरिद"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": taxable_import,
            "label": _("करयोग्य पैठारी"),
            "datatype": "Int",
            "indicator": "Blue",
        },
        {
            "value": capital,
            "label": _("पूंजीगत खरिद"),
            "datatype": "Int",
            "indicator": "Grey",
        },
    ]
    if prior_fy_count:
        summary.append(
            {
                "value": prior_fy_count,
                "label": _("Prior Fiscal Year Purchases"),
                "datatype": "Int",
                "indicator": "Red",
            }
        )
    return summary


def execute(filters=None):
    """Run the IRD Purchase Register and return columns, rows, and summary."""
    columns = get_columns()
    data = get_data(filters, bucket="all")
    prior_fy_count = sum(1 for r in data if r.get("is_prior_fy"))
    summary = get_purchase_register_summary(data, prior_fy_count=prior_fy_count)
    return columns, data, None, None, summary


def get_columns():
    """Column definitions for the IRD Purchase Register."""
    return [
        {"label": _("मिति"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Data", "width": 200},
        {"label": _("बीजक मिति"), "fieldname": "bill_date", "fieldtype": "Date", "width": 120},
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


def get_data(filters, bucket="all"):
    """Build purchase register rows from submitted invoices in the filter range.

    *bucket* controls which rows are returned:
    - ``eligible``: bill_date on/after selected FY start (or blank bill_date)
    - ``prior_fy``: bill_date before selected FY start
    - ``all``: eligible then prior-FY rows (prior marked ``is_prior_fy`` for dual tables)
    """
    filters = filters or {}
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

    apply_ird_posting_date_filters(filters, conditions, values, "pi.posting_date")

    conditions_sql = " AND ".join(conditions)

    query = """
        SELECT
            pi.name as invoice, pi.bill_no, pi.bill_date, pi.customs_declaration_number, pi.rounded_total, pi.grand_total, pi.summary_grand_total, pi.posting_date,
            pi.supplier_name, pi.tax_id as invoice_pan, pi.total, pi.supplier, pi.company,
            pi.taxable_amount as stored_taxable_amount, pi.item_vat_detail as stored_item_vat_detail,
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
    if not invoices:
        return []

    eligible = []
    prior_fy = []

    vat_breakup = get_vat_breakup("Purchase Invoice", {inv.invoice: inv.company for inv in invoices})

    invoice_names = [inv.invoice for inv in invoices]
    all_items = frappe.get_all(
        "Purchase Invoice Item",
        filters={"parent": ["in", invoice_names]},
        fields=["parent", "is_nontaxable_item", "net_amount", "amount", "asset_category", "item_code", "item_name"],
        limit_page_length=0
    )
    items_by_invoice = {}
    for item in all_items:
        items_by_invoice.setdefault(item.parent, []).append(item)

    fy_start = resolve_ird_fiscal_year_start(filters)

    for inv in invoices:
        supplier_country = resolve_ird_country(inv.stored_party_country, inv.address_country)
        is_import = is_foreign_country(supplier_country)

        pan = inv.invoice_pan or inv.supplier_tax_id

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0
        tax_domestic_nc = tax_import_nc = tax_capital = 0.0

        items = items_by_invoice.get(inv.invoice, [])
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

        row = {
            "posting_date": inv.posting_date,
            "invoice": inv.bill_no if inv.bill_no else inv.invoice,
            **invoice_link_fields("Purchase Invoice", inv.invoice),
            "bill_date": inv.bill_date,
            "customs_declaration_number": inv.customs_declaration_number if is_import else "",
            "supplier_name": inv.supplier_name,
            "pan": pan,
            "total": invoice_ird_total(inv),
            "tax_exempt": tax_exempt,
            "taxable_amount": taxable_domestic_nc,
            "tax_amount": tax_domestic_nc,
            "taxable_import_non_capital_amount": taxable_import_nc,
            "taxable_import_non_capital_tax": tax_import_nc,
            "capital_taxable_amount": capital_taxable_amount,
            "capital_taxable_tax": tax_capital,
            **_bill_posting_date_meta(inv.bill_date, inv.posting_date),
        }

        if is_prior_fy_bill(inv.bill_date, fy_start):
            row["is_prior_fy"] = 1
            prior_fy.append(row)
        else:
            eligible.append(row)

    if bucket == "eligible":
        return eligible
    if bucket == "prior_fy":
        return prior_fy

    return eligible + prior_fy
