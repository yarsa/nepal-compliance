from __future__ import annotations
import csv, os, threading, re
from datetime import date, datetime, timedelta
from typing import Dict, List, Union

try:
    import frappe
    HAS_FRAPPE = True
    def _to_date(v): return frappe.utils.getdate(v)
    def _to_datetime(v): return frappe.utils.get_datetime(v)
    def _throw(msg): frappe.throw(msg)
    def _log(msg): frappe.log_error(msg)
except Exception:
    HAS_FRAPPE = False
    def _to_date(v): return date.fromisoformat(str(v))
    def _to_datetime(v): return datetime.fromisoformat(str(v))
    class NepaliDateError(Exception): pass
    def _throw(msg): raise NepaliDateError(msg)
    def _log(msg): print("NepaliDateError:", msg)

CALENDAR_FILENAME = "nepali_calendar.csv"
BASE_AD = date(1943, 4, 14)
BASE_BS_YEAR, BASE_BS_MONTH, BASE_BS_DAY = 2000, 1, 1

NEPALI_MONTHS = ["", "बैशाख", "जेठ", "असार", "साउन",
                 "भदौ", "असोज", "कार्तिक", "मंसिर",
                 "पुष", "माघ", "फागुन", "चैत"]

_bs_months: Dict[int, List[int]] = {}
_loaded = False
_lock = threading.Lock()


def _csv_path() -> str:
    if HAS_FRAPPE:
        app_path = frappe.get_app_path("nepal_compliance")
        return os.path.join(app_path, "nepali_date_utils", "data", CALENDAR_FILENAME)
    return os.path.join(os.path.dirname(__file__), "data", CALENDAR_FILENAME)


def load_calendar() -> None:
    global _loaded, _bs_months
    if _loaded:
        return

    with _lock:
        if _loaded:
            return

        path = _csv_path()
        if not os.path.exists(path):
            _throw(f"Calendar CSV missing at: {path}")

        parsed: Dict[int, List[int]] = {}

        try:
            with open(path, encoding="utf-8") as f:
                for row in csv.reader(f):
                    if not row or row[0].startswith("#"):
                        continue
                    if row[0].lower() in ("year", "bs_year"):
                        continue
                    if len(row) != 13:
                        _throw(f"Invalid row: expected 13 columns: {row}")

                    try:
                        year = int(row[0])
                        months = [int(x) for x in row[1:13]]
                    except ValueError as e:
                        _throw(f"Invalid integer in row: {row} ({e})")

                    if any(m <= 0 for m in months):
                        _throw(f"Invalid day count in year {year}: {months}")

                    parsed[year] = months

        except OSError as e:
            _throw(f"Failed to read calendar file {path}: {e}")

        years = sorted(parsed.keys())
        if not years:
            _throw(f"No BS years found in calendar file {path}")
        for i in range(1, len(years)):
            if years[i] != years[i - 1] + 1:
                _throw(f"Missing BS year in calendar: {years[i - 1] + 1}")

        _bs_months = parsed
        _loaded = True


def _ensure_loaded():
    if not _loaded:
        load_calendar()


def _validate_bs(year: int, month: int, day: int):
    _ensure_loaded()
    if year not in _bs_months:
        _throw(f"Year {year} outside supported BS range {min(_bs_months)}–{max(_bs_months)}")
    if not 1 <= month <= 12:
        _throw("Month must be between 1 and 12")
    max_day = _bs_months[year][month - 1]
    if not (1 <= day <= max_day):
        _throw(f"Invalid BS day {day} for {year}-{month} (max {max_day})")


def _d(v):
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    d = _to_date(v)
    if d is None:
        _throw(f"Invalid AD date input: {v}")
    return d


def _dt(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, datetime.min.time())
    dt = _to_datetime(v)
    if dt is None:
        _throw(f"Invalid datetime input: {v}")
    return dt


def ad_to_bs(ad: Union[str, date, datetime]):
    _ensure_loaded()

    ad_date = _d(ad)
    if ad_date < BASE_AD:
        _throw(f"AD date before supported range {BASE_AD}")

    delta = (ad_date - BASE_AD).days
    y, m, d = BASE_BS_YEAR, BASE_BS_MONTH, BASE_BS_DAY

    max_year = max(_bs_months)
    for year in range(BASE_BS_YEAR, max_year + 1):
        days_in_year = sum(_bs_months[year])
        if delta >= days_in_year:
            delta -= days_in_year
            y += 1
        else:
            break

    if delta and y > max_year:
        _throw("Exceeded available BS calendar data.")
    while delta:
        dim = _bs_months[y][m - 1]
        d += 1
        if d > dim:
            d = 1
            m += 1
            if m > 12:
                m = 1
                y += 1
                if y not in _bs_months:
                    _throw("Exceeded available BS calendar data.")
        delta -= 1

    return {"year": y, "month": m, "day": d}


def bs_to_ad(year: int, month: int, day: int) -> date:
    _ensure_loaded()
    _validate_bs(year, month, day)

    ad = BASE_AD

    for y in range(BASE_BS_YEAR, year):
        ad += timedelta(days=sum(_bs_months[y]))

    for m in range(1, month):
        ad += timedelta(days=_bs_months[year][m - 1])

    ad += timedelta(days=day - 1)
    return ad


def _safe_replace(fmt: str, mapping: Dict[str, str]) -> str:

    # Replaces known tokens and support legacy M and D only when used as standalone tokens (e.g. YYYY.M.D, YYYY-M-D).

    # Replace explicit tokens first
    tokens = sorted(mapping, key=len, reverse=True)
    pattern = "|".join(re.escape(t) for t in tokens)
    result = re.sub(pattern, lambda m: mapping[m.group(0)], fmt)

    # Legacy compatibility: standalone M and D
    result = re.sub(r'(?<![A-Za-z])M(?![A-Za-z])', mapping["M_S"], result)
    result = re.sub(r'(?<![A-Za-z])D(?![A-Za-z])', mapping["D_S"], result)

    return result


def format_bs(ad_date, fmt="YYYY-MM-DD"):
    bs = ad_to_bs(ad_date)
    return _safe_replace(fmt, {
        "YYYY": str(bs["year"]),
        "MM": f"{bs['month']:02d}",
        "DD": f"{bs['day']:02d}",
        "M_NP": NEPALI_MONTHS[bs["month"]],
        "M_S": str(bs["month"]),
        "D_S": str(bs["day"]),
        "M_NP": NEPALI_MONTHS[bs["month"]]
    })


def format_bs_datetime(ad_dt, fmt="YYYY-MM-DD HH:mm:SS"):
    dt = _dt(ad_dt)
    bs = ad_to_bs(dt.date())
    return _safe_replace(fmt, {
        "YYYY": str(bs["year"]),
        "MM": f"{bs['month']:02d}",
        "DD": f"{bs['day']:02d}",
        "M_NP": NEPALI_MONTHS[bs["month"]],
        "M_S": str(bs["month"]),
        "D_S": str(bs["day"]),
        "HH": f"{dt.hour:02d}",
        "mm": f"{dt.minute:02d}",
        "SS": f"{dt.second:02d}",
    })

__all__ = ["ad_to_bs", "bs_to_ad", "format_bs", "format_bs_datetime"]