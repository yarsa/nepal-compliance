from typing import Optional
from frappe.utils import add_days, date_diff, flt, getdate

from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
    AssetDepreciationSchedule,
)

from nepal_compliance.nepali_date_utils.bs_periods import (
    advance,
    end_of_bs_month,
)
from nepal_compliance.nepali_date_utils.nepali_date import (
    ad_to_bs,
    bs_to_ad,
    days_in_bs_month,
)


def _cint(v) -> int:
    """Safe integer conversion defaulting to 0 for None or invalid values."""
    if v is None:
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


def _val(obj, key, default=None):
    """Retrieve value from dict-like or namespace object."""
    if hasattr(obj, "get"):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _flag(asset_doc, name: str) -> bool:
    """Read an ERPNext asset flag whether flags is a dict-like or namespace."""
    flags = getattr(asset_doc, "flags", None)
    if flags is None:
        return False
    if hasattr(flags, "get"):
        return bool(flags.get(name))
    return bool(getattr(flags, name, False))


def _is_adjustment_schedule(asset_doc) -> bool:
    """True when ERPNext rebuilds the schedule after repair or value adjustment."""
    return (
        _flag(asset_doc, "decrease_in_asset_value_due_to_value_adjustment")
        or _flag(asset_doc, "increase_in_asset_value_due_to_repair")
        or _flag(asset_doc, "increase_in_asset_life")
    )


class CustomAssetDepreciationSchedule(AssetDepreciationSchedule):
    """Override ERPNext Asset Depreciation Schedule to support Bikram Sambat (B.S.) calendar.

    Aligns depreciation schedules with Nepali calendar intervals (monthly, quarterly,
    half-yearly, yearly), prevents Gregorian day-count drift, and ensures exact
    Straight-Line and pro-rata amount settlement.
    """

    def make_depr_schedule(
        self,
        asset_doc,
        row,
        date_of_disposal=None,
        update_asset_finance_book_row=True,
        value_after_depreciation=None,
    ):
        """Generate asset depreciation schedule and snap dates and amounts to B.S. calendar."""
        super().make_depr_schedule(
            asset_doc,
            row,
            date_of_disposal=date_of_disposal,
            update_asset_finance_book_row=update_asset_finance_book_row,
            value_after_depreciation=value_after_depreciation,
        )
        self.snap_schedule_dates_to_bs(asset_doc, row, date_of_disposal=date_of_disposal)
        self.recalculate_amounts_after_bs_snap(
            asset_doc, row, date_of_disposal=date_of_disposal
        )
        self.sync_finance_book_start_to_first_pending(
            row, update_asset_finance_book_row=update_asset_finance_book_row
        )

    def snap_schedule_dates_to_bs(self, asset_doc, row, date_of_disposal=None):
        """Adjust schedule_date of all pending rows according to Bikram Sambat calendar.

        Preserves posted rows with existing journal entries and keeps terminal
        disposal row on date_of_disposal.
        """
        rows = self.get("depreciation_schedule") or []
        if not rows:
            return

        posted = [r for r in rows if r.get("journal_entry")]
        pending = [r for r in rows if not r.get("journal_entry")]
        if not pending:
            return

        if date_of_disposal and getdate(pending[-1].schedule_date) == getdate(date_of_disposal):
            pending = pending[:-1]
            if not pending:
                return

        freq = _cint(_val(row, "frequency_of_depreciation")) or _cint(
            self.get("frequency_of_depreciation")
        ) or 1

        if posted:
            last_ad = getdate(posted[-1].schedule_date)
            last_bs = ad_to_bs(last_ad)
            anchor_y, anchor_m = advance(last_bs["year"], last_bs["month"], freq)
            anchor_day = last_bs["day"]
            is_month_end = anchor_day >= days_in_bs_month(last_bs["year"], last_bs["month"])
        else:
            start_ad = getdate(_val(row, "depreciation_start_date") or asset_doc.available_for_use_date)
            start_bs = ad_to_bs(start_ad)
            anchor_y, anchor_m = start_bs["year"], start_bs["month"]
            anchor_day = start_bs["day"]
            is_month_end = anchor_day >= days_in_bs_month(start_bs["year"], start_bs["month"])

        for idx, sched_row in enumerate(pending):
            y, m = advance(anchor_y, anchor_m, idx * freq)
            if is_month_end:
                day = days_in_bs_month(y, m)
            elif anchor_day == 1:
                day = 1
            else:
                day = min(anchor_day, days_in_bs_month(y, m))
            sched_row.schedule_date = bs_to_ad(y, m, day)

    def recalculate_amounts_after_bs_snap(self, asset_doc, row, date_of_disposal=None):
        """Recompute Straight Line or Manual depreciation amounts for pending rows.

        Ensures full period amount is booked for full periods, accurate pro-ration
        is used for mid-period asset acquisition, and residual settles to salvage.
        """
        if not asset_doc or not row:
            return
        if _val(row, "depreciation_method") not in ("Straight Line", "Manual"):
            return
        if _cint(_val(row, "daily_prorata_based")) or _cint(_val(row, "shift_based")):
            return

        rows = self.get("depreciation_schedule") or []
        pending = [r for r in rows if not r.get("journal_entry")]
        if not pending:
            return

        disposal_row = None
        if date_of_disposal and getdate(pending[-1].schedule_date) == getdate(date_of_disposal):
            disposal_row = pending[-1]
            pending = pending[:-1]
            if not pending:
                return

        precision = asset_doc.precision("gross_purchase_amount") if hasattr(asset_doc, "precision") else 2
        pending_count = len(pending)
        salvage = flt(_val(row, "expected_value_after_useful_life", 0))
        remaining_depreciable = flt(_val(row, "value_after_depreciation", 0)) - salvage

        if _is_adjustment_schedule(asset_doc):
            full_amt = flt(remaining_depreciable / max(pending_count, 1), precision)
        else:
            total_depr = max(_cint(_val(row, "total_number_of_depreciations", 1)), 1)
            full_amt = flt((flt(asset_doc.gross_purchase_amount) - salvage) / total_depr, precision)

        freq = _cint(_val(row, "frequency_of_depreciation")) or _cint(
            self.get("frequency_of_depreciation")
        ) or 1
        posted = [r for r in rows if r.get("journal_entry")]
        if posted:
            accum = flt(posted[-1].accumulated_depreciation_amount)
            period_from = add_days(getdate(posted[-1].schedule_date), 1)
        else:
            accum = flt(self.opening_accumulated_depreciation or 0)
            first_sched_ad = getdate(pending[0].schedule_date)
            first_sched_bs = ad_to_bs(first_sched_ad)
            prev_y, prev_m = advance(first_sched_bs["year"], first_sched_bs["month"], -freq)
            period_from = add_days(end_of_bs_month(prev_y, prev_m), 1)

        available_for_use = getdate(asset_doc.available_for_use_date) if hasattr(asset_doc, "available_for_use_date") and asset_doc.available_for_use_date else period_from
        target_total = flt(accum + remaining_depreciable, precision)

        for idx, schedule_row in enumerate(pending):
            is_last = idx == len(pending) - 1
            settle_residual = is_last and disposal_row is None

            if settle_residual:
                amount = flt(target_total - accum, precision)
            elif idx == 0 and not posted:
                if available_for_use > period_from:
                    first_end = getdate(schedule_row.schedule_date)
                    active_days = date_diff(first_end, available_for_use) + 1
                    total_days = date_diff(first_end, period_from) + 1
                    if total_days > 0 and active_days < total_days:
                        pro_rata = (full_amt * active_days) / total_days
                        amount = flt(min(pro_rata, full_amt), precision)
                    else:
                        amount = flt(full_amt, precision)
                else:
                    amount = flt(full_amt, precision)
            else:
                amount = flt(full_amt, precision)

            remaining = flt(target_total - accum, precision)
            if amount > remaining:
                amount = remaining
            if amount < 0:
                amount = 0

            schedule_row.depreciation_amount = amount
            accum = flt(accum + amount, precision)
            schedule_row.accumulated_depreciation_amount = accum

        if disposal_row is not None:
            remaining = flt(target_total - accum, precision)
            amount = flt(disposal_row.depreciation_amount, precision)
            if amount > remaining:
                amount = remaining
            if amount < 0:
                amount = 0
            disposal_row.depreciation_amount = amount
            disposal_row.accumulated_depreciation_amount = flt(accum + amount, precision)

    def sync_finance_book_start_to_first_pending(self, row, update_asset_finance_book_row=True):
        """Persist first pending schedule date to finance book row if not yet posted."""
        if not update_asset_finance_book_row or not row:
            return

        rows = self.get("depreciation_schedule") or []
        if not rows or any(r.get("journal_entry") for r in rows):
            return

        first_date = getdate(rows[0].schedule_date)
        if getdate(_val(row, "depreciation_start_date")) == first_date:
            return

        row.depreciation_start_date = first_date
        if hasattr(row, "db_update") and _val(row, "name"):
            row.db_update()
