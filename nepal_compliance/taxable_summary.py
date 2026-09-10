import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import to_csv

from nepal_compliance.utils import set_taxable_amounts

BATCH_SIZE = 500
DOCTYPE_ORDER = ("Sales Invoice", "Purchase Invoice")
TAXABLE_SUMMARY_CSV_COLUMNS = [
    "Type",
    "Invoice",
    "Posting Date",
    "Company",
    "Taxable (Old)",
    "Taxable (New)",
    "Non-Taxable (Old)",
    "Non-Taxable (New)",
    "VAT (Old)",
    "VAT (New)",
    "Bill Total (Old)",
    "Bill Total (New)",
    "Would Change",
    "Group",
    "Expected VAT",
    "Recorded VAT",
    "Difference",
    "Calculation Check",
]


def _ensure_permission():
    """Require write access on Nepal Compliance Settings for refresh actions."""
    if not frappe.has_permission("Nepal Compliance Settings", "write"):
        frappe.throw(_("Not permitted to recompute taxable summary."), frappe.PermissionError)


def _resolve_dates(from_date, to_date):
    """Parse and validate the posting-date range used by preview and apply."""
    from_date = getdate(from_date) if from_date else None
    to_date = getdate(to_date) if to_date else None
    if not from_date or not to_date:
        frappe.throw(_("From Posting Date and To Posting Date are required."))
    if from_date > to_date:
        frappe.throw(_("From Posting Date cannot be after To Posting Date."))
    return from_date, to_date


def _invoice_filters(from_date, to_date):
    """Submitted Sales/Purchase Invoice filters for the posting-date range."""
    return {
        "docstatus": 1,
        "posting_date": ["between", [from_date, to_date]],
    }


def _count_invoices(from_date, to_date):
    """Count submitted sales and purchase invoices in the date range."""
    return sum(
        frappe.db.count(doctype, _invoice_filters(from_date, to_date))
        for doctype in DOCTYPE_ORDER
    )


def _iter_invoice_rows(from_date, to_date):
    """Yield (doctype, row) for submitted invoices, in batches of BATCH_SIZE."""
    fields = [
        "name",
        "company",
        "posting_date",
        "is_return",
        "taxable_amount",
        "non_taxable_amount",
        "vat_amount",
        "summary_grand_total",
    ]
    for doctype in DOCTYPE_ORDER:
        start = 0
        while True:
            rows = frappe.get_all(
                doctype,
                filters=_invoice_filters(from_date, to_date),
                fields=fields,
                limit_start=start,
                limit_page_length=BATCH_SIZE,
                order_by="posting_date, name",
            )
            if not rows:
                break
            for row in rows:
                yield doctype, row
            if len(rows) < BATCH_SIZE:
                break
            start += BATCH_SIZE


SUMMARY_COMPARE_FIELDS = (
    "taxable_amount",
    "non_taxable_amount",
    "vat_amount",
    "summary_grand_total",
)


def _amt(value):
    """Round a money field to 2 decimals, preserving None."""
    return None if value is None else flt(value, 2)


def _figures_changed(old, new):
    """True when taxable, non-taxable, VAT, or Bill Total would change."""
    return any(
        _amt(old.get(field)) != _amt(new.get(field))
        for field in SUMMARY_COMPARE_FIELDS
    )


def _document_type(doctype, is_return):
    if not is_return:
        return doctype
    return "Sales Return" if doctype == "Sales Invoice" else "Purchase Return"


def _compute_refresh_row(doctype, row, consider_is_non_taxable_item=False):
    """Recompute one invoice's taxable summary and classify the result."""
    doc = frappe.get_doc(doctype, row.name)
    if not frappe.has_permission(doctype, "write", doc=doc):
        return "denied", None

    calculation_check = set_taxable_amounts(
        doc,
        None,
        consider_is_non_taxable_item=consider_is_non_taxable_item,
    )
    if doc.get("taxable_amount") is None:
        return "skipped", None

    figures_changed = _figures_changed(row, doc)
    has_warning = bool(
        calculation_check and calculation_check.get("has_vat_mismatch")
    )
    if not figures_changed and not has_warning:
        return "unchanged", None

    return ("changed" if figures_changed else "warning"), {
        "doctype": doctype,
        "document_type": _document_type(doctype, row.get("is_return")),
        "name": row.name,
        "company": row.company,
        "posting_date": str(row.posting_date),
        "would_change": figures_changed,
        "vat_on_added_taxes": bool(
            calculation_check and calculation_check.get("vat_on_added_taxes")
        ),
        "old_taxable_amount": _amt(row.taxable_amount),
        "new_taxable_amount": _amt(doc.taxable_amount),
        "old_non_taxable_amount": _amt(row.non_taxable_amount),
        "new_non_taxable_amount": _amt(doc.non_taxable_amount),
        "old_vat_amount": _amt(row.vat_amount),
        "new_vat_amount": _amt(doc.vat_amount),
        "old_summary_grand_total": _amt(row.summary_grand_total),
        "new_summary_grand_total": _amt(doc.summary_grand_total),
        "summary_grand_total": doc.summary_grand_total,
        "item_vat_detail": doc.get("item_vat_detail"),
        "calculation_check": calculation_check,
    }


def _scan_changes(from_date, to_date, consider_is_non_taxable_item=False):
    """Scan invoices in range and return preview rows plus counts."""
    scanned = 0
    unchanged = 0
    skipped = 0
    denied = 0
    failed = 0
    calculation_warnings = 0
    by_doctype = {doctype: 0 for doctype in DOCTYPE_ORDER}
    changes = []

    for doctype, row in _iter_invoice_rows(from_date, to_date):
        scanned += 1
        try:
            status, change = _compute_refresh_row(
                doctype, row, consider_is_non_taxable_item
            )
        except Exception:
            failed += 1
            frappe.log_error(
                title=_("Taxable Summary Preview Failed for {0}").format(row.name)
            )
            continue
        if status == "skipped":
            skipped += 1
        elif status == "denied":
            denied += 1
        elif status == "unchanged":
            unchanged += 1
        else:
            if change["calculation_check"] and change["calculation_check"].get(
                "has_vat_mismatch"
            ):
                calculation_warnings += 1
            if status == "changed":
                by_doctype[doctype] += 1
            changes.append({k: change[k] for k in change if k != "item_vat_detail"})

    changed = sum(by_doctype.values())
    return {
        "queued": False,
        "from_date": str(from_date),
        "to_date": str(to_date),
        "scanned": scanned,
        "changed": changed,
        "unchanged": unchanged,
        "skipped": skipped,
        "denied": denied,
        "failed": failed,
        "calculation_warnings": calculation_warnings,
        "sales_changed": by_doctype["Sales Invoice"],
        "purchase_changed": by_doctype["Purchase Invoice"],
        "batched": scanned > BATCH_SIZE,
        "changes": changes,
        "consider_is_non_taxable_item": bool(consider_is_non_taxable_item),
    }


def _apply_change(change):
    """Write recomputed taxable summary fields and add a comment on the invoice."""
    frappe.db.set_value(
        change["doctype"],
        change["name"],
        {
            "taxable_amount": change["new_taxable_amount"],
            "non_taxable_amount": change["new_non_taxable_amount"],
            "vat_amount": change["new_vat_amount"],
            "summary_grand_total": change["summary_grand_total"],
            "item_vat_detail": change["item_vat_detail"],
        },
        update_modified=False,
    )
    doc = frappe.get_doc(change["doctype"], change["name"])
    doc.add_comment(
        "Comment",
        _(
            "Nepal Compliance: taxable summary recomputed. "
            "Taxable: {0} → {1}, Non-Taxable: {2} → {3}, "
            "VAT: {4} → {5}, Bill Total: {6} → {7}."
        ).format(
            flt(change["old_taxable_amount"], 2),
            flt(change["new_taxable_amount"], 2),
            flt(change["old_non_taxable_amount"], 2),
            flt(change["new_non_taxable_amount"], 2),
            flt(change["old_vat_amount"], 2),
            flt(change["new_vat_amount"], 2),
            flt(change["old_summary_grand_total"], 2),
            flt(change["new_summary_grand_total"], 2),
        ),
    )


def _parse_selected_invoices(selected_invoices):
    """Return validated selected invoice keys from a JSON/list payload."""
    selected = (
        frappe.parse_json(selected_invoices)
        if isinstance(selected_invoices, str)
        else selected_invoices
    )
    if not isinstance(selected, list):
        frappe.throw(_("Selected invoices must be a list."))

    keys = set()
    for row in selected:
        if not isinstance(row, dict):
            frappe.throw(_("Each selected invoice must include a type and name."))
        doctype = row.get("doctype")
        name = row.get("name")
        if doctype not in DOCTYPE_ORDER or not name:
            frappe.throw(_("Invalid selected invoice: {0} {1}").format(doctype, name))
        keys.add((doctype, name))
    return keys


def _run_apply(
    from_date,
    to_date,
    selected_invoices,
    consider_is_non_taxable_item=False,
):
    """Apply selected recomputed values, committing every BATCH_SIZE invoices."""
    selected = (
        set(selected_invoices)
        if isinstance(selected_invoices, set)
        else _parse_selected_invoices(selected_invoices)
    )
    updated = 0
    denied = 0
    failed = 0
    calculation_warnings = 0
    stale = 0
    batch_count = 0
    for doctype, row in _iter_invoice_rows(from_date, to_date):
        key = (doctype, row.name)
        if key not in selected:
            continue
        selected.remove(key)
        try:
            status, change = _compute_refresh_row(
                doctype, row, consider_is_non_taxable_item
            )
        except Exception:
            failed += 1
            frappe.log_error(
                title=_("Taxable Summary Apply Failed for {0}").format(row.name)
            )
            continue
        if status == "denied":
            denied += 1
            continue
        if status != "changed":
            stale += 1
            continue
        if change["calculation_check"] and change["calculation_check"].get(
            "has_vat_mismatch"
        ):
            calculation_warnings += 1
        _apply_change(change)
        updated += 1
        batch_count += 1
        if batch_count >= BATCH_SIZE:
            frappe.db.commit()  # nosemgrep
            batch_count = 0
    if batch_count:
        frappe.db.commit()  # nosemgrep

    stale += len(selected)
    return {
        "updated": updated,
        "denied": denied,
        "failed": failed,
        "calculation_warnings": calculation_warnings,
        "stale": stale,
    }


def _csv_amount(value):
    """Format a money field for CSV, leaving blanks when unset."""
    return "" if value is None else flt(value, 2)


def taxable_summary_csv_data(changes):
    """Return CSV header plus one row per taxable-summary preview change."""
    data = [TAXABLE_SUMMARY_CSV_COLUMNS]
    for change in changes or []:
        check = change.get("calculation_check") or {}
        data.append(
            [
                change.get("document_type") or change.get("doctype") or "",
                change.get("name") or "",
                change.get("posting_date") or "",
                change.get("company") or "",
                _csv_amount(change.get("old_taxable_amount")),
                _csv_amount(change.get("new_taxable_amount")),
                _csv_amount(change.get("old_non_taxable_amount")),
                _csv_amount(change.get("new_non_taxable_amount")),
                _csv_amount(change.get("old_vat_amount")),
                _csv_amount(change.get("new_vat_amount")),
                _csv_amount(change.get("old_summary_grand_total")),
                _csv_amount(change.get("new_summary_grand_total")),
                _("Yes") if change.get("would_change") else _("No"),
                _("Includes added taxes")
                if change.get("vat_on_added_taxes")
                else _("Suggestion"),
                _csv_amount(check.get("expected_vat")),
                _csv_amount(check.get("recorded_vat")),
                _csv_amount(check.get("vat_difference")),
                _("Mismatch") if check.get("has_vat_mismatch") else _("OK"),
            ]
        )
    return data


@frappe.whitelist(methods=["POST"])
def download_taxable_summary_csv(
    rows: list | str,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Return a CSV file for the selected taxable-summary preview rows."""
    _ensure_permission()
    changes = frappe.parse_json(rows) if isinstance(rows, str) else rows
    if not isinstance(changes, list) or not changes:
        frappe.throw(_("Select at least one row to download."))

    filename = "taxable_summary"
    if from_date and to_date:
        filename = f"taxable_summary_{from_date}_to_{to_date}"
    return {
        "filename": f"{filename}.csv",
        "csv": to_csv(taxable_summary_csv_data(changes)),
    }


@frappe.whitelist(methods=["POST"])
def preview_taxable_summary_refresh(
    from_date: str,
    to_date: str,
    consider_is_non_taxable_item: int | bool = 0,
    request_id: str | None = None,
):
    """Preview invoices whose taxable summary would change in the date range.

    Ranges larger than BATCH_SIZE run on the long queue so the HTTP worker
    is not blocked loading every invoice.
    """
    _ensure_permission()
    from_date, to_date = _resolve_dates(from_date, to_date)
    consider_is_non_taxable_item = bool(cint(consider_is_non_taxable_item))
    scanned = _count_invoices(from_date, to_date)
    if scanned > BATCH_SIZE:
        user = frappe.session.user
        enqueue(
            method="nepal_compliance.taxable_summary.run_taxable_summary_preview",
            queue="long",
            timeout=3600,
            is_async=True,
            from_date=str(from_date),
            to_date=str(to_date),
            consider_is_non_taxable_item=consider_is_non_taxable_item,
            request_id=request_id,
            user=user,
            enqueue_after_commit=True,
        )
        return {
            "queued": True,
            "scanned": scanned,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "request_id": request_id,
        }
    preview = _scan_changes(
        from_date, to_date, consider_is_non_taxable_item
    )
    preview["request_id"] = request_id
    return preview


@frappe.whitelist(methods=["POST"])
def apply_taxable_summary_refresh(
    from_date: str,
    to_date: str,
    selected_invoices: list | str | None = None,
    consider_is_non_taxable_item: int | bool = 0,
    request_id: str | None = None,
):
    """Apply recomputed taxable summary values, enqueueing ranges above BATCH_SIZE."""
    _ensure_permission()
    from_date, to_date = _resolve_dates(from_date, to_date)
    selected = _parse_selected_invoices(selected_invoices or [])
    consider_is_non_taxable_item = bool(cint(consider_is_non_taxable_item))
    if not selected:
        return {
            "queued": False,
            "updated": 0,
            "scanned": 0,
            "request_id": request_id,
        }

    if len(selected) > BATCH_SIZE:
        user = frappe.session.user
        enqueue(
            method="nepal_compliance.taxable_summary.run_taxable_summary_refresh",
            queue="long",
            timeout=3600,
            is_async=True,
            from_date=str(from_date),
            to_date=str(to_date),
            selected_invoices=[
                {"doctype": doctype, "name": name}
                for doctype, name in sorted(selected)
            ],
            consider_is_non_taxable_item=consider_is_non_taxable_item,
            request_id=request_id,
            user=user,
            enqueue_after_commit=True,
        )
        return {
            "queued": True,
            "updated": 0,
            "scanned": len(selected),
            "request_id": request_id,
        }

    result = _run_apply(
        from_date,
        to_date,
        selected,
        consider_is_non_taxable_item,
    )
    return {
        "queued": False,
        "scanned": len(selected),
        "request_id": request_id,
        **result,
    }


def run_taxable_summary_preview(
    from_date: str,
    to_date: str,
    consider_is_non_taxable_item=False,
    request_id=None,
    user=None,
):
    """Background preview scan; publishes taxable_summary_preview_done when finished."""
    from_date, to_date = _resolve_dates(from_date, to_date)
    preview = _scan_changes(
        from_date, to_date, bool(consider_is_non_taxable_item)
    )
    preview["request_id"] = request_id
    frappe.publish_realtime(
        "taxable_summary_preview_done",
        preview,
        user=user or frappe.session.user,
    )
    return preview


def run_taxable_summary_refresh(
    from_date: str,
    to_date: str,
    selected_invoices,
    consider_is_non_taxable_item=False,
    request_id=None,
    user=None,
):
    """Background apply; publishes taxable_summary_refresh_done when finished."""
    from_date, to_date = _resolve_dates(from_date, to_date)
    result = _run_apply(
        from_date,
        to_date,
        selected_invoices,
        bool(consider_is_non_taxable_item),
    )
    frappe.publish_realtime(
        "taxable_summary_refresh_done",
        {
            **result,
            "from_date": str(from_date),
            "to_date": str(to_date),
            "request_id": request_id,
        },
        user=user or frappe.session.user,
    )
    return result
