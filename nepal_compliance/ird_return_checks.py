"""Partial-safe credit/debit note comparisons for IRD reports."""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from nepal_compliance.ird_checks import MONEY_TOLERANCE, issue
from nepal_compliance.utils import distribute_item_vat, get_vat_breakup


def _different(left, right):
    return abs(flt(left) - flt(right)) >= MONEY_TOLERANCE


def _headers(doctype, report_names):
    party = "customer" if doctype == "Sales Invoice" else "supplier"
    fields = [
        "name",
        party,
        "company",
        "currency",
        "conversion_rate",
        "is_return",
        "return_against",
        "taxable_amount",
        "non_taxable_amount",
        "vat_amount",
        "summary_grand_total",
    ]
    report_docs = frappe.get_all(
        doctype,
        filters={"name": ["in", report_names]},
        fields=fields,
        limit_page_length=0,
    )
    linked_returns = frappe.get_all(
        doctype,
        filters={
            "docstatus": 1,
            "is_return": 1,
            "return_against": ["in", report_names],
        },
        fields=fields,
        limit_page_length=0,
    )
    docs = {row.name: row for row in [*report_docs, *linked_returns]}
    source_names = {row.return_against for row in docs.values() if row.return_against}
    missing = source_names.difference(docs)
    if missing:
        for row in frappe.get_all(
            doctype,
            filters={"name": ["in", list(missing)]},
            fields=fields,
            limit_page_length=0,
        ):
            docs[row.name] = row
    return docs


def _items(doctype, names):
    item_doctype = f"{doctype} Item"
    source_field = (
        "sales_invoice_item" if doctype == "Sales Invoice" else "purchase_invoice_item"
    )
    rows = frappe.get_all(
        item_doctype,
        filters={"parent": ["in", names]},
        fields=[
            "name",
            "parent",
            "item_code",
            "item_name",
            "uom",
            "qty",
            "rate",
            "net_rate",
            "net_amount",
            "item_tax_template",
            source_field,
        ],
        limit_page_length=0,
    )
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.parent].append(row)
    return grouped, source_field


def _item_vat(doctype, docs, items):
    breakup = get_vat_breakup(
        doctype, {name: row.company for name, row in docs.items()}
    )
    result = {}
    configured = {
        name: bool((breakup.get(name) or {}).get("configured")) for name in docs
    }
    for name, invoice_items in items.items():
        vat_map = (breakup.get(name) or {}).get("item_vat") or {}
        allocated = distribute_item_vat(invoice_items, vat_map)
        result.update(
            {
                (name, row.name): amount
                for row, amount in zip(invoice_items, allocated, strict=True)
            }
        )
    return result, configured


def _vat_ready(note, source, vat_configured):
    if vat_configured is None:
        return True
    return bool(vat_configured.get(note.name) and vat_configured.get(source.name))


def _compare_pair(doctype, note, source, items, source_field, item_vat, vat_configured=None):
    differences = []
    party = "customer" if doctype == "Sales Invoice" else "supplier"
    for field in (party, "company", "currency"):
        if note.get(field) != source.get(field):
            differences.append(_("{0} differs").format(frappe.unscrub(field)))
    if _different(note.conversion_rate, source.conversion_rate):
        differences.append(_("Exchange rate differs"))

    source_items = {row.name: row for row in items.get(source.name, [])}
    expected_taxable = expected_non_taxable = expected_vat = 0.0
    vat_ready = _vat_ready(note, source, vat_configured)
    for row in items.get(note.name, []):
        source_row = source_items.get(row.get(source_field))
        if not source_row:
            differences.append(_("Item {0} is not linked to the original row").format(row.item_code))
            continue
        for field in ("item_code", "uom", "item_tax_template"):
            if row.get(field) != source_row.get(field):
                differences.append(
                    _("{0} differs for item {1}").format(
                        frappe.unscrub(field), row.item_code
                    )
                )
        if _different(abs(row.rate), abs(source_row.rate)) or _different(
            abs(row.net_rate), abs(source_row.net_rate)
        ):
            differences.append(_("Rate differs for item {0}").format(row.item_code))

        if not vat_ready:
            continue
        ratio = abs(flt(row.qty)) / abs(flt(source_row.qty)) if source_row.qty else 0
        source_vat = abs(flt(item_vat.get((source.name, source_row.name)))) * ratio
        note_vat = abs(flt(item_vat.get((note.name, row.name))))
        if bool(source_vat) != bool(note_vat):
            differences.append(_("VAT treatment differs for item {0}").format(row.item_code))
        if source_vat:
            expected_taxable += source_vat / 0.13
            expected_vat += source_vat
        else:
            expected_non_taxable += abs(flt(source_row.net_amount)) * ratio

    if vat_ready:
        expected = {
            "taxable_amount": expected_taxable,
            "non_taxable_amount": expected_non_taxable,
            "vat_amount": expected_vat,
            "summary_grand_total": expected_taxable + expected_non_taxable + expected_vat,
        }
        for field, value in expected.items():
            if _different(abs(flt(note.get(field))), value):
                differences.append(
                    _("{0} is not proportional").format(frappe.unscrub(field))
                )
    return list(dict.fromkeys(differences))


def return_match_errors(doctype, report_names):
    """Return mismatch errors keyed by both note and original invoice."""
    docs = _headers(doctype, report_names)
    items, source_field = _items(doctype, list(docs))
    item_vat, vat_configured = _item_vat(doctype, docs, items)
    errors = defaultdict(list)
    for note in docs.values():
        if not note.is_return or not note.return_against:
            continue
        source = docs.get(note.return_against)
        if not source:
            continue
        differences = _compare_pair(
            doctype, note, source, items, source_field, item_vat, vat_configured
        )
        if not differences:
            continue
        error = issue(
            "return_value_mismatch",
            _("{0}: {1}").format(note.name, "; ".join(differences)),
        )
        errors[note.name].append(error)
        errors[source.name].append(error)
    return errors
