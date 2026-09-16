"""Sales invoice and return sequence checks for IRD reports."""

from __future__ import annotations

import re
from collections import defaultdict

import frappe
from frappe import _

from nepal_compliance.ird_checks import filter_rows, issue
from nepal_compliance.ird_filters import apply_ird_posting_date_filters

TRAILING_NUMBER = re.compile(r"^(.*?)([0-9]+)$")


def _missing_ranges(numbers):
    ordered = sorted(set(numbers))
    return [
        (left + 1, right - 1)
        for left, right in zip(ordered, ordered[1:])
        if right - left > 1
    ]


def _occupied_names(filters, is_return):
    conditions = ["si.is_return = %(is_return)s"]
    values = {"is_return": int(bool(is_return))}
    if (filters or {}).get("company"):
        conditions.append("si.company = %(company)s")
        values["company"] = filters.get("company")
    apply_ird_posting_date_filters(filters, conditions, values, "si.posting_date")
    return frappe.db.sql(
        f"""
        SELECT si.name, si.company
        FROM `tabSales Invoice` si
        WHERE {" AND ".join(conditions)}
        """,
        values,
        as_dict=True,
    )


def _gap_rows(filters, is_return):
    groups = defaultdict(list)
    for row in _occupied_names(filters, is_return):
        match = TRAILING_NUMBER.fullmatch(row.name or "")
        if not match:
            continue
        prefix, number = match.groups()
        groups[(row.company, prefix, len(number))].append(int(number))

    rows = []
    for (company, prefix, width), numbers in sorted(groups.items()):
        for start, finish in _missing_ranges(numbers):
            first = f"{prefix}{start:0{width}d}"
            last = f"{prefix}{finish:0{width}d}"
            label = first if first == last else f"{first} – {last}"
            error = issue(
                "invoice_sequence_gap",
                _("Invoice number is absent from the selected period and series."),
                expected=label,
                actual=_("Absent"),
            )
            rows.append(
                frappe._dict(
                    invoice=_("Missing: {0}").format(label),
                    invoice_name="",
                    invoice_doctype="",
                    company=company,
                    is_compliance_issue=1,
                    compliance_errors=[error],
                    compliance_error_codes=[error["code"]],
                    compliance_checks=error["label"],
                )
            )
    return rows


def append_sequence_gaps(rows, filters, is_return=False):
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    if not settings.get("enable_sales_invoice_number_check"):
        return rows
    return filter_rows([*rows, *_gap_rows(filters, is_return)], filters)
