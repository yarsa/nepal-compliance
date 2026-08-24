import frappe

from erpnext.assets.doctype.asset_depreciation_schedule.asset_depreciation_schedule import (
    AssetDepreciationSchedule,
)

from nepal_compliance.nepali_date_utils.bs_periods import (
    advance,
    end_of,
    next_fiscal_period_end,
)
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs


class CustomAssetDepreciationSchedule(AssetDepreciationSchedule):
    """Snap ERPNext's generated depreciation rows onto BS fiscal period ends.

    ERPNext computes the schedule on Gregorian month boundaries. We let it do all
    the amount/pro-rata work, then move only schedule_date so each row falls on a
    BS period end for the chosen frequency: every BS month end for monthly, and
    Nepali fiscal year (1 Shrawan start) quarter/half/year ends for longer
    frequencies — e.g. yearly rows always land on end of Ashadh.
    """

    def make_depr_schedule(self, *args, **kwargs):
        """Build the schedule via ERPNext, then re-snap dates to BS period ends."""
        super().make_depr_schedule(*args, **kwargs)
        self.snap_schedule_dates_to_bs_month_end()

    def snap_schedule_dates_to_bs_month_end(self):
        """Move pending rows onto consecutive BS fiscal period ends.

        Posted rows (with a journal entry) keep their historical dates. The first
        pending row is anchored at the next fiscal period end on or after its
        computed month; each later row advances by exactly frequency_of_depreciation
        months, which keeps it on fiscal period ends.
        """
        rows = self.get("depreciation_schedule") or []
        if not rows:
            return

        posted = [r for r in rows if r.get("journal_entry")]
        pending = [r for r in rows if not r.get("journal_entry")]
        if not pending:
            return

        freq = frappe.utils.cint(self.get("frequency_of_depreciation")) or 1

        # Continue from the BS month after the last posted row; otherwise start
        # from the BS month of the first pending row.
        if posted:
            anchor, skip = posted[-1].schedule_date, freq
        else:
            anchor, skip = pending[0].schedule_date, 0

        bs = ad_to_bs(frappe.utils.getdate(anchor))
        y, m = advance(bs["year"], bs["month"], skip)
        y, m = next_fiscal_period_end(y, m, freq)

        for row in pending:
            row.schedule_date = end_of(y, m)
            y, m = advance(y, m, freq)
