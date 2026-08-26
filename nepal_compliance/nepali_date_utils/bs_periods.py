import frappe
from frappe.utils import cint, getdate

from nepal_compliance.nepali_date_utils.nepali_date import (
    ad_to_bs,
    bs_to_ad,
    days_in_bs_month,
)


def advance(y, m, n):
    """Move (BS year, BS month) forward by n months."""
    t = (y * 12 + (m - 1)) + n
    return t // 12, (t % 12) + 1


def end_of(y, m):
    """AD date of the last day of BS month y-m.

    Uses the known length of month y-m from the calendar CSV, so the last
    supported month (e.g. Chaitra 2100) works without needing BS 2101 data.
    """
    return bs_to_ad(y, m, days_in_bs_month(y, m))


def next_fiscal_period_end(y, m, freq):
    """First BS month on or after (y, m) that ends a Nepali fiscal period.

    The Nepali fiscal year runs 1 Shrawan to end of Ashadh (months 4..3), so a
    month closes a fiscal period exactly when (m - 3) % freq == 0:
    monthly (1) -> every month; quarterly (3) -> Ashwin/Poush/Chaitra/Ashadh;
    half-yearly (6) -> Poush/Ashadh; yearly (12) -> Ashadh (FY end).
    """
    freq = max(cint(freq), 1)
    while (m - 3) % freq != 0:
        y, m = advance(y, m, 1)
    return y, m


@frappe.whitelist()
def bs_month_end_series(start_date, count, skip=0):
    """`count` consecutive BS month-end AD dates, starting from the BS month
    containing start_date, advanced by `skip` months."""
    bs = ad_to_bs(getdate(start_date))
    y, m = advance(bs["year"], bs["month"], cint(skip))

    out = []
    for _i in range(cint(count)):
        out.append({"key": "{0}-{1:02d}".format(y, m), "end_ad": str(end_of(y, m))})
        y, m = advance(y, m, 1)
    return out
