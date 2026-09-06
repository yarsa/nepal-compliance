import frappe
from frappe.utils import getdate
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs
from nepal_compliance.custom_code.leave_allocation.monthly_leave_bs import allocate_monthly_leave_bs

def run_daily_bs_tasks():
    try:
        today_ad = getdate()
        bs = ad_to_bs(today_ad)

        # Allocate the monthly leave before the stored BS date is refreshed.
        # allocate_monthly_leave_bs decides whether a month has already been
        # processed by comparing the requested month against bs_year and
        # bs_month in Nepal Compliance Settings, so if those are updated first
        # the current month always looks done and the allocation is skipped.
        allocation_failed = False
        if bs["day"] == 1:
            leave_types = frappe.get_all(
                "Leave Type",
                filters={"allocate_leave_on_start_of_bs_month": 1},
                pluck="name",
            )

            if leave_types:
                result = allocate_monthly_leave_bs(
                    bs_year=bs["year"],
                    bs_month=bs["month"],
                    leave_types=leave_types,
                    force=False,
                    silent=True,
                )
                if result and result.get("status") == "error":
                    allocation_failed = True

        settings = frappe.get_single("Nepal Compliance Settings")
        settings.db_set("bs_day", bs["day"], update_modified=False)

        # bs_year and bs_month double as the marker for the last processed month,
        # so only advance them when the allocation did not fail. Advancing them
        # after a failed run would mark the month done and stop it being retried.
        if not allocation_failed:
            settings.db_set("bs_year", bs["year"], update_modified=False)
            settings.db_set("bs_month", bs["month"], update_modified=False)

        frappe.logger().info(
            f"[BS] Updated to {bs['year']}-{bs['month']}-{bs['day']}"
        )

    except Exception:
        frappe.log_error(
            title="Daily BS Tasks Failed",
            message=frappe.get_traceback()
        )