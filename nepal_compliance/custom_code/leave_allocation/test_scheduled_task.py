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


if __name__ == "__main__":
    unittest.main()
