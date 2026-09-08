# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from nepal_compliance.tds_base_scan import (
    _apply,
    _ensure_permission,
    _filters,
    _job_id,
    _resolve_dates,
    _scan,
)

@frappe.whitelist()
def preview_tds_base_backfill(from_date: str | None = None, to_date: str | None = None, fiscal_year: str | None = None):
    _ensure_permission()
    from_date, to_date = _resolve_dates(from_date, to_date, fiscal_year)
    count = frappe.db.count("Purchase Invoice", _filters(from_date, to_date))
    if count > BATCH_SIZE:
        job = enqueue(
            method="nepal_compliance.tds_base_backfill.run_preview",
            queue="long",
            timeout=3600,
            is_async=True,
            job_id=_job_id("preview", from_date, to_date),
            deduplicate=True,
            from_date=str(from_date),
            to_date=str(to_date),
            user=frappe.session.user,
        )
        return {"queued": True, "duplicate": job is None, "scanned": count}
    return {
        "queued": False,
        "from_date": str(from_date),
        "to_date": str(to_date),
        **_scan(from_date, to_date),
    }


@frappe.whitelist(methods=["POST"])
def apply_tds_base_backfill(
    from_date: str | None = None, to_date: str | None = None, fiscal_year: str | None = None, confirmed: int = 0
):
    _ensure_permission()
    if not cint(confirmed):
        frappe.throw(_("Preview and confirm the TDS-base backfill before applying it."))
    from_date, to_date = _resolve_dates(from_date, to_date, fiscal_year)
    count = frappe.db.count("Purchase Invoice", _filters(from_date, to_date))
    if count > BATCH_SIZE:
        job = enqueue(
            method="nepal_compliance.tds_base_backfill.run_apply",
            queue="long",
            timeout=3600,
            is_async=True,
            job_id=_job_id("apply", from_date, to_date),
            deduplicate=True,
            from_date=str(from_date),
            to_date=str(to_date),
            user=frappe.session.user,
        )
        return {"queued": True, "duplicate": job is None, "scanned": count}
    return {"queued": False, "scanned": count, **_apply(from_date, to_date)}


def run_preview(from_date, to_date, user):
    frappe.set_user(user)
    _ensure_permission()
    result = _scan(getdate(from_date), getdate(to_date))
    frappe.publish_realtime(
        "tds_base_backfill_preview_done",
        {"from_date": from_date, "to_date": to_date, **result},
        user=user,
    )
    return result


def run_apply(from_date, to_date, user):
    frappe.set_user(user)
    _ensure_permission()
    result = _apply(getdate(from_date), getdate(to_date))
    frappe.publish_realtime(
        "tds_base_backfill_apply_done",
        {"from_date": from_date, "to_date": to_date, **result},
        user=user,
    )
    return result
