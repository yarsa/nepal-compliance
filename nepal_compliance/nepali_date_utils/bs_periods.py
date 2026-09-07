from datetime import date
from typing import Tuple, Union

import frappe
from frappe.utils import cint, getdate

from nepal_compliance.nepali_date_utils.nepali_date import (
    ad_to_bs,
    bs_to_ad,
    days_in_bs_month,
)


def advance(year: int, month: int, n: int) -> Tuple[int, int]:
    """Advance (BS year, BS month) forward by n months."""
    t = (year * 12 + (month - 1)) + n
    return t // 12, (t % 12) + 1


def end_of_bs_month(year: int, month: int) -> date:
    """Return the Gregorian AD date of the last day of BS year-month."""
    return bs_to_ad(year, month, days_in_bs_month(year, month))


def start_of_bs_month(year: int, month: int) -> date:
    """Return the Gregorian AD date of the first day (day 1) of BS year-month."""
    return bs_to_ad(year, month, 1)


def is_bs_month_end(ad_date: Union[str, date]) -> bool:
    """True if ad_date corresponds to the last day of its Bikram Sambat month."""
    bs = ad_to_bs(getdate(ad_date))
    return bs["day"] == days_in_bs_month(bs["year"], bs["month"])


def next_fiscal_period_end(year: int, month: int, freq: int) -> Tuple[int, int]:
    """First BS month on or after (year, month) that ends a Nepali fiscal period.

    The Nepali fiscal year runs from 1 Shrawan to end of Ashadh (months 4..3),
    so a month closes a fiscal period exactly when (month - 3) % freq == 0:
    - monthly (1): every month
    - quarterly (3): Ashwin (6), Poush (9), Chaitra (12), Ashadh (3)
    - half-yearly (6): Poush (9), Ashadh (3)
    - yearly (12): Ashadh (3) (Nepali fiscal year end)
    """
    freq = max(cint(freq), 1)
    while (month - 3) % freq != 0:
        year, month = advance(year, month, 1)
    return year, month


@frappe.whitelist()
def bs_month_end_series(start_date: Union[str, date], count: int, skip: int = 0):
    """Return count consecutive BS month-end AD dates starting from start_date."""
    bs = ad_to_bs(getdate(start_date))
    year, month = advance(bs["year"], bs["month"], cint(skip))

    out = []
    for _ in range(cint(count)):
        out.append({"key": f"{year}-{month:02d}", "end_ad": str(end_of_bs_month(year, month))})
        year, month = advance(year, month, 1)
    return out
