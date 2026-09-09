import hashlib

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from frappe.utils.background_jobs import enqueue

from nepal_compliance.utils import (
    category_calculates_tds_on_taxable_amount,
    get_configured_vat_accounts,
    get_purchase_taxable_tds_base,
    get_purchase_tds_category,
    tax_row_amount,
)


BATCH_SIZE = 500
PREVIEW_TABLE_LIMIT = 100


def _ensure_permission():
    if not frappe.has_permission("Nepal Compliance Settings", "write"):
        frappe.throw(_("Not permitted to audit Nepal TDS bases."), frappe.PermissionError)
    if not frappe.has_permission("Purchase Invoice", "write"):
        frappe.throw(_("Not permitted to update Purchase Invoice."), frappe.PermissionError)


def _resolve_dates(from_date, to_date, fiscal_year=None):
    if fiscal_year:
        dates = frappe.db.get_value(
            "Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True
        )
        if not dates:
            frappe.throw(_("Fiscal Year {0} does not exist.").format(fiscal_year))
        from_date = from_date or dates.year_start_date
        to_date = to_date or dates.year_end_date
    from_date = getdate(from_date) if from_date else None
    to_date = getdate(to_date) if to_date else None
    if not from_date or not to_date:
        frappe.throw(_("From Posting Date and To Posting Date are required."))
    if from_date > to_date:
        frappe.throw(_("From Posting Date cannot be after To Posting Date."))
    return from_date, to_date


def _filters(from_date, to_date):
    return {
        "docstatus": 1,
        "apply_tds": 1,
        "posting_date": ["between", [from_date, to_date]],
    }


def _iter_rows(from_date, to_date):
    start = 0
    while True:
        rows = frappe.get_all(
            "Purchase Invoice",
            filters=_filters(from_date, to_date),
            fields=[
                "name",
                "company",
                "posting_date",
                "tax_withholding_net_total",
                "base_tax_withholding_net_total",
            ],
            order_by="posting_date, name",
            limit_start=start,
            limit_page_length=BATCH_SIZE,
        )
        if not rows:
            return
        yield from rows
        if len(rows) < BATCH_SIZE:
            return
        start += BATCH_SIZE


def _job_id(operation, from_date, to_date):
    user = frappe.session.user or "Guest"
    user_key = hashlib.sha256(user.encode()).hexdigest()[:16]
    return f"nepal-tds-base-{operation}-{user_key}-{from_date}-{to_date}"


def _wrong_historical_vat_ledger(doc):
    accounts = get_configured_vat_accounts().get(doc.company, {})
    purchase_account = accounts.get("purchase")
    sales_account = accounts.get("sales")
    if not sales_account or sales_account == purchase_account:
        return None
    if any(
        tax.get("account_head") == sales_account and abs(tax_row_amount(tax)) > 0.000001
        for tax in doc.get("taxes") or []
    ):
        return sales_account
    return None


def _precision(doc, fieldname):
    return doc.precision(fieldname) if hasattr(doc, "precision") else 2


def _audit_row(row):
    if not frappe.has_permission("Purchase Invoice", "write", doc=row.name):
        return "denied", None, None

    doc = frappe.get_doc("Purchase Invoice", row.name)
    category = get_purchase_tds_category(doc)
    if not category_calculates_tds_on_taxable_amount(category):
        return "option_off", None, doc

    wrong_account = _wrong_historical_vat_ledger(doc)
    if wrong_account:
        return (
            "wrong_ledger",
            {
                "name": row.name,
                "company": row.company,
                "posting_date": str(row.posting_date),
                "wrong_vat_account": wrong_account,
            },
            doc,
        )

    taxable, reason = get_purchase_taxable_tds_base(
        doc, throw_on_unavailable=False
    )
    if reason:
        return (
            "unavailable",
            {
                "name": row.name,
                "company": row.company,
                "posting_date": str(row.posting_date),
                "reason": reason,
            },
            doc,
        )

    corrected = flt(taxable, _precision(doc, "tax_withholding_net_total"))
    corrected_base = flt(
        taxable * flt(doc.get("conversion_rate") or 1),
        _precision(doc, "base_tax_withholding_net_total"),
    )
    old = flt(row.tax_withholding_net_total, _precision(doc, "tax_withholding_net_total"))
    old_base = flt(
        row.base_tax_withholding_net_total,
        _precision(doc, "base_tax_withholding_net_total"),
    )
    if old == corrected and old_base == corrected_base:
        return "unchanged", None, doc

    return (
        "changed",
        {
            "name": row.name,
            "company": row.company,
            "posting_date": str(row.posting_date),
            "old_tax_withholding_net_total": old,
            "new_tax_withholding_net_total": corrected,
            "old_base_tax_withholding_net_total": old_base,
            "new_base_tax_withholding_net_total": corrected_base,
        },
        doc,
    )


def _scan(from_date, to_date):
    result = {
        "scanned": 0,
        "changed": 0,
        "unchanged": 0,
        "option_off": 0,
        "unavailable": 0,
        "wrong_ledger": 0,
        "denied": 0,
        "failed": 0,
        "changes": [],
        "exceptions": [],
    }
    for row in _iter_rows(from_date, to_date):
        result["scanned"] += 1
        try:
            status, detail, _doc = _audit_row(row)
        except Exception:
            result["failed"] += 1
            frappe.log_error(
                title=f"Nepal TDS base preview failed for {row.name}",
                message=frappe.get_traceback(),
            )
            continue
        result[status] += 1
        if status == "changed" and len(result["changes"]) < PREVIEW_TABLE_LIMIT:
            result["changes"].append(detail)
        elif status in ("unavailable", "wrong_ledger") and len(result["exceptions"]) < PREVIEW_TABLE_LIMIT:
            result["exceptions"].append(detail)
    result["hidden_changes"] = max(result["changed"] - len(result["changes"]), 0)
    return result


def _apply(from_date, to_date):
    result = {
        "updated": 0,
        "unchanged": 0,
        "option_off": 0,
        "unavailable": 0,
        "wrong_ledger": 0,
        "denied": 0,
        "failed": 0,
    }
    batch_count = 0
    for row in _iter_rows(from_date, to_date):
        savepoint = "nepal_tds_base_invoice"
        frappe.db.savepoint(savepoint)
        try:
            status, detail, doc = _audit_row(row)
            if status != "changed":
                result[status] += 1
                frappe.db.release_savepoint(savepoint)
                continue
            frappe.db.set_value(
                "Purchase Invoice",
                row.name,
                {
                    "tax_withholding_net_total": detail["new_tax_withholding_net_total"],
                    "base_tax_withholding_net_total": detail[
                        "new_base_tax_withholding_net_total"
                    ],
                },
                update_modified=False,
            )
            doc.add_comment(
                "Comment",
                _(
                    "Nepal Compliance TDS-base backfill: transaction base {0} → {1}; "
                    "company-currency base {2} → {3}. Historical TDS tax, VAT rows, and GL entries were not changed."
                ).format(
                    detail["old_tax_withholding_net_total"],
                    detail["new_tax_withholding_net_total"],
                    detail["old_base_tax_withholding_net_total"],
                    detail["new_base_tax_withholding_net_total"],
                ),
            )
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            result["failed"] += 1
            frappe.log_error(
                title=f"Nepal TDS base apply failed for {row.name}",
                message=frappe.get_traceback(),
            )
            continue
        frappe.db.release_savepoint(savepoint)
        result["updated"] += 1
        batch_count += 1
        if batch_count >= BATCH_SIZE:
            frappe.db.commit()  # nosemgrep
            batch_count = 0
    if batch_count:
        frappe.db.commit()  # nosemgrep
    return result


