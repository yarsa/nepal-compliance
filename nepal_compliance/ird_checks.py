"""Configurable checks shared by the four IRD registers."""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.utils import flt

MONEY_TOLERANCE = 0.01
VAT_CHECK_PRECISION = 4
NEPAL_PAN = re.compile(r"^[0-9]{9}$")
IRD_CHECK_FIELDS = (
    "enable_party_tax_id_check",
    "enable_vat_amount_check",
    "enable_total_amount_check",
    "enable_sales_invoice_number_check",
    "enable_purchase_attachment_check",
    "enable_purchase_vat_tax_id_check",
    "enable_return_match_check",
)

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
    if not party:
        return []

    is_sales = context.get("doctype") == "Sales Invoice"
    vat = (
        context.get("check_vat_amount")
        if context.get("check_vat_amount") is not None
        else context.get("vat_amount")
    )
    vat_requires_tax_id = (
        not is_sales
        and settings.get("enable_purchase_vat_tax_id_check")
        and abs(flt(vat)) >= MONEY_TOLERANCE
    )
    rules = settings.get(
        "customer_tax_id_rules" if is_sales else "supplier_tax_id_rules"
    )
    type_field = "customer_type" if is_sales else "supplier_type"
    group_field = "customer_group" if is_sales else "supplier_group"
    rule_requires_tax_id = settings.get("enable_party_tax_id_check") and _rule_matches(
        party, rules, type_field, group_field
    )
    if not vat_requires_tax_id and not rule_requires_tax_id:
        return []

    tax_id = str(context.get("tax_id") or party.get("tax_id") or "").strip()
    if not tax_id:
        message = (
            _("Tax ID is required when a Purchase Invoice includes VAT.")
            if vat_requires_tax_id
            else _("Tax ID is required for the configured party type or group.")
        )
        return [
            issue(
                "missing_tax_id",
                message,
            )
        ]
    country = str(
        context.get("ird_party_country") or party.get("country") or "Nepal"
    ).strip()
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
    taxable = flt(
        context.get("check_taxable_amount")
        if context.get("check_taxable_amount") is not None
        else context.get("taxable_amount")
    )
    non_taxable = flt(
        context.get("check_non_taxable_amount")
        if context.get("check_non_taxable_amount") is not None
        else context.get("non_taxable_amount")
    )
    vat = flt(
        context.get("check_vat_amount")
        if context.get("check_vat_amount") is not None
        else context.get("vat_amount")
    )
    total = flt(context.get("summary_grand_total"))
    pan_bill = bool(context.get("is_pan_or_abbreviated_bill"))

    if settings.get("enable_vat_amount_check"):
        expected_vat = (
            0.0 if pan_bill else flt(taxable * 0.13, VAT_CHECK_PRECISION)
        )
        actual_vat = flt(vat, VAT_CHECK_PRECISION)
        if actual_vat != expected_vat:
            errors.append(
                issue(
                    "vat_mismatch",
                    _("VAT must be 13% of taxable amount."),
                    expected=expected_vat,
                    actual=actual_vat,
                )
            )

    if settings.get("enable_total_amount_check"):
        expected_total = flt(taxable + non_taxable + vat, 2)
        allowed_totals = [expected_total]
        if not context.get("disable_rounded_total"):
            allowed_totals.append(flt(taxable + non_taxable + vat, 0))
        if all(abs(total - allowed) >= MONEY_TOLERANCE for allowed in allowed_totals):
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
    field_attachment = context.get("attach_purchase_invoice") or context.get(
        "has_accepted_purchase_attachment"
    )
    sidebar_attachment = (
        settings.get("consider_sidebar_purchase_attachments")
        and context.get("has_sidebar_purchase_attachment")
    )
    if (
        context.get("doctype") == "Purchase Invoice"
        and settings.get("enable_purchase_attachment_check")
        and not field_attachment
        and not sidebar_attachment
    ):
        return [
            issue(
                "missing_purchase_attachment",
                _("Attach the supplier invoice in an accepted attachment field or the sidebar."),
            )
        ]
    return []


def check_return_reference(context, settings):
    if (
        settings.get("enable_return_match_check")
        and context.get("is_return")
        and not context.get("return_against")
    ):
        return [
            issue(
                "missing_return_against",
                _("Select the original invoice in Return Against."),
            )
        ]
    return []


def check_context(context, party, settings):
    return [
        *check_party_tax_id(context, party, settings),
        *check_amounts(context, settings),
        *check_attachment(context, settings),
        *check_return_reference(context, settings),
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


def filter_summary_rows(rows, filters):
    """Filter report rows when a summary card is selected."""
    view = (filters or {}).get("ird_summary_view")
    if not view or view == "all":
        return rows

    def matches(row):
        if view == "errors":
            return bool(row.get("compliance_error_codes"))
        if view == "tax_exempt":
            return flt(row.get("tax_exempt")) > 0
        if view == "taxable":
            return any(
                flt(row.get(fieldname)) > 0
                for fieldname in (
                    "taxable_amount",
                    "taxable_import_non_capital_amount",
                    "capital_taxable_amount",
                )
            )
        if view == "export":
            return flt(row.get("Value of Exported Goods or Services")) > 0
        if view == "import":
            return flt(row.get("taxable_import_non_capital_amount")) > 0
        if view == "capital":
            return flt(row.get("capital_taxable_amount")) > 0
        if view == "prior_fy":
            return bool(row.get("is_prior_fy"))
        if view == "same_bs_month":
            return bool(row.get("bill_date")) and not row.get("bill_month_mismatch")
        if view == "different_bs_month":
            return bool(row.get("bill_date")) and bool(row.get("bill_month_mismatch"))
        return True

    return [row for row in rows if matches(row)]


def checks_enabled(settings=None):
    if settings is None:
        settings = frappe.get_cached_doc("Nepal Compliance Settings")
    return any(settings.get(fieldname) for fieldname in IRD_CHECK_FIELDS)


def check_columns(columns, settings=None):
    """Insert enabled compliance columns without disturbing the register layout."""
    if settings is None:
        settings = frappe.get_cached_doc("Nepal Compliance Settings")
    columns = list(columns)
    if not checks_enabled(settings):
        return columns

    columns.insert(
        1,
        {
            "label": _("Checks"),
            "fieldname": "compliance_checks",
            "fieldtype": "Data",
            "width": 220,
        },
    )
    if settings.get("enable_return_match_check"):
        columns.append(
            {
                "label": _("Credit / Debit Note"),
                "fieldname": "adjustment_notes",
                "fieldtype": "Data",
                "width": 180,
            }
        )
    return columns


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
        "ird_view": "errors",
    }


def _submitted_returns(doctype, source_names):
    if not source_names:
        return {}
    grouped = {}
    rows = frappe.get_all(
        doctype,
        filters={
            "docstatus": 1,
            "is_return": 1,
            "return_against": ["in", source_names],
        },
        fields=["name", "return_against"],
        limit_page_length=0,
    )
    for row in rows:
        grouped.setdefault(row.return_against, []).append(row.name)
    return grouped


def _accepted_purchase_attachment_fields(settings):
    fields = {"attach_purchase_invoice"}
    selected = {
        row.get("custom_field")
        for row in (settings.get("accepted_purchase_attachment_fields") or [])
        if row.get("custom_field")
    }
    if selected:
        fields.update(
            frappe.get_all(
                "Custom Field",
                filters={
                    "name": ["in", list(selected)],
                    "dt": "Purchase Invoice",
                    "fieldtype": ["in", ["Attach", "Attach Image"]],
                },
                pluck="fieldname",
            )
        )
    return fields


def _invoice_contexts(doctype, names, settings=None):
    if not names:
        return {}
    party_field = "customer" if doctype == "Sales Invoice" else "supplier"
    address_field = (
        "customer_address" if doctype == "Sales Invoice" else "supplier_address"
    )
    fields = [
        "name",
        "company",
        "currency",
        "conversion_rate",
        "is_return",
        "return_against",
        "disable_rounded_total",
        "tax_id",
        "ird_party_country",
        "taxable_amount",
        "non_taxable_amount",
        "vat_amount",
        "summary_grand_total",
        party_field,
        address_field,
    ]
    attachment_fields = set()
    if doctype == "Purchase Invoice":
        attachment_fields = _accepted_purchase_attachment_fields(settings or {})
        fields.extend(["is_pan_or_abbreviated_bill", *sorted(attachment_fields)])
    rows = frappe.get_all(
        doctype,
        filters={"name": ["in", names]},
        fields=fields,
        limit_page_length=0,
    )
    for row in rows:
        row.doctype = doctype
    address_names = {row.get(address_field) for row in rows if row.get(address_field)}
    countries = (
        dict(
            frappe.get_all(
                "Address",
                filters={"name": ["in", list(address_names)]},
                fields=["name", "country"],
                as_list=True,
                limit_page_length=0,
            )
        )
        if address_names
        else {}
    )
    for row in rows:
        row.ird_party_country = (
            row.get("ird_party_country") or countries.get(row.get(address_field)) or ""
        )
        if attachment_fields:
            row.has_accepted_purchase_attachment = any(
                row.get(fieldname) for fieldname in attachment_fields
            )
    if (
        doctype == "Purchase Invoice"
        and settings
        and settings.get("enable_purchase_attachment_check")
        and settings.get("consider_sidebar_purchase_attachments")
    ):
        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": doctype,
                "attached_to_name": ["in", names],
                "is_folder": 0,
            },
            fields=["attached_to_name", "attached_to_field", "file_url"],
            limit_page_length=0,
        )
        attached_names = {
            file.attached_to_name
            for file in files
            if file.file_url and not file.attached_to_field
        }
        for row in rows:
            row.has_sidebar_purchase_attachment = row.name in attached_names
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


def _invoice_hover_items(doctype, contexts):
    if not contexts:
        return {}
    item_doctype = f"{doctype} Item"
    rows = frappe.get_all(
        item_doctype,
        filters={"parent": ["in", list(contexts)]},
        fields=[
            "parent",
            "item_code",
            "item_name",
            "qty",
            "uom",
            "net_rate",
            "net_amount",
            "is_nontaxable_item",
            "item_tax_template",
        ],
        order_by="parent, idx",
        limit_page_length=0,
    )
    item_codes = list({row.item_code for row in rows if row.item_code})
    fixed_assets = (
        set(
            frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes], "is_fixed_asset": 1},
                pluck="name",
            )
        )
        if item_codes
        else set()
    )
    grouped = {}
    for row in rows:
        context = contexts[row.parent]
        has_invoice_vat = abs(flt(context.get("check_vat_amount"))) > 0
        grouped.setdefault(row.parent, []).append(
            {
                "item_name": row.item_name or row.item_code,
                "qty": abs(flt(row.qty)),
                "uom": row.uom,
                "rate": abs(flt(row.net_rate)),
                "amount": abs(flt(row.net_amount)),
                "is_taxable": not row.is_nontaxable_item
                and bool(row.item_tax_template or has_invoice_vat),
                "is_fixed_asset": row.item_code in fixed_assets,
            }
        )
    return grouped


def _report_check_amounts(rows, contexts):
    """Collect the precise taxable and VAT values displayed by the register."""
    amount_fields = (
        "taxable_amount",
        "taxable_import_non_capital_amount",
        "capital_taxable_amount",
        "tax_amount",
        "taxable_import_non_capital_tax",
        "capital_taxable_tax",
        "tax_exempt",
    )
    amounts = {}
    for row in rows:
        name = row.get("invoice_name")
        if (
            not name
            or row.get("is_section")
            or not any(fieldname in row for fieldname in amount_fields)
        ):
            continue
        values = amounts.setdefault(
            name,
            {"taxable": 0.0, "non_taxable": 0.0, "vat": 0.0},
        )
        values["taxable"] += sum(
            flt(row.get(fieldname))
            for fieldname in (
                "taxable_amount",
                "taxable_import_non_capital_amount",
                "capital_taxable_amount",
            )
        )
        values["vat"] += sum(
            flt(row.get(fieldname))
            for fieldname in (
                "tax_amount",
                "taxable_import_non_capital_tax",
                "capital_taxable_tax",
            )
        )
        values["non_taxable"] += flt(row.get("tax_exempt"))

    for name, values in amounts.items():
        context = contexts.get(name)
        if not context:
            continue
        sign = -1 if context.get("is_return") else 1
        context.check_taxable_amount = sign * values["taxable"]
        context.check_non_taxable_amount = sign * values["non_taxable"]
        context.check_vat_amount = sign * values["vat"]


def decorate_rows(rows, doctype, filters=None):
    """Attach configured errors to report rows, then apply the error filter."""
    names = list(
        {
            row.get("invoice_name")
            for row in rows
            if row.get("invoice_name") and not row.get("is_section")
        }
    )
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    contexts = _invoice_contexts(doctype, names, settings)
    _report_check_amounts(rows, contexts)
    hover_items = _invoice_hover_items(doctype, contexts)
    parties = _parties(doctype, contexts)
    returns_by_source = _submitted_returns(doctype, names)
    party_field = "customer" if doctype == "Sales Invoice" else "supplier"
    errors_by_invoice = {
        name: check_context(
            context,
            parties.get(context.get(party_field)),
            settings,
        )
        for name, context in contexts.items()
    }
    if settings.get("enable_return_match_check"):
        from nepal_compliance.ird_return_checks import return_match_errors

        for name, errors in return_match_errors(doctype, names).items():
            errors_by_invoice.setdefault(name, []).extend(errors)

    for row in rows:
        context = contexts.get(row.get("invoice_name"))
        party = parties.get(context.get(party_field)) if context else None
        errors = list(errors_by_invoice.get(row.get("invoice_name"), []))
        if (
            doctype == "Sales Invoice"
            and settings.get("enable_sales_invoice_number_check")
            and row.get("invoice_doctype")
            and not str(row.get("invoice") or "").strip()
        ):
            errors.append(
                issue(
                    "missing_invoice_number",
                    _("The Sales Invoice or Sales Return number is blank."),
                )
            )
        row["compliance_errors"] = errors
        row["compliance_error_codes"] = [error["code"] for error in errors]
        row["compliance_checks"] = ", ".join(error["label"] for error in errors)
        if context and context.get("is_return"):
            note_names = [context.get("return_against")] if context.get("return_against") else []
        else:
            note_names = returns_by_source.get(row.get("invoice_name"), [])
        row["adjustment_note_links"] = [
            {"doctype": doctype, "name": name} for name in note_names
        ]
        row["adjustment_notes"] = ", ".join(note_names)
        row["invoice_hover_items"] = hover_items.get(row.get("invoice_name"), [])
        row["party_type"] = (
            party.get("customer_type") or party.get("supplier_type") if party else ""
        )
        row["party_group"] = (
            party.get("customer_group") or party.get("supplier_group") if party else ""
        )
    return filter_rows(rows, filters)
