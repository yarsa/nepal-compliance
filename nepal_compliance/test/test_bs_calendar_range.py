import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from nepal_compliance.nepali_date_utils import nepali_date
from nepal_compliance.nepali_date_utils import patch as bs_patch


class TestBSCalendarRange(unittest.TestCase):
    def test_range_ends_on_the_last_day_of_the_calendar(self):
        first, last = nepali_date.bs_calendar_range()
        self.assertEqual(first, nepali_date.BASE_AD)
        self.assertEqual(nepali_date.ad_to_bs(last), {"year": 2100, "month": 12, "day": 30})

    def test_dates_inside_and_outside_the_calendar(self):
        _first, last = nepali_date.bs_calendar_range()
        self.assertTrue(bs_patch._in_bs_calendar(last))
        self.assertTrue(bs_patch._in_bs_calendar(datetime(2026, 10, 5, 9, 30)))
        self.assertTrue(bs_patch._in_bs_calendar("2026-10-05"))
        self.assertFalse(bs_patch._in_bs_calendar(last + timedelta(days=1)))
        self.assertFalse(bs_patch._in_bs_calendar("2099-12-31"))
        self.assertFalse(bs_patch._in_bs_calendar("2099-12-31 00:00:00"))
        self.assertFalse(bs_patch._in_bs_calendar(date(1900, 1, 1)))

    @patch.object(bs_patch, "get_bs_date_format", return_value="YYYY-MM-DD")
    @patch.object(bs_patch, "is_bs_enabled", return_value=True)
    def test_date_past_the_calendar_stays_in_ad_without_a_message(self, _enabled, _fmt):
        # ERPNext's default Item End of Life; converting it used to queue
        # "Exceeded available BS calendar data." on every save
        # the old code caught the error and returned the AD date too, but only after
        # frappe.throw had queued the message, so the check is that it never throws
        with patch.object(nepali_date, "_throw", side_effect=ValueError) as throw:
            self.assertEqual(bs_patch._convert_to_bs_if_date("2099-12-31"), "2099-12-31")
            self.assertEqual(bs_patch._convert_to_bs_if_date(date(2099, 12, 31)), date(2099, 12, 31))
        throw.assert_not_called()

    @patch.object(bs_patch, "get_bs_date_format", return_value="YYYY-MM-DD")
    @patch.object(bs_patch, "is_bs_enabled", return_value=True)
    def test_date_inside_the_calendar_is_still_converted(self, _enabled, _fmt):
        self.assertEqual(bs_patch._convert_to_bs_if_date("2026-10-05"), "2083-06-19")


if __name__ == "__main__":
    unittest.main()
