from frappe.utils import add_days, cint, flt, getdate

from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
    AssetDepreciationSchedule,
    _get_pro_rata_amt,
)

from nepal_compliance.nepali_date_utils.bs_periods import (
    advance,
    end_of,
    next_fiscal_period_end,
)
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs


def bs_aligned_depreciation_start(available_for_use_date, depreciation_start_date, frequency):
    """Next BS fiscal period end on or after the later of use-date and start-date."""
    afu = getdate(available_for_use_date)
    anchor = getdate(depreciation_start_date or available_for_use_date)
    if anchor < afu:
        anchor = afu

    freq = max(cint(frequency), 1)
    bs = ad_to_bs(anchor)
    y, m = next_fiscal_period_end(bs["year"], bs["month"], freq)
    return end_of(y, m)


def resolve_bs_snap_anchor(posted, pending, available_for_use_date, frequency, opening_booked=0):
    """Return (anchor_ad_date, skip_months) for snapping pending schedule rows.

    Posted JE rows continue from the last posted date. Migrated assets with
    opening_number_of_booked_depreciations but no journal_entry yet must skip
    those opening periods instead of re-anchoring at available_for_use_date.
    """
    freq = max(cint(frequency), 1)
    opening = cint(opening_booked)

    if posted:
        return posted[-1].schedule_date, freq
    if opening and available_for_use_date:
        return available_for_use_date, opening * freq
    if available_for_use_date:
        return available_for_use_date, 0
    return pending[0].schedule_date, 0


class CustomAssetDepreciationSchedule(AssetDepreciationSchedule):
    """Snap ERPNext depreciation rows onto BS fiscal period ends and fix amounts.

    Before ERPNext builds the schedule, depreciation_start_date is forced to the
    next Nepali fiscal period end after available_for_use (for the chosen
    frequency). That stops a stale yearly Ashadh start from skipping earlier
    half-year / quarter ends. After generation we still snap pending dates onto
    consecutive BS period ends and recompute Straight Line / Manual amounts.
    """

    def make_depr_schedule(
        self,
        asset_doc,
        row,
        date_of_disposal=None,
        update_asset_finance_book_row=True,
        value_after_depreciation=None,
    ):
        self.align_depreciation_start_to_bs_period_end(asset_doc, row)
        super().make_depr_schedule(
            asset_doc,
            row,
            date_of_disposal=date_of_disposal,
            update_asset_finance_book_row=update_asset_finance_book_row,
            value_after_depreciation=value_after_depreciation,
        )
        self.snap_schedule_dates_to_bs_month_end(asset_doc)
        self.recalculate_amounts_after_bs_snap(asset_doc, row)
        self.sync_finance_book_start_to_first_pending(
            row, update_asset_finance_book_row=update_asset_finance_book_row
        )

    def align_depreciation_start_to_bs_period_end(self, asset_doc, row):
        """Set finance-book start to the next BS period end after available-for-use.

        Ignores a stale depreciation_start_date when nothing is booked yet, so
        changing frequency (e.g. yearly → half-yearly) re-anchors correctly.
        With opening booked depreciations, the existing start is only rounded
        forward to a BS period end.
        """
        if not asset_doc or not row or not asset_doc.available_for_use_date:
            return

        freq = row.get("frequency_of_depreciation")
        opening = cint(self.get("opening_number_of_booked_depreciations")) or cint(
            asset_doc.get("opening_number_of_booked_depreciations")
        )

        if opening:
            anchor_start = row.get("depreciation_start_date") or asset_doc.available_for_use_date
        else:
            # Fresh schedule: always first period end on/after put-to-use
            anchor_start = asset_doc.available_for_use_date

        aligned = bs_aligned_depreciation_start(
            asset_doc.available_for_use_date,
            anchor_start,
            freq,
        )
        if getdate(row.depreciation_start_date) != aligned:
            row.depreciation_start_date = aligned

    def snap_schedule_dates_to_bs_month_end(self, asset_doc=None):
        """Move pending rows onto consecutive BS fiscal period ends.

        Posted rows (with a journal entry) keep their historical dates. With no
        posted rows, the series starts at the next fiscal period end on or after
        available_for_use (not ERPNext's first Gregorian date), unless opening
        booked depreciations require skipping those periods first. Later rows
        advance by frequency_of_depreciation months.
        """
        rows = self.get("depreciation_schedule") or []
        if not rows:
            return

        posted = [r for r in rows if r.get("journal_entry")]
        pending = [r for r in rows if not r.get("journal_entry")]
        if not pending:
            return

        freq = cint(self.get("frequency_of_depreciation")) or 1
        opening = cint(self.get("opening_number_of_booked_depreciations")) or cint(
            (asset_doc or {}).get("opening_number_of_booked_depreciations")
        )
        available = asset_doc.get("available_for_use_date") if asset_doc else None

        anchor, skip = resolve_bs_snap_anchor(
            posted, pending, available, freq, opening_booked=opening
        )

        bs = ad_to_bs(getdate(anchor))
        y, m = advance(bs["year"], bs["month"], skip)
        y, m = next_fiscal_period_end(y, m, freq)

        for schedule_row in pending:
            schedule_row.schedule_date = end_of(y, m)
            y, m = advance(y, m, freq)

    def recalculate_amounts_after_bs_snap(self, asset_doc, row):
        """Rebuild SL/Manual amounts from BS-snapped dates.

        First pending row is pro-rated from the period start through its snapped
        schedule_date (capped at one full period); middle rows use the full
        period amount; the last pending row takes the residual so accumulated
        depreciation hits salvage.
        """
        if not asset_doc or not row:
            return
        if row.depreciation_method not in ("Straight Line", "Manual"):
            return
        if cint(row.get("daily_prorata_based")) or cint(row.get("shift_based")):
            return

        rows = self.get("depreciation_schedule") or []
        pending = [r for r in rows if not r.get("journal_entry")]
        if not pending:
            return

        precision = asset_doc.precision("gross_purchase_amount")
        full_amt = (
            flt(asset_doc.gross_purchase_amount) - flt(row.expected_value_after_useful_life)
        ) / flt(row.total_number_of_depreciations)

        freq = cint(row.get("frequency_of_depreciation")) or cint(
            self.get("frequency_of_depreciation")
        ) or 1
        opening = cint(self.get("opening_number_of_booked_depreciations")) or cint(
            asset_doc.get("opening_number_of_booked_depreciations")
        )

        posted = [r for r in rows if r.get("journal_entry")]
        if posted:
            accum = flt(posted[-1].accumulated_depreciation_amount)
            period_from = add_days(getdate(posted[-1].schedule_date), 1)
        elif opening:
            # First pending period begins the day after the last opening period end
            accum = flt(self.opening_accumulated_depreciation)
            first_bs = ad_to_bs(getdate(pending[0].schedule_date))
            prev_y, prev_m = advance(first_bs["year"], first_bs["month"], -freq)
            period_from = add_days(end_of(prev_y, prev_m), 1)
        else:
            accum = flt(self.opening_accumulated_depreciation)
            period_from = getdate(asset_doc.available_for_use_date)

        target_total = flt(asset_doc.gross_purchase_amount) - flt(
            row.expected_value_after_useful_life
        )

        for idx, schedule_row in enumerate(pending):
            is_last = idx == len(pending) - 1
            if idx == 0:
                amount, _days, _months = _get_pro_rata_amt(
                    row, full_amt, period_from, schedule_row.schedule_date
                )
                # Never charge more than one frequency period in the first row
                amount = flt(min(amount, full_amt), precision)
            elif is_last:
                amount = flt(target_total - accum, precision)
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

    def sync_finance_book_start_to_first_pending(self, row, update_asset_finance_book_row=True):
        """Persist the first pending BS period end as depreciation_start_date."""
        if not update_asset_finance_book_row or not row:
            return

        rows = self.get("depreciation_schedule") or []
        if not rows or any(r.get("journal_entry") for r in rows):
            return

        first_date = getdate(rows[0].schedule_date)
        if getdate(row.depreciation_start_date) == first_date:
            return

        row.depreciation_start_date = first_date
        if row.get("name"):
            row.db_update()
