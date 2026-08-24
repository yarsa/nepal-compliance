from datetime import timedelta

import frappe
from frappe.utils import cint, getdate

from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs, bs_to_ad


def advance(y, m, n):
    """Move (BS year, BS month) forward by n months."""
    t = (y * 12 + (m - 1)) + n
    return t // 12, (t % 12) + 1


def end_of(y, m):
    """AD date of the last day of BS month y-m.

    Derived as 'first day of next BS month minus one day' rather than probing
    days 32/31/30/29: the app's _validate_bs calls frappe.throw, which would push
    entries into the message log and spray UI toasts even inside a try/except.

    Known limit: end_of(2100, 12) needs BS 2101, outside the CSV, and will throw.
    That is AD 2044 and out of scope.
    """
    ny, nm = advance(y, m, 1)
    return bs_to_ad(ny, nm, 1) - timedelta(days=1)


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
