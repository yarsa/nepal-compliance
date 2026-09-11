"""Configurable checks shared by the four IRD registers."""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.utils import flt

MONEY_TOLERANCE = 0.01
NEPAL_PAN = re.compile(r"^[0-9]{9}$")

ERROR_LABELS = {
    "missing_tax_id": _("Missing Tax ID"),
    "invalid_nepal_tax_id": _("Invalid Nepal Tax ID"),
    "vat_mismatch": _("VAT Mismatch"),
    "total_mismatch": _("Total Mismatch"),
    "missing_purchase_attachment": _("Missing Purchase Attachment"),
    "missing_invoice_number": _("Missing Invoice Number"),
    "invoice_sequence_gap": _("Invoice Sequence Gap"),
    "missing_return_against": _("Missing Original Invoice"),
    "return_value_mismatch": _("Credit/Debit Note Mismatch"),
}


def issue(code, message, *, expected=None, actual=None):
    return {
        "code": code,
        "label": ERROR_LABELS[code],
        "message": message,
        "expected": expected,
        "actual": actual,
    }


def _rule_matches(party, rules, type_field, group_field):
    for rule in rules or []:
        field = type_field if rule.get("match_by") == "Type" else group_field
        if rule.get(field) and rule.get(field) == party.get(field):
            return True
    return False


def check_party_tax_id(context, party, settings):
    if not settings.get("enable_party_tax_id_check") or not party:
        return []

    is_sales = context.get("doctype") == "Sales Invoice"
    rules = settings.get(
        "customer_tax_id_rules" if is_sales else "supplier_tax_id_rules"
    )
    type_field = "customer_type" if is_sales else "supplier_type"
    group_field = "customer_group" if is_sales else "supplier_group"
    if not _rule_matches(party, rules, type_field, group_field):
        return []

    tax_id = str(context.get("tax_id") or party.get("tax_id") or "").strip()
    if not tax_id:
        return [
            issue(
                "missing_tax_id",
                _("Tax ID is required for the configured party type or group."),
            )
        ]
    country = str(context.get("ird_party_country") or "").strip()
    if country.casefold() == "nepal" and not NEPAL_PAN.fullmatch(tax_id):
        return [
            issue(
                "invalid_nepal_tax_id",
                _("A Nepal Tax ID must contain exactly 9 digits."),
                expected="9 digits",
                actual=tax_id,
            )
        ]
    return []


def check_amounts(context, settings):
    errors = []
    taxable = flt(context.get("taxable_amount"))
    non_taxable = flt(context.get("non_taxable_amount"))
    vat = flt(context.get("vat_amount"))
    total = flt(context.get("summary_grand_total"))
    pan_bill = bool(context.get("is_pan_or_abbreviated_bill"))

    if settings.get("enable_vat_amount_check"):
        expected_vat = 0.0 if pan_bill else flt(taxable * 0.13, 2)
        if abs(vat - expected_vat) >= MONEY_TOLERANCE:
            errors.append(
                issue(
                    "vat_mismatch",
                    _("VAT must be 13% of taxable amount."),
                    expected=expected_vat,
                    actual=flt(vat, 2),
                )
            )

    if settings.get("enable_total_amount_check"):
        expected_total = flt(taxable + non_taxable + vat, 2)
        if abs(total - expected_total) >= MONEY_TOLERANCE:
            errors.append(
                issue(
                    "total_mismatch",
                    _("Total must equal taxable + non-taxable + VAT."),
                    expected=expected_total,
                    actual=flt(total, 2),
                )
            )

    return errors


def check_attachment(context, settings):
    if (
        context.get("doctype") == "Purchase Invoice"
        and settings.get("enable_purchase_attachment_check")
        and not context.get("attach_purchase_invoice")
    ):
        return [
            issue(
                "missing_purchase_attachment",
                _("Attach the supplier invoice in Attach Purchase Invoice."),
            )
        ]
    return []


def check_context(context, party, settings):
    return [
        *check_party_tax_id(context, party, settings),
        *check_amounts(context, settings),
        *check_attachment(context, settings),
    ]


def _selected_codes(filters):
    selected = (filters or {}).get("error_types") or []
    if isinstance(selected, str):
        try:
            selected = json.loads(selected)
        except (TypeError, ValueError):
            selected = [selected]
    return set(selected)


def filter_rows(rows, filters):
    selected = _selected_codes(filters)
    if not selected:
        return rows
    return [
        row
        for row in rows
        if selected.intersection(row.get("compliance_error_codes") or [])
    ]


def check_columns():
    return [
        {
            "label": _("Checks"),
            "fieldname": "compliance_checks",
            "fieldtype": "Data",
            "width": 220,
        }
    ]


def check_summary(rows):
    invoices = {}
    for row in rows:
        name = row.get("invoice_name") or row.get("invoice")
        codes = row.get("compliance_error_codes") or []
        if name and codes:
            invoices.setdefault(name, set()).update(codes)
    return {
        "value": len(invoices),
        "label": _("Invoices With Errors"),
        "datatype": "Int",
        "indicator": "Red" if invoices else "Green",
    }
