import unittest
from types import SimpleNamespace
from datetime import date, datetime
from frappe.exceptions import ValidationError
import frappe

# Import your class
from nepal_compliance.custom_code.holiday_list.holiday_list import HolidayList_Nepali_Date

# Mock frappe.throw to raise ValidationError
frappe.throw = lambda msg: (_ for _ in ()).throw(ValidationError(msg))

# Pure Python subclass for testing
class TestableHolidayList(HolidayList_Nepali_Date):
    def __init__(self):
        self.holidays = []
        self.total_holidays = 0
        self.weekly_off = None
        self.nepali_from_date = None
        self.nepali_to_date = None

    # Mock Frappe's append method
    def append(self, key, val):
        # Ensure holiday_date is always string (like Frappe DocType)
        if isinstance(val.get("holiday_date"), date):
            val["holiday_date"] = val["holiday_date"].isoformat()
        self.holidays.append(SimpleNamespace(**val))

# Unit Tests
class TestHolidayListNepaliDate(unittest.TestCase):

    def setUp(self):
        self.doc = TestableHolidayList()
        self.doc.weekly_off = "Sunday"
        self.doc.nepali_from_date = "2080-01-01"
        self.doc.nepali_to_date = "2080-01-30"

    # validate() sets total_holidays
    def test_validate_sets_total_holidays(self):
        self.doc.append("holidays", {
            "description": "Test Holiday",
            "holiday_date": "2024-01-01"
        })
        self.doc.validate()
        self.assertEqual(self.doc.total_holidays, 1)

    # sort_holidays() sorts and sets idx
    def test_sort_holidays(self):
        self.doc.append("holidays", {
            "description": "Holiday 2",
            "holiday_date": "2024-01-05"
        })
        self.doc.append("holidays", {
            "description": "Holiday 1",
            "holiday_date": "2024-01-01"
        })
        self.doc.sort_holidays()
        self.assertEqual(self.doc.holidays[0].holiday_date, "2024-01-01")
        self.assertEqual(self.doc.holidays[0].idx, 1)
        self.assertEqual(self.doc.holidays[1].idx, 2)

    # get_holidays() returns list of date objects
    def test_get_holidays(self):
        self.doc.append("holidays", {
            "description": "Holiday",
            "holiday_date": "2024-01-01"
        })
        holidays = self.doc.get_holidays()
        self.assertEqual(holidays, [date(2024, 1, 1)])

    # get_weekly_off_dates() raises error if weekly_off not set
    def test_get_weekly_off_without_selection(self):
        self.doc.weekly_off = None
        with self.assertRaises(ValidationError):
            self.doc.get_weekly_off_dates()

    # get_weekly_off_dates() adds new holiday
    def test_get_weekly_off_adds_dates(self):
        # Mock weekly off generator returns a date object
        self.doc.get_weekly_off_date_list = lambda f, t: [date(2024, 1, 7)]
        self.doc.get_weekly_off_dates()
        # holiday_date should be stored as string
        self.assertEqual(len(self.doc.holidays), 1)
        self.assertEqual(self.doc.holidays[0].weekly_off, 1)
        self.assertEqual(self.doc.holidays[0].holiday_date, "2024-01-07")

    # get_weekly_off_dates() does not duplicate existing holidays
    def test_weekly_off_not_duplicated(self):
        self.doc.append("holidays", {
            "description": "Existing Holiday",
            "holiday_date": "2024-01-07"
        })
        self.doc.get_weekly_off_date_list = lambda f, t: [date(2024, 1, 7)]
        self.doc.get_weekly_off_dates()
        # Should not add duplicate
        self.assertEqual(len(self.doc.holidays), 1)


if __name__ == "__main__":
    unittest.main()
