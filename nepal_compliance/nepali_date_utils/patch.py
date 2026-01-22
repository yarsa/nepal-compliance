import frappe
from datetime import date, datetime
import re, threading

from nepal_compliance.nepali_date_utils.nepali_date import (
    format_bs,
    format_bs_datetime,
)

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

_patch_lock = threading.Lock()

# Cache helpers (TTL based)
def is_bs_enabled():
    key = "nepal_compliance:bs_enabled"
    cached = frappe.cache().get_value(key)
    if cached is not None:
        return cached

    try:
        enabled = bool(
            frappe.get_single("Nepal Compliance Settings").enable_nepali_date
        )
        frappe.cache().set_value(key, enabled, expires_in_sec=300)
        return enabled
    except Exception:
        return False


def get_bs_date_format():
    key = "nepal_compliance:date_format"
    cached = frappe.cache().get_value(key)
    if cached is not None:
        return cached

    try:
        fmt = (
            frappe.get_single("Nepal Compliance Settings").date_format
            or "YYYY-MM-DD"
        )
        frappe.cache().set_value(key, fmt, expires_in_sec=300)
        return fmt
    except Exception:
        return "YYYY-MM-DD"

def _convert_to_bs_if_date(value):
    if not value or not is_bs_enabled():
        return value

    fmt = get_bs_date_format()

    try:
        if isinstance(value, datetime):
            return format_bs_datetime(value, f"{fmt} HH:mm:SS")

        if isinstance(value, date):
            return format_bs(value, fmt)

        if isinstance(value, str):
            if DATE_REGEX.match(value):
                return format_bs(value, fmt)
            if DATETIME_REGEX.match(value):
                return format_bs_datetime(value, f"{fmt} HH:mm:SS")

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Nepal Compliance BS conversion failed"
        )

    return value

def apply_runtime_patches():
    with _patch_lock:
        if getattr(frappe.flags, "nepal_compliance_patched", False):
            return

        frappe.flags.nepal_compliance_patched = True

        from frappe.utils import formatdate as _orig_formatdate
        from frappe.utils.xlsxutils import make_xlsx as _orig_make_xlsx
        from frappe.utils.csvutils import to_csv as _orig_to_csv
        from frappe import format_value as _orig_format_value

        def patched_format_value(value, df=None, *args, **kwargs):
            fieldtype = None
            if isinstance(df, dict):
                fieldtype = df.get("fieldtype")
            elif df and hasattr(df, "fieldtype"):
                fieldtype = df.fieldtype

            if fieldtype in ("Date", "Datetime") and is_bs_enabled():
                converted = _convert_to_bs_if_date(value)
                if converted != value:
                    return converted

            return _orig_format_value(value, df, *args, **kwargs)

        def patched_formatdate(value=None, format=None):
            if not is_bs_enabled():
                return _orig_formatdate(value, format)

            if not value:
                return value

            try:
                if format:
                    if isinstance(value, datetime):
                        return format_bs_datetime(value, format)
                    return format_bs(value, format)

                return _convert_to_bs_if_date(value)

            except Exception:
                return _orig_formatdate(value, format)

        def patched_make_xlsx(data, sheet_name, wb=None, column_widths=None):
            if not is_bs_enabled():
                return _orig_make_xlsx(data, sheet_name, wb, column_widths)

            converted = []
            for row in data:
                new_row = []
                for cell in row:
                    val = _convert_to_bs_if_date(cell)

                    if isinstance(val, (date, datetime)):
                        val = str(val)

                    new_row.append(val)
                converted.append(new_row)

            return _orig_make_xlsx(converted, sheet_name, wb, column_widths)

        def patched_to_csv(data):
            if not is_bs_enabled():
                return _orig_to_csv(data)

            return _orig_to_csv(
                [[_convert_to_bs_if_date(c) for c in row] for row in data]
            )

        frappe.format_value = patched_format_value
        frappe.utils.formatdate = patched_formatdate
        frappe.utils.xlsxutils.make_xlsx = patched_make_xlsx
        frappe.utils.csvutils.to_csv = patched_to_csv