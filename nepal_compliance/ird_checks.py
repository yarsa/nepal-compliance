"""Configurable checks shared by the four IRD registers."""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.utils import flt

MONEY_TOLERANCE = 0.01
NEPAL_PAN = re.compile(r"^[0-9]{9}$")

def error_labels():
    return {
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
        "label": error_labels()[code],
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


def _invoice_contexts(doctype, names):
    if not names:
        return {}
    party_field = "customer" if doctype == "Sales Invoice" else "supplier"
    fields = [
        "name",
        "company",
        "currency",
        "conversion_rate",
        "is_return",
        "return_against",
        "tax_id",
        "ird_party_country",
        "taxable_amount",
        "non_taxable_amount",
        "vat_amount",
        "summary_grand_total",
        party_field,
    ]
    if doctype == "Purchase Invoice":
        fields.extend(["attach_purchase_invoice", "is_pan_or_abbreviated_bill"])
    rows = frappe.get_all(
        doctype,
        filters={"name": ["in", names]},
        fields=fields,
        limit_page_length=0,
    )
    for row in rows:
        row.doctype = doctype
    return {row.name: row for row in rows}


def _parties(doctype, contexts):
    party_doctype = "Customer" if doctype == "Sales Invoice" else "Supplier"
    party_field = party_doctype.lower()
    names = {row.get(party_field) for row in contexts.values() if row.get(party_field)}
    if not names:
        return {}
    fields = ["name", "tax_id"]
    if party_doctype == "Customer":
        fields.extend(["customer_type", "customer_group"])
    else:
        fields.extend(["supplier_type", "supplier_group", "country"])
    return {
        row.name: row
        for row in frappe.get_all(
            party_doctype,
            filters={"name": ["in", list(names)]},
            fields=fields,
            limit_page_length=0,
        )
    }


def decorate_rows(rows, doctype, filters=None):
    """Attach configured errors to report rows, then apply the error filter."""
    names = list(
        {
            row.get("invoice_name")
            for row in rows
            if row.get("invoice_name") and not row.get("is_section")
        }
    )
    contexts = _invoice_contexts(doctype, names)
    parties = _parties(doctype, contexts)
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    party_field = "customer" if doctype == "Sales Invoice" else "supplier"
    errors_by_invoice = {
        name: check_context(
            context,
            parties.get(context.get(party_field)),
            settings,
        )
        for name, context in contexts.items()
    }

    for row in rows:
        errors = errors_by_invoice.get(row.get("invoice_name"), [])
        row["compliance_errors"] = errors
        row["compliance_error_codes"] = [error["code"] for error in errors]
        row["compliance_checks"] = ", ".join(error["label"] for error in errors)
    return filter_rows(rows, filters)
