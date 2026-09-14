"""Sales invoice and return sequence checks for IRD reports."""

from __future__ import annotations

import re
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import getdate

from nepal_compliance.ird_checks import filter_rows, issue
from nepal_compliance.ird_filters import (
    bs_month_to_ad_range,
    current_bs_month_key,
    fiscal_year_ad_range,
)

TRAILING_NUMBER = re.compile(r"^(.*?)([0-9]+)$")


def _missing_ranges(numbers):
    ordered = sorted(set(numbers))
    return [
        (left + 1, right - 1)
        for left, right in zip(ordered, ordered[1:])
        if right - left > 1
    ]


def _occupied_names(filters, is_return):
    filters = filters or {}
    query_filters = {"is_return": int(bool(is_return))}
    if filters.get("company"):
        query_filters["company"] = filters.get("company")

    from_date = filters.get("from_nepali_date")
    to_date = filters.get("to_nepali_date")
    if from_date and to_date:
        query_filters["posting_date"] = [
            "between",
            [getdate(from_date), getdate(to_date)],
        ]
    elif from_date:
        query_filters["posting_date"] = [">=", getdate(from_date)]
    elif to_date:
        query_filters["posting_date"] = ["<=", getdate(to_date)]
    elif filters.get("bs_month"):
        query_filters["posting_date"] = [
            "between",
            list(bs_month_to_ad_range(filters.get("bs_month"))),
        ]
    elif filters.get("fiscal_year"):
        query_filters["posting_date"] = [
            "between",
            list(fiscal_year_ad_range(filters.get("fiscal_year"))),
        ]
    else:
        query_filters["posting_date"] = [
            "between",
            list(bs_month_to_ad_range(current_bs_month_key())),
        ]
    return frappe.get_list(
        "Sales Invoice",
        filters=query_filters,
        fields=["name", "company"],
        limit_page_length=0,
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
