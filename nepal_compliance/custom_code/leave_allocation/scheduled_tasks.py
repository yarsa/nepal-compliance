import frappe
from frappe.utils import getdate
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs
from nepal_compliance.custom_code.leave_allocation.monthly_leave_bs import allocate_monthly_leave_bs

def run_daily_bs_tasks():
    try:
        today_ad = getdate()
        bs = ad_to_bs(today_ad)

        settings = frappe.get_single("Nepal Compliance Settings")
        settings.db_set("bs_year", bs["year"], update_modified=False)
        settings.db_set("bs_month", bs["month"], update_modified=False)
        settings.db_set("bs_day", bs["day"], update_modified=False)

        frappe.logger().info(
            f"[BS] Updated to {bs['year']}-{bs['month']}-{bs['day']}"
        )

        if bs["day"] == 1:
            leave_types = frappe.get_all(
                "Leave Type",
                filters={"allocate_leave_on_start_of_bs_month": 1},
                pluck="name",
            )

            if leave_types:
                allocate_monthly_leave_bs(
                    bs_year=bs["year"],
                    bs_month=bs["month"],
                    leave_types=leave_types,
                    force=False,
                    silent=True,
                )

    except Exception:
        frappe.log_error(
            title="Daily BS Tasks Failed",
            message=frappe.get_traceback()
        )