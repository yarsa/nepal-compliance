import unittest
from unittest.mock import patch, MagicMock
from datetime import date

# Import the function to test
from nepal_compliance.custom_code.leave_allocation.scheduled_tasks import run_daily_bs_tasks


class TestRunDailyBSTasks(unittest.TestCase):

    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.frappe")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.ad_to_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.allocate_monthly_leave_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.getdate")
    def test_daily_task_updates_settings_and_allocates_leave(
        self, mock_getdate, mock_allocate_leave, mock_ad_to_bs, mock_frappe
    ):
        """
        Test that the daily task:
        - Converts AD to BS
        - Updates Nepal Compliance Settings
        - Allocates leave if day=1
        """
        # Set up mock returns
        today_ad = date(2024, 1, 1)
        mock_getdate.return_value = today_ad

        # BS date for the AD date
        mock_ad_to_bs.return_value = {"year": 2080, "month": 1, "day": 1}

        # Mock settings
        settings_mock = MagicMock()
        mock_frappe.get_single.return_value = settings_mock

        # Mock leave types
        mock_frappe.get_all.return_value = ["Casual Leave", "Sick Leave"]

        # Mock logger
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        # Run the function
        run_daily_bs_tasks()

        # Assertions
        # Settings updated
        settings_mock.db_set.assert_any_call("bs_year", 2080, update_modified=False)
        settings_mock.db_set.assert_any_call("bs_month", 1, update_modified=False)
        settings_mock.db_set.assert_any_call("bs_day", 1, update_modified=False)

        # Logger called
        mock_logger.info.assert_called_once_with("[BS] Updated to 2080-1-1")

        # Allocate monthly leave called with correct arguments
        mock_allocate_leave.assert_called_once_with(
            bs_year=2080,
            bs_month=1,
            leave_types=["Casual Leave", "Sick Leave"],
            force=False,
            silent=True
        )

    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.frappe")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.ad_to_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.allocate_monthly_leave_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.getdate")
    def test_no_leave_allocation_if_day_not_1(
        self, mock_getdate, mock_allocate_leave, mock_ad_to_bs, mock_frappe
    ):
        """Leave allocation should not happen if BS day != 1"""
        mock_getdate.return_value = date(2024, 1, 2)
        mock_ad_to_bs.return_value = {"year": 2080, "month": 1, "day": 2}

        settings_mock = MagicMock()
        mock_frappe.get_single.return_value = settings_mock

        mock_frappe.get_all.return_value = ["Casual Leave"]

        run_daily_bs_tasks()

        # db_set should still run
        settings_mock.db_set.assert_any_call("bs_year", 2080, update_modified=False)
        settings_mock.db_set.assert_any_call("bs_month", 1, update_modified=False)
        settings_mock.db_set.assert_any_call("bs_day", 2, update_modified=False)

        # allocate_monthly_leave_bs should NOT be called
        mock_allocate_leave.assert_not_called()

    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.frappe")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.ad_to_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.allocate_monthly_leave_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.getdate")
    def test_leave_allocated_before_bs_date_is_refreshed(
        self, mock_getdate, mock_allocate_leave, mock_ad_to_bs, mock_frappe
    ):
        """Leave must be allocated before bs_year and bs_month are refreshed.

        allocate_monthly_leave_bs treats a match between the requested month and
        the stored bs_year and bs_month as a sign that the month is already
        done. Refreshing those fields first would make every run look done and
        the allocation would silently never happen.
        """
        mock_getdate.return_value = date(2024, 1, 1)
        mock_ad_to_bs.return_value = {"year": 2080, "month": 1, "day": 1}

        settings_mock = MagicMock()
        mock_frappe.get_single.return_value = settings_mock
        mock_frappe.get_all.return_value = ["Casual Leave"]

        manager = MagicMock()
        manager.attach_mock(mock_allocate_leave, "allocate")
        manager.attach_mock(settings_mock.db_set, "db_set")

        run_daily_bs_tasks()

        names = [call[0] for call in manager.mock_calls]
        self.assertIn("allocate", names)
        allocate_index = names.index("allocate")
        watermark_indices = [
            i
            for i, call in enumerate(manager.mock_calls)
            if call[0] == "db_set" and call[1] and call[1][0] in ("bs_year", "bs_month")
        ]
        self.assertTrue(watermark_indices)
        self.assertTrue(
            all(allocate_index < i for i in watermark_indices),
            "allocation must run before bs_year and bs_month are updated",
        )

    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.frappe")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.ad_to_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.allocate_monthly_leave_bs")
    @patch("nepal_compliance.custom_code.leave_allocation.scheduled_tasks.getdate")
    def test_bs_month_not_advanced_when_allocation_fails(
        self, mock_getdate, mock_allocate_leave, mock_ad_to_bs, mock_frappe
    ):
        """A failed allocation must not advance the bs_year and bs_month marker.

        The allocation rolls back on failure, so if the marker were advanced the
        month would look done and never be retried. bs_day is display only and
        still updates.
        """
        mock_getdate.return_value = date(2024, 1, 1)
        mock_ad_to_bs.return_value = {"year": 2080, "month": 1, "day": 1}

        settings_mock = MagicMock()
        mock_frappe.get_single.return_value = settings_mock
        mock_frappe.get_all.return_value = ["Casual Leave"]
        mock_allocate_leave.return_value = {"status": "error", "error": "boom"}

        run_daily_bs_tasks()

        written_fields = [call[0][0] for call in settings_mock.db_set.call_args_list]
        self.assertIn("bs_day", written_fields)
        self.assertNotIn("bs_year", written_fields)
        self.assertNotIn("bs_month", written_fields)


if __name__ == "__main__":
    unittest.main()
