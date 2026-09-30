import unittest

import frappe

from nepal_compliance.nepali_date_utils.bs_periods import end_of
from nepal_compliance.nepali_date_utils.nepali_date import bs_to_ad
from nepal_compliance.overrides.asset_depreciation_schedule import (
    CustomAssetDepreciationSchedule,
    bs_has_pro_rata,
    life_end_date,
)


class FakeAsset(frappe._dict):
    def precision(self, fieldname):
        return 2


class FakeSchedule(frappe._dict):
    add_missing_bs_pro_rata_stub = CustomAssetDepreciationSchedule.add_missing_bs_pro_rata_stub
    snap_schedule_dates_to_bs_month_end = (
        CustomAssetDepreciationSchedule.snap_schedule_dates_to_bs_month_end
    )
    recalculate_amounts_after_bs_snap = CustomAssetDepreciationSchedule.recalculate_amounts_after_bs_snap
    _recalculates_bs_amounts = CustomAssetDepreciationSchedule._recalculates_bs_amounts
    _cap_pending_rows_at_disposal = CustomAssetDepreciationSchedule._cap_pending_rows_at_disposal

    def add_depr_schedule_row(self, schedule_date, depreciation_amount, schedule_idx):
        self.depreciation_schedule.append(
            frappe._dict(schedule_date=schedule_date, depreciation_amount=depreciation_amount)
        )


def make_yearly(available_for_use_date, rows=5):
    """Five-year straight-line schedule as ERPNext builds it without a stub."""
    fb_row = frappe._dict(
        depreciation_method="Straight Line",
        frequency_of_depreciation=12,
        total_number_of_depreciations=5,
        expected_value_after_useful_life=0,
    )
    asset = FakeAsset(available_for_use_date=available_for_use_date, gross_purchase_amount=100000)
    schedule = FakeSchedule(
        frequency_of_depreciation=12,
        total_number_of_depreciations=5,
        opening_accumulated_depreciation=0,
        depreciation_schedule=[
            frappe._dict(schedule_date=end_of(2083 + i, 3), depreciation_amount=20000)
            for i in range(rows)
        ],
    )
    return schedule, asset, fb_row


class TestBSProRataStub(unittest.TestCase):
    def test_yearly_pro_rata_uses_bs_fiscal_year_start(self):
        self.assertFalse(bs_has_pro_rata(bs_to_ad(2082, 4, 1), 12))
        for day in (2, 10, 16, 17, 29):
            self.assertTrue(bs_has_pro_rata(bs_to_ad(2082, 4, day), 12), day)

    def test_quarterly_pro_rata_uses_bs_quarter_start(self):
        self.assertFalse(bs_has_pro_rata(bs_to_ad(2082, 7, 1), 3))
        self.assertTrue(bs_has_pro_rata(bs_to_ad(2082, 4, 10), 3))

    def test_shrawan_10_gets_final_stub_row(self):
        afu = bs_to_ad(2082, 4, 10)
        schedule, asset, fb_row = make_yearly(afu)
        schedule.add_missing_bs_pro_rata_stub(asset, fb_row)
        schedule.snap_schedule_dates_to_bs_month_end(asset)
        schedule.recalculate_amounts_after_bs_snap(asset, fb_row)

        rows = schedule.depreciation_schedule
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1].schedule_date, life_end_date(afu, 5, 12))
        self.assertEqual([r.schedule_date for r in rows[:5]], [end_of(2083 + i, 3) for i in range(5)])
        self.assertEqual(rows[0].depreciation_amount, 19506.85)
        self.assertEqual([r.depreciation_amount for r in rows[1:5]], [20000] * 4)
        self.assertEqual(rows[-1].depreciation_amount, 493.15)
        self.assertEqual(rows[-1].accumulated_depreciation_amount, 100000)

    def test_shrawan_1_keeps_five_full_years(self):
        schedule, asset, fb_row = make_yearly(bs_to_ad(2082, 4, 1))
        schedule.add_missing_bs_pro_rata_stub(asset, fb_row)
        self.assertEqual(len(schedule.depreciation_schedule), 5)

    def test_existing_stub_is_not_duplicated(self):
        schedule, asset, fb_row = make_yearly(bs_to_ad(2082, 4, 17), rows=6)
        schedule.add_missing_bs_pro_rata_stub(asset, fb_row)
        self.assertEqual(len(schedule.depreciation_schedule), 6)

    def test_disposal_does_not_add_stub(self):
        schedule, asset, fb_row = make_yearly(bs_to_ad(2082, 4, 10))
        schedule.add_missing_bs_pro_rata_stub(asset, fb_row, date_of_disposal="2027-01-01")
        self.assertEqual(len(schedule.depreciation_schedule), 5)


if __name__ == "__main__":
    unittest.main()
