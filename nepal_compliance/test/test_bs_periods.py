import unittest

from nepal_compliance.nepali_date_utils.bs_periods import (
    is_fiscal_period_month,
    next_fiscal_period_end,
)
from nepal_compliance.overrides.asset_depreciation_schedule import (
    is_bs_fiscal_period_end,
)


class TestBSFiscalPeriods(unittest.TestCase):
    def test_standard_fiscal_period_end_months(self):
        self.assertTrue(is_fiscal_period_month(2083, 3, 12))
        self.assertTrue(is_fiscal_period_month(2083, 6, 3))
        self.assertFalse(is_fiscal_period_month(2083, 5, 3))

    def test_next_period_end_uses_same_anchor(self):
        self.assertEqual(next_fiscal_period_end(2083, 4, 3), (2083, 6))
        self.assertEqual(next_fiscal_period_end(2083, 12, 6), (2084, 3))

    def test_asset_override_imports_period_helper(self):
        self.assertTrue(callable(is_bs_fiscal_period_end))


if __name__ == "__main__":
    unittest.main()
