import unittest
from types import SimpleNamespace

from nepal_compliance.nepali_date_utils.nepali_date import (
    ad_to_bs,
    bs_to_ad,
    days_in_bs_month,
)
from nepal_compliance.nepali_date_utils.bs_periods import (
    advance,
    end_of,
    is_fiscal_period_month,
    next_fiscal_period_end,
)
from nepal_compliance.overrides.asset_depreciation_schedule import (
    CustomAssetDepreciationSchedule,
    is_bs_fiscal_period_end,
)


class MockScheduleRow:
    """Mock ERPNext Depreciation Schedule child row."""

    def __init__(self, schedule_date=None, amount=0.0, accum=0.0, journal_entry=None):
        """Initialize mock depreciation row attributes."""
        self.schedule_date = schedule_date
        self.depreciation_amount = amount
        self.accumulated_depreciation_amount = accum
        self.journal_entry = journal_entry

    def get(self, k, default=None):
        """Get attribute value by key with optional fallback default."""
        return getattr(self, k, default)


class MockDocument(SimpleNamespace):
    """Mock ERPNext Document supporting attribute and dict-like get access."""

    def get(self, k, default=None):
        """Get attribute value by key with optional fallback default."""
        return getattr(self, k, default)


class TestBSPeriods(unittest.TestCase):
    """Unit tests for BS period manipulation functions."""

    def test_advance_months(self):
        """Verify advancing Bikram Sambat months across year and month boundaries."""
        self.assertEqual(advance(2083, 4, 1), (2083, 5))
        self.assertEqual(advance(2083, 12, 1), (2084, 1))
        self.assertEqual(advance(2083, 4, 12), (2084, 4))
        self.assertEqual(advance(2083, 4, -1), (2083, 3))
        self.assertEqual(advance(2083, 1, -1), (2082, 12))

    def test_days_in_bs_month(self):
        """Verify day count bounds for BS calendar months."""
        self.assertGreater(days_in_bs_month(2083, 1), 28)
        self.assertLessEqual(days_in_bs_month(2083, 1), 32)
        with self.assertRaises(Exception):
            days_in_bs_month(2083, 13)

    def test_end_of(self):
        """Verify end_of helper returns Gregorian date of last day of BS month."""
        end_d = end_of(2083, 4)
        bs_end = ad_to_bs(end_d)
        self.assertEqual(bs_end["year"], 2083)
        self.assertEqual(bs_end["month"], 4)
        self.assertEqual(bs_end["day"], days_in_bs_month(2083, 4))

    def test_next_fiscal_period_end(self):
        """Verify calculation of next Nepali fiscal period end for different frequencies."""
        # Monthly frequency (1) -> every month closes
        self.assertEqual(next_fiscal_period_end(2083, 4, 1), (2083, 4))
        # Quarterly frequency (3) -> closes at Ashwin (6), Poush (9), Chaitra (12), Ashadh (3)
        self.assertEqual(next_fiscal_period_end(2083, 4, 3), (2083, 6))
        # Yearly frequency (12) -> closes at Ashadh (3)
        self.assertEqual(next_fiscal_period_end(2083, 4, 12), (2084, 3))

    def test_is_fiscal_period_month(self):
        """Verify check whether a BS month closes an Ashadh-anchored fiscal period."""
        self.assertTrue(is_fiscal_period_month(2083, 3, 12))
        self.assertTrue(is_fiscal_period_month(2083, 6, 3))
        self.assertFalse(is_fiscal_period_month(2083, 5, 3))


class TestCustomAssetDepreciationSchedule(unittest.TestCase):
    """Unit tests for CustomAssetDepreciationSchedule date snapping and amount recalculation."""

    def _make_ads(self, num_rows=12, opening_accum=0, frequency=1):
        """Create test CustomAssetDepreciationSchedule with empty mock rows."""
        ads = CustomAssetDepreciationSchedule({"doctype": "Asset Depreciation Schedule"})
        ads.depreciation_schedule = [MockScheduleRow() for _ in range(num_rows)]
        ads.opening_accumulated_depreciation = opening_accum
        ads.frequency_of_depreciation = frequency
        return ads

    def test_monthly_depreciation_no_drift_issue_285(self):
        """Verify fix for Issue #285: Monthly schedules stay on consecutive BS month ends without drift."""
        ads = self._make_ads(num_rows=12, frequency=1)
        start_date = bs_to_ad(2083, 4, 1)
        asset = MockDocument(
            gross_purchase_amount=120000,
            available_for_use_date=start_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=1,
            total_number_of_depreciations=12,
            value_after_depreciation=120000,
            expected_value_after_useful_life=0,
            depreciation_start_date=start_date,
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs_month_end(asset)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        expected_periods = [
            (2083, 4), (2083, 5), (2083, 6), (2083, 7),
            (2083, 8), (2083, 9), (2083, 10), (2083, 11),
            (2083, 12), (2084, 1), (2084, 2), (2084, 3),
        ]
        for idx, expected_period in enumerate(expected_periods):
            schedule_row = ads.depreciation_schedule[idx]
            bs_date = ad_to_bs(schedule_row.schedule_date)
            self.assertEqual(
                (bs_date["year"], bs_date["month"]),
                expected_period,
                f"Row {idx+1} period drifted from expected BS period",
            )
            self.assertEqual(
                bs_date["day"],
                days_in_bs_month(bs_date["year"], bs_date["month"]),
                f"Row {idx+1} is not on the BS month end",
            )

        # Sum of depreciation amounts must equal gross depreciable amount
        total_amt = sum(r.depreciation_amount for r in ads.depreciation_schedule)
        self.assertAlmostEqual(total_amt, 120000.0, places=2)
        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 120000.0)

    def test_quarterly_depreciation_schedule(self):
        """Verify quarterly depreciation advances every 3 months on fiscal quarter ends."""
        ads = self._make_ads(num_rows=4, frequency=3)
        available_date = bs_to_ad(2083, 4, 1)
        asset = MockDocument(
            gross_purchase_amount=40000,
            available_for_use_date=available_date,
            flags=SimpleNamespace(),
            precision=lambda field: 2,
        )
        row = SimpleNamespace(
            frequency_of_depreciation=3,
            total_number_of_depreciations=4,
            value_after_depreciation=40000,
            expected_value_after_useful_life=0,
            depreciation_start_date=end_of(2083, 6),
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs_month_end(asset)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        expected_quarter_ends = [6, 9, 12, 3]
        for idx, exp_m in enumerate(expected_quarter_ends):
            bs = ad_to_bs(ads.depreciation_schedule[idx].schedule_date)
            self.assertEqual(bs["month"], exp_m)

        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 40000.0)

    def test_yearly_depreciation_calculation_exact(self):
        """Verify yearly depreciation books exact annual amount settled at Ashadh month end."""
        ads = self._make_ads(num_rows=5, frequency=12)
        available_date = bs_to_ad(2083, 4, 1)  # Shrawan 1 (full FY)
        asset = MockDocument(
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
            depreciation_start_date=end_of(2084, 3),
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs_month_end(asset)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        for idx, r in enumerate(ads.depreciation_schedule):
            self.assertEqual(
                r.depreciation_amount,
                20000.0,
                f"Year {idx+1} amount should be 20000, got {r.depreciation_amount}",
            )
        self.assertEqual(ads.depreciation_schedule[-1].accumulated_depreciation_amount, 100000.0)

    def test_yearly_depreciation_mid_year_pro_rata(self):
        """Verify yearly depreciation with mid-year purchase pro-rates the first period."""
        ads = self._make_ads(num_rows=5, frequency=12)
        available_date = bs_to_ad(2083, 7, 15)  # Kartik 15 (mid-year purchase)
        asset = MockDocument(
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
            depreciation_start_date=end_of(2084, 3),
            depreciation_method="Straight Line",
        )

        ads.snap_schedule_dates_to_bs_month_end(asset)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        # First year is pro-rated (less than 20,000)
        self.assertLess(ads.depreciation_schedule[0].depreciation_amount, 20000.0)
        self.assertGreater(ads.depreciation_schedule[0].depreciation_amount, 0.0)
        # Middle years use full period amount
        self.assertEqual(ads.depreciation_schedule[1].depreciation_amount, 20000.0)
        # Total reaches full depreciable gross
        self.assertAlmostEqual(
            ads.depreciation_schedule[-1].accumulated_depreciation_amount, 100000.0, places=2
        )

    def test_preserves_posted_journal_entries(self):
        """Verify posted journal entries are never modified during re-snapping."""
        posted_date = bs_to_ad(2083, 4, 1)
        posted_row = MockScheduleRow(
            schedule_date=posted_date, amount=10000.0, accum=10000.0, journal_entry="ACC-JV-001"
        )
        pending_rows = [MockScheduleRow() for _ in range(3)]
        ads = CustomAssetDepreciationSchedule({"doctype": "Asset Depreciation Schedule"})
        ads.depreciation_schedule = [posted_row, *pending_rows]
        ads.frequency_of_depreciation = 1

        asset = MockDocument(
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

        ads.snap_schedule_dates_to_bs_month_end(asset)
        ads.recalculate_amounts_after_bs_snap(asset, row)

        # Posted row remains untouched
        self.assertEqual(ads.depreciation_schedule[0].schedule_date, posted_date)
        self.assertEqual(ads.depreciation_schedule[0].depreciation_amount, 10000.0)
        self.assertEqual(ads.depreciation_schedule[0].journal_entry, "ACC-JV-001")

        # Pending rows advance cleanly from last posted date
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
        ads.frequency_of_depreciation = 1

        start_date = bs_to_ad(2083, 4, 1)
        asset = MockDocument(
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

        ads.snap_schedule_dates_to_bs_month_end(asset, date_of_disposal=disposal_date)
        ads.recalculate_amounts_after_bs_snap(asset, row, date_of_disposal=disposal_date)

        # Terminal row kept on disposal date
        self.assertEqual(ads.depreciation_schedule[-1].schedule_date, disposal_date)
        self.assertEqual(ads.depreciation_schedule[-1].depreciation_amount, 5000.0)

    def test_is_bs_fiscal_period_end_callable(self):
        """Verify helper function is callable."""
        self.assertTrue(callable(is_bs_fiscal_period_end))


if __name__ == "__main__":
    unittest.main()
