import frappe
import re
from nepal_compliance.nepali_date_utils.nepali_date import format_bs, format_bs_datetime
from datetime import date, datetime, time

def nepal_compliance_enabled() -> bool:
    try:
        settings = frappe.get_single("Nepal Compliance Settings")
        return bool(settings.enable_nepali_date)
    except Exception as e:
        frappe.log_error(f"Error checking Nepal Compliance settings: {e}", "Nepal Compliance Settings Check")
        return False

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")

def bs_date(value):

    if not value:
        return value

    try:
        settings = frappe.get_cached_doc("Nepal Compliance Settings")
        if not settings.enable_nepali_date:
            return value
        fmt = settings.default_date_format or "YYYY-MM-DD"
    except Exception:
        return value

    if isinstance(value, datetime):
        return format_bs_datetime(value, f"{fmt} HH:mm:SS")

    if isinstance(value, date):
        return format_bs(value, fmt)

    if isinstance(value, time):
        return value.strftime("%H:%M:%S")

    if isinstance(value, str):
        if DATETIME_RE.match(value):
            return format_bs_datetime(value, f"{fmt} HH:mm:SS")

        if DATE_RE.match(value):
            return format_bs(value, fmt)

        if TIME_RE.match(value):
            return value

    return value