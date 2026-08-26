import unittest
from types import SimpleNamespace

from nepal_compliance.overrides.asset_depreciation_schedule import (
    _get_recalc_bases,
    _get_recalc_target_total,
)


def _asset(**overrides):
    defaults = {
        "gross_purchase_amount": 100000,
        "available_for_use_date": "2020-01-01",
        "to_date": "2030-01-01",
        "flags": SimpleNamespace(),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _row(**overrides):
    defaults = {
        "value_after_depreciation": 100000,
        "expected_value_after_useful_life": 0,
        "total_number_of_depreciations": 12,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestRecalcBases(unittest.TestCase):
    def test_fresh_asset_uses_gross_over_total_depreciations(self):
        asset = _asset()
        row = _row()
        full_amt, remaining = _get_recalc_bases(asset, row, pending_count=12, precision=2)
        self.assertEqual(full_amt, 8333.33)
        self.assertEqual(remaining, 100000)

    def test_value_adjustment_uses_current_book_over_pending_count(self):
        asset = _asset(flags=SimpleNamespace(decrease_in_asset_value_due_to_value_adjustment=True))
        row = _row(value_after_depreciation=60000)
        full_amt, remaining = _get_recalc_bases(asset, row, pending_count=4, precision=2)
        self.assertEqual(full_amt, 15000)
        self.assertEqual(remaining, 60000)

    def test_repair_uses_current_book_over_pending_count(self):
        asset = _asset(flags=SimpleNamespace(increase_in_asset_value_due_to_repair=True))
        row = _row(value_after_depreciation=120000)
        full_amt, remaining = _get_recalc_bases(asset, row, pending_count=4, precision=2)
        self.assertEqual(full_amt, 30000)
        self.assertEqual(remaining, 120000)

    def test_life_extension_uses_remaining_days(self):
        asset = _asset(flags=SimpleNamespace(increase_in_asset_life=True))
        row = _row(value_after_depreciation=90000)
        full_amt, remaining = _get_recalc_bases(asset, row, pending_count=3, precision=2)
        self.assertEqual(remaining, 90000)
        self.assertAlmostEqual(full_amt, 9000, places=0)

    def test_target_total_after_write_down_does_not_reach_gross(self):
        row = _row(value_after_depreciation=60000)
        target = _get_recalc_target_total(row, accum_start=20000, precision=2)
        self.assertEqual(target, 80000)


if __name__ == "__main__":
    unittest.main()
