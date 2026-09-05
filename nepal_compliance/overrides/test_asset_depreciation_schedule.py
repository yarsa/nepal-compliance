import unittest
from datetime import date, timedelta
from types import SimpleNamespace

from frappe.utils import flt, getdate

from nepal_compliance.nepali_date_utils.nepali_date import (
    ad_to_bs,
    bs_to_ad,
    days_in_bs_month,
)
from nepal_compliance.nepali_date_utils.bs_periods import (
    advance,
    end_of_bs_month,
    is_bs_month_end,
    next_fiscal_period_end,
    start_of_bs_month,
)
from nepal_compliance.overrides.asset_depreciation_schedule import (
    CustomAssetDepreciationSchedule,
    _flag,
    _is_adjustment_schedule,
)


class MockScheduleRow:
    """Mock ERPNext Depreciation Schedule child row."""

    def __init__(self, schedule_date=None, amount=0.0, accum=0.0, journal_entry=None):
        self.schedule_date = schedule_date
        self.depreciation_amount = amount
        self.accumulated_depreciation_amount = accum
        self.journal_entry = journal_entry

    def get(self, k, default=None):
        return getattr(self, k, default)


class TestBSPeriods(unittest.TestCase):
    """Unit tests for BS period manipulation functions."""

    def test_advance_months(self):
        self.assertEqual(advance(2083, 4, 1), (2083, 5))
        self.assertEqual(advance(2083, 12, 1), (2084, 1))
        self.assertEqual(advance(2083, 4, 12), (2084, 4))
        self.assertEqual(advance(2083, 4, -1), (2083, 3))
        self.assertEqual(advance(2083, 1, -1), (2082, 12))

    def test_days_in_bs_month(self):
        self.assertGreater(days_in_bs_month(2083, 1), 28)
        self.assertLessEqual(days_in_bs_month(2083, 1), 32)
        with self.assertRaises(Exception):
            days_in_bs_month(2083, 13)

    def test_end_of_bs_month(self):
        end_d = end_of_bs_month(2083, 4)
        bs_end = ad_to_bs(end_d)
        self.assertEqual(bs_end["year"], 2083)
        self.assertEqual(bs_end["month"], 4)
        self.assertEqual(bs_end["day"], days_in_bs_month(2083, 4))
        self.assertTrue(is_bs_month_end(end_d))

    def test_start_of_bs_month(self):
        start_d = start_of_bs_month(2083, 4)
        bs_start = ad_to_bs(start_d)
        self.assertEqual(bs_start["year"], 2083)
        self.assertEqual(bs_start["month"], 4)
        self.assertEqual(bs_start["day"], 1)

    def test_next_fiscal_period_end(self):
        # Monthly
        self.assertEqual(next_fiscal_period_end(2083, 4, 1), (2083, 4))
        # Quarterly: closes at Ashwin (6), Poush (9), Chaitra (12), Ashadh (3)
        self.assertEqual(next_fiscal_period_end(2083, 4, 3), (2083, 6))
        # Yearly: closes at Ashadh (3)
        self.assertEqual(next_fiscal_period_end(2083, 4, 12), (2084, 3))


class TestCustomAssetDepreciationSchedule(unittest.TestCase):
    """Unit tests for CustomAssetDepreciationSchedule."""

    def _make_ads(self, num_rows=12, opening_accum=0):
        ads = CustomAssetDepreciationSchedule({"doctype": "Asset Depreciation Schedule"})
        ads.depreciation_schedule = [MockScheduleRow() for _ in range(num_rows)]
        ads.opening_accumulated_depreciation = opening_accum
        return ads

    def test_monthly_depreciation_no_drift_issue_285(self):
        """Verify fix for Issue #285: Monthly schedules starting on day 1 must not drift."""
        ads = self._make_ads(num_rows=12)
        start_date = bs_to_ad(2083, 4, 1)
        asset = SimpleNamespace(
            gross_purchase_amount=100000,
            available_for_use_date=start_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=1,
            total_number_of_depreciations=12,
            value_after_depreciation=100000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        expected_months = [
            (2083, 4, 1),
            (2083, 5, 1),
            (2083, 6, 1),
            (2083, 7, 1),
            (2083, 8, 1),
            (2083, 9, 1),
            (2083, 10, 1),
            (2083, 11, 1),
            (2083, 12, 1),
            (2084, 1, 1),
            (2084, 2, 1),
            (2084, 3, 1),
        ]

        for idx, (exp_y, exp_m, exp_d) in enumerate(expected_months):
            bs_date = ad_to_bs(ads.depreciation_schedule[idx].schedule_date)
            self.assertEqual(
                (bs_date["year"], bs_date["month"], bs_date["day"]),
                (exp_y, exp_m, exp_d),
                f"Row {idx+1} drifted from expected BS date",
            )

        # Sum of amounts must equal gross (100,000)
        total_amt = sum(r.depreciation_amount for r in ads.depreciation_schedule)
        self.assertAlmostEqual(total_amt, 100000.0, places=2)
        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 100000.0)

    def test_monthly_depreciation_month_end(self):
        """Monthly schedule starting on month end stays on month end for all rows."""
        ads = self._make_ads(num_rows=6)
        start_date = end_of_bs_month(2083, 4)
        asset = SimpleNamespace(
            gross_purchase_amount=60000,
            available_for_use_date=start_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=1,
            total_number_of_depreciations=6,
            value_after_depreciation=60000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        for r in ads.depreciation_schedule:
            bs = ad_to_bs(r.schedule_date)
            self.assertEqual(bs["day"], days_in_bs_month(bs["year"], bs["month"]))

    def test_yearly_depreciation_calculation_exact(self):
        """Verify yearly depreciation (5 years) books full annual amount without shortfall."""
        ads = self._make_ads(num_rows=5)
        # In Nepali FY, year 1 ends at Ashadh end 2084
        start_date = end_of_bs_month(2084, 3)
        available_date = bs_to_ad(2083, 4, 1)  # Shrawan 1 (full FY)
        asset = SimpleNamespace(
            gross_purchase_amount=100000,
            available_for_use_date=available_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=12,
            total_number_of_depreciations=5,
            value_after_depreciation=100000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        # Full year amount must be exactly 20,000 per year
        for idx, r in enumerate(ads.depreciation_schedule):
            self.assertEqual(
                r.depreciation_amount,
                20000.0,
                f"Year {idx+1} amount should be 20000, got {r.depreciation_amount}",
            )
        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 100000.0)

    def test_yearly_depreciation_mid_year_pro_rata(self):
        """Verify yearly depreciation with mid-year purchase pro-rates first year accurately."""
        ads = self._make_ads(num_rows=5)
        start_date = end_of_bs_month(2084, 3)
        available_date = bs_to_ad(2083, 7, 15)  # Kartik 15 (mid-year purchase)
        asset = SimpleNamespace(
            gross_purchase_amount=100000,
            available_for_use_date=available_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=12,
            total_number_of_depreciations=5,
            value_after_depreciation=100000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        # Year 1 should be pro-rated (< 20000)
        self.assertLess(ads.depreciation_schedule[0].depreciation_amount, 20000.0)
        self.assertGreater(ads.depreciation_schedule[0].depreciation_amount, 0.0)
        # Middle years should be 20000.0
        self.assertEqual(ads.depreciation_schedule[1].depreciation_amount, 20000.0)
        # Total must reach 100,000
        self.assertAlmostEqual(
            ads.depreciation_schedule[-1].accumulated_depreciation_amount, 100000.0, places=2
        )

    def test_quarterly_depreciation_schedule(self):
        """Verify quarterly depreciation advances every 3 months."""
        ads = self._make_ads(num_rows=4)
        start_date = end_of_bs_month(2083, 6)  # Ashwin end
        asset = SimpleNamespace(
            gross_purchase_amount=40000,
            available_for_use_date=bs_to_ad(2083, 4, 1),
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=3,
            total_number_of_depreciations=4,
            value_after_depreciation=40000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        expected_months = [6, 9, 12, 3]
        for idx, exp_m in enumerate(expected_months):
            bs = ad_to_bs(ads.depreciation_schedule[idx].schedule_date)
            self.assertEqual(bs["month"], exp_m)

        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 40000.0)

    def test_preserves_posted_journal_entries(self):
        """Verify posted journal entries are never modified during re-snapping."""
        posted_date = bs_to_ad(2083, 4, 1)
        posted_row = MockScheduleRow(
            schedule_date=posted_date, amount=10000.0, accum=10000.0, journal_entry="ACC-JV-001"
        )
        pending_rows = [MockScheduleRow() for _ in range(3)]
        ads = CustomAssetDepreciationSchedule({"doctype": "Asset Depreciation Schedule"})
        ads.depreciation_schedule = [posted_row] + pending_rows

        asset = SimpleNamespace(
            gross_purchase_amount=40000,
            available_for_use_date=posted_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=1,
            total_number_of_depreciations=4,
            value_after_depreciation=30000,
            expected_value_after_useful_life=0,
            depreciation_start_date=posted_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        # Posted row remains untouched
        self.assertEqual(ads.depreciation_schedule[0].schedule_date, posted_date)
        self.assertEqual(ads.depreciation_schedule[0].depreciation_amount, 10000.0)
        self.assertEqual(ads.depreciation_schedule[0].journal_entry, "ACC-JV-001")

        # Pending rows advance cleanly from row 0
        self.assertEqual(ad_to_bs(ads.depreciation_schedule[1].schedule_date)["month"], 5)
        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 40000.0)

    def test_terminal_disposal_row_preserved(self):
        """Verify disposal row on date_of_disposal is kept and accumulated is updated."""
        disposal_date = bs_to_ad(2083, 6, 15)
        schedules = [
            MockScheduleRow(),
            MockScheduleRow(),
            MockScheduleRow(schedule_date=disposal_date, amount=5000.0),
        ]
        ads = CustomAssetDepreciationSchedule({"doctype": "Asset Depreciation Schedule"})
        ads.depreciation_schedule = schedules
        ads.opening_accumulated_depreciation = 0

        start_date = bs_to_ad(2083, 4, 1)
        asset = SimpleNamespace(
            gross_purchase_amount=30000,
            available_for_use_date=start_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=1,
            total_number_of_depreciations=3,
            value_after_depreciation=30000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs(asset, row, date_of_disposal=disposal_date)
        ads.recalculate_amounts_after_bs_snap(asset, row, date_of_disposal=disposal_date)

        # Terminal row kept on disposal date
        self.assertEqual(ads.depreciation_schedule[-1].schedule_date, disposal_date)
        self.assertEqual(ads.depreciation_schedule[-1].depreciation_amount, 5000.0)


if __name__ == "__main__":
    unittest.main()
