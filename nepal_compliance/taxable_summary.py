import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from frappe.utils.background_jobs import enqueue
from frappe.utils.csvutils import to_csv

from nepal_compliance.utils import get_configured_vat_accounts, set_taxable_amounts, vat_side

BATCH_SIZE = 500
DOCTYPE_ORDER = ("Sales Invoice", "Purchase Invoice", "Sales Order")
# a Sales Order has no posting date; it is filtered by its order date
DATE_FIELDS = {"Sales Order": "transaction_date"}
VAT_ACCOUNTING_ERROR_TAG = "VAT Accounting Error"
BILL_SUMMARY_MISSING_TAG = "Bill Summary Missing"
NEGATIVE_DISCOUNT_TAG = "Negative Discount"
PRICE_GAP_TAG = "Price Gap as Discount"
DISCOUNT_VAT_TWICE_TAG = "Discount VAT Removed Twice"
TAXABLE_SPLIT_TAG = "Taxable Split Changed"
CORRECTED_TAG = "Bill Summary Corrected"
TAXABLE_SUMMARY_CSV_COLUMNS = [
    "Type",
    "Document",
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
    "Subtotal (Old)",
    "Subtotal (New)",
    "Discount (Old)",
    "Discount (New)",
    "Tags",
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


def _date_field(doctype):
    return DATE_FIELDS.get(doctype, "posting_date")


def _invoice_filters(doctype, from_date, to_date):
    """Submitted-document filters for the date range, on the doctype's own date field."""
    return {
        "docstatus": 1,
        _date_field(doctype): ["between", [from_date, to_date]],
    }


def _count_invoices(from_date, to_date):
    """Count submitted documents of every recomputed doctype in the date range."""
    return sum(
        frappe.db.count(doctype, _invoice_filters(doctype, from_date, to_date))
        for doctype in DOCTYPE_ORDER
    )


def _iter_invoice_rows(from_date, to_date):
    """Yield (doctype, row) for submitted documents, in batches of BATCH_SIZE.

    Each row's date is read as posting_date, whatever the doctype calls it.
    """
    for doctype in DOCTYPE_ORDER:
        date_field = _date_field(doctype)
        fields = [
            "name",
            "company",
            date_field if date_field == "posting_date" else f"{date_field} as posting_date",
            "taxable_amount",
            "non_taxable_amount",
            "vat_amount",
            "summary_grand_total",
            "bill_subtotal",
            "taxable_discount",
            "disable_rounded_total",
        ]
        if doctype != "Sales Order":
            fields.append("is_return")
        start = 0
        while True:
            rows = frappe.get_all(
                doctype,
                filters=_invoice_filters(doctype, from_date, to_date),
                fields=fields,
                limit_start=start,
                limit_page_length=BATCH_SIZE,
                order_by=f"{date_field}, name",
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
    "bill_subtotal",
    "taxable_discount",
)
ROUNDING_IGNORE_LIMIT = 1.0


def _amt(value):
    """Round a money field to 2 decimals, preserving None."""
    return None if value is None else flt(value, 2)


def _abs_diff(old_value, new_value):
    """Absolute difference between money fields, treating None as zero."""
    return abs(flt(old_value) - flt(new_value))


def _figures_changed(old, new, disable_rounded_total=False):
    """Ignore sub-rupee summary noise for either rounded-total setting."""
    changed = any(
        _amt(old.get(field)) != _amt(new.get(field))
        for field in SUMMARY_COMPARE_FIELDS
    )
    if not changed:
        return False
    minor = all(
        _abs_diff(old.get(field), new.get(field)) < ROUNDING_IGNORE_LIMIT
        for field in SUMMARY_COMPARE_FIELDS
    )
    if minor:
        return False
    return True


def _differs(old_value, new_value):
    """A change of a rupee or more; anything smaller is rounding."""
    return _abs_diff(old_value, new_value) >= ROUNDING_IGNORE_LIMIT


def _vat_included_in_rate(doc):
    """Whether the document's VAT row is included in the item rates."""
    vat_account = get_configured_vat_accounts().get(doc.get("company"), {}).get(vat_side(doc.doctype))
    return any(
        tax.get("included_in_print_rate") for tax in doc.get("taxes") or [] if tax.get("account_head") == vat_account
    )


def _classify(row, doc, calculation_check):
    """Tag a document by why its stored summary (``row``) differs from the recomputed ``doc``."""
    tags = []
    if _has_vat_accounting_error(calculation_check):
        tags.append(VAT_ACCOUNTING_ERROR_TAG)
    # fields added after the document was created were never filled
    missing = (
        not flt(row.get("taxable_amount"))
        and not flt(row.get("vat_amount"))
        and bool(flt(doc.get("total_taxes_and_charges")))
    )
    if missing:
        tags.append(BILL_SUMMARY_MISSING_TAG)
    if flt(row.get("taxable_discount")) < 0:
        tags.append(NEGATIVE_DISCOUNT_TAG)
    discount_changed = _differs(row.get("taxable_discount"), doc.get("taxable_discount"))
    if (
        doc.get("ignore_pricing_rule")
        and any(flt(item.get("discount_amount")) > 0 for item in doc.get("items") or [])
        and discount_changed
    ):
        tags.append(PRICE_GAP_TAG)
    if _vat_included_in_rate(doc) and flt(doc.get("discount_amount")) and discount_changed:
        tags.append(DISCOUNT_VAT_TWICE_TAG)
    split_changed = _differs(row.get("taxable_amount"), doc.get("taxable_amount")) or _differs(
        row.get("non_taxable_amount"), doc.get("non_taxable_amount")
    )
    if split_changed and not missing:
        tags.append(TAXABLE_SPLIT_TAG)
    if not tags and _figures_changed(row, doc):
        tags.append(CORRECTED_TAG)
    return tags


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

    figures_changed = _figures_changed(
        row,
        doc,
        disable_rounded_total=cint(doc.get("disable_rounded_total")),
    )
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
        "old_bill_subtotal": _amt(row.get("bill_subtotal")),
        "new_bill_subtotal": _amt(doc.get("bill_subtotal")),
        "old_taxable_discount": _amt(row.get("taxable_discount")),
        "new_taxable_discount": _amt(doc.get("taxable_discount")),
        "summary_grand_total": doc.summary_grand_total,
        "item_vat_detail": doc.get("item_vat_detail"),
        "calculation_check": calculation_check,
        "tags": _classify(row, doc, calculation_check),
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
        "sales_order_changed": by_doctype["Sales Order"],
        "batched": scanned > BATCH_SIZE,
        "changes": changes,
        "consider_is_non_taxable_item": bool(consider_is_non_taxable_item),
    }


def _has_vat_accounting_error(calculation_check):
    """True when tax-table VAT disagrees with Taxable × 13%."""
    return bool(calculation_check and calculation_check.get("has_vat_mismatch"))


def _flag_vat_accounting_error(doc, calculation_check):
    """Tag and comment a document whose accounting VAT is wrong."""
    if _has_vat_accounting_error(calculation_check):
        _tag_document(doc, [VAT_ACCOUNTING_ERROR_TAG], calculation_check)


def _tag_document(doc, tags, calculation_check):
    """Add each tag; a VAT accounting error also gets a comment with the figures."""
    for tag in tags:
        doc.add_tag(tag)
    if VAT_ACCOUNTING_ERROR_TAG not in tags:
        return
    doc.add_comment(
        "Comment",
        _(
            "Nepal Compliance: VAT Accounting Error. Expected VAT {0} "
            "(Taxable × 13%) but accounting has {1} (difference {2}). "
            "IRD summary can be correct while GL / tax-table VAT stays wrong."
        ).format(
            flt(calculation_check["expected_vat"], 2),
            flt(calculation_check["recorded_vat"], 2),
            flt(calculation_check["vat_difference"], 2),
        ),
    )


def _flag_invoice(change):
    """Flag a VAT accounting error without rewriting summary fields."""
    doc = frappe.get_doc(change["doctype"], change["name"])
    _flag_vat_accounting_error(doc, change.get("calculation_check") or {})


def _apply_change(change):
    """Write recomputed taxable summary fields, then comment on and tag the document."""
    check = change.get("calculation_check") or {}
    tags = change.get("tags")
    if tags is None:
        tags = [VAT_ACCOUNTING_ERROR_TAG] if _has_vat_accounting_error(check) else []
    values = {
        "taxable_amount": change["new_taxable_amount"],
        "non_taxable_amount": change["new_non_taxable_amount"],
        "vat_amount": change["new_vat_amount"],
        "summary_grand_total": change["summary_grand_total"],
        "item_vat_detail": change["item_vat_detail"],
    }
    for field in ("bill_subtotal", "taxable_discount"):
        if f"new_{field}" in change:
            values[field] = change[f"new_{field}"]
    frappe.db.set_value(change["doctype"], change["name"], values, update_modified=False)
    doc = frappe.get_doc(change["doctype"], change["name"])
    doc.add_comment(
        "Comment",
        _(
            "Nepal Compliance: taxable summary recomputed. "
            "Taxable: {0} → {1}, Non-Taxable: {2} → {3}, "
            "VAT: {4} → {5}, Bill Total: {6} → {7}, "
            "Subtotal: {8} → {9}, Discount: {10} → {11}. Tags: {12}."
        ).format(
            flt(change["old_taxable_amount"], 2),
            flt(change["new_taxable_amount"], 2),
            flt(change["old_non_taxable_amount"], 2),
            flt(change["new_non_taxable_amount"], 2),
            flt(change["old_vat_amount"], 2),
            flt(change["new_vat_amount"], 2),
            flt(change["old_summary_grand_total"], 2),
            flt(change["new_summary_grand_total"], 2),
            flt(change.get("old_bill_subtotal"), 2),
            flt(change.get("new_bill_subtotal"), 2),
            flt(change.get("old_taxable_discount"), 2),
            flt(change.get("new_taxable_discount"), 2),
            ", ".join(_(tag) for tag in tags) or _("none"),
        ),
    )
    _tag_document(doc, tags, check)


def _parse_selected_invoices(selected_invoices):
    """Return validated selected invoice keys from a JSON/list payload."""
    selected = (
        frappe.parse_json(selected_invoices)
        if isinstance(selected_invoices, str)
        else selected_invoices
    )
    if not isinstance(selected, list):
        frappe.throw(_("Selected documents must be a list."))

    keys = set()
    for row in selected:
        if not isinstance(row, dict):
            frappe.throw(_("Each selected document must include a type and name."))
        doctype = row.get("doctype")
        name = row.get("name")
        if doctype not in DOCTYPE_ORDER or not name:
            frappe.throw(_("Invalid selected document: {0} {1}").format(doctype, name))
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
        if status not in ("changed", "warning"):
            stale += 1
            continue
        if _has_vat_accounting_error(change.get("calculation_check")):
            calculation_warnings += 1
        if status == "changed":
            _apply_change(change)
        else:
            _flag_invoice(change)
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
                _("VAT Accounting Error")
                if _has_vat_accounting_error(check)
                else (
                    _("Includes added taxes")
                    if change.get("vat_on_added_taxes")
                    else _("Suggestion")
                ),
                _csv_amount(check.get("expected_vat")),
                _csv_amount(check.get("recorded_vat")),
                _csv_amount(check.get("vat_difference")),
                _("Error") if check.get("has_vat_mismatch") else _("OK"),
                _csv_amount(change.get("old_bill_subtotal")),
                _csv_amount(change.get("new_bill_subtotal")),
                _csv_amount(change.get("old_taxable_discount")),
                _csv_amount(change.get("new_taxable_discount")),
                ", ".join(change.get("tags") or []),
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
