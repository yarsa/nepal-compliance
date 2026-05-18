#!/usr/bin/env python3
"""Compare backend and frontend Nepali calendar month-length tables."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path


BACKEND_SOURCE = Path("nepal_compliance/nepali_date_utils/data/nepali_calendar.csv")
BACKEND_RUNTIME = Path("nepal_compliance/nepali_date_utils/nepali_date.py")
FRONTEND_SOURCE = Path("nepal_compliance/public/js/nepali_date_lib.js")
FRONTEND_RUNTIME = Path("nepal_compliance/public/js/nepali_date_override.js")
FRONTEND_DATEPICKER_RUNTIME = Path("nepal_compliance/public/js/report_filter.js")

MONTH_NAMES = [
    "Baisakh",
    "Jestha",
    "Asadh",
    "Shrawan",
    "Bhadra",
    "Asoj",
    "Kartik",
    "Mangsir",
    "Poush",
    "Magh",
    "Falgun",
    "Chaitra",
]


@dataclass(frozen=True)
class CalendarBase:
    bs_year: int
    bs_month: int
    bs_day: int
    ad_date: str


@dataclass(frozen=True)
class MonthMismatch:
    bs_year: int
    bs_month: int
    month_name: str
    backend_days: int
    frontend_days: int
    importance: str
    classification: str


@dataclass(frozen=True)
class YearTotalMismatch:
    bs_year: int
    backend_total_days: int
    frontend_total_days: int
    importance: str


@dataclass(frozen=True)
class ShiftExample:
    bs_date: str
    backend_ad: str
    frontend_ad: str
    delta_days: int
    note: str


def _compact_ranges(years: list[int]) -> list[str]:
    if not years:
        return []
    ranges: list[str] = []
    start = prev = years[0]
    for year in years[1:]:
        if year == prev + 1:
            prev = year
            continue
        ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = year
    ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ranges


def _parse_backend_base() -> CalendarBase:
    text = BACKEND_RUNTIME.read_text(encoding="utf-8")
    ad_match = re.search(r"BASE_AD\s*=\s*date\((\d+),\s*(\d+),\s*(\d+)\)", text)
    bs_match = re.search(
        r"BASE_BS_YEAR,\s*BASE_BS_MONTH,\s*BASE_BS_DAY\s*=\s*(\d+),\s*(\d+),\s*(\d+)",
        text,
    )
    if not ad_match or not bs_match:
        raise ValueError(f"Could not parse backend base constants from {BACKEND_RUNTIME}")
    ad = date(*(int(part) for part in ad_match.groups()))
    bs_year, bs_month, bs_day = (int(part) for part in bs_match.groups())
    return CalendarBase(bs_year=bs_year, bs_month=bs_month, bs_day=bs_day, ad_date=ad.isoformat())


def _parse_frontend_base() -> CalendarBase:
    text = FRONTEND_SOURCE.read_text(encoding="utf-8")
    bs_match = re.search(r"var N = \{ year: (\d+), monthIndex: (\d+), day: (\d+) \}", text)
    ad_match = re.search(r"B = new Date\(Date\.UTC\((\d+),\s*(\d+),\s*(\d+)\)\)", text)
    if not bs_match or not ad_match:
        raise ValueError(f"Could not parse frontend base constants from {FRONTEND_SOURCE}")
    bs_year = int(bs_match.group(1))
    bs_month = int(bs_match.group(2)) + 1
    bs_day = int(bs_match.group(3))
    ad_year = int(ad_match.group(1))
    ad_month = int(ad_match.group(2)) + 1
    ad_day = int(ad_match.group(3))
    return CalendarBase(bs_year=bs_year, bs_month=bs_month, bs_day=bs_day, ad_date=date(ad_year, ad_month, ad_day).isoformat())


def load_backend_calendar() -> dict[int, list[int]]:
    rows: dict[int, list[int]] = {}
    with BACKEND_SOURCE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            year = int(row["Year"])
            rows[year] = [int(row[month]) for month in MONTH_NAMES]
    return rows


def load_frontend_calendar() -> dict[int, list[int]]:
    text = FRONTEND_SOURCE.read_text(encoding="utf-8")
    match = re.search(r"var c = \{(.*?)\}, E = Object\.keys\(c\)", text, flags=re.S)
    if not match:
        raise ValueError(f"Could not find frontend month table in {FRONTEND_SOURCE}")
    rows: dict[int, list[int]] = {}
    for key, value in re.findall(r"([0-9]+(?:e[0-9]+)?): \[([^\]]+)\]", match.group(1)):
        year = int(float(key)) if "e" in key else int(key)
        months = [int(part.strip()) for part in value.split(",")]
        if len(months) != 12:
            raise ValueError(f"Frontend year {year} has {len(months)} month values")
        rows[year] = months
    return rows


def _bs_to_ad(
    table: dict[int, list[int]],
    base: CalendarBase,
    bs_year: int,
    bs_month: int,
    bs_day: int,
) -> date:
    if base.bs_month != 1 or base.bs_day != 1:
        raise ValueError("This comparison script expects first-day BS base constants")
    if bs_year not in table:
        raise ValueError(f"BS year {bs_year} is outside this table")
    if not 1 <= bs_month <= 12:
        raise ValueError(f"Invalid BS month {bs_month}")
    max_day = table[bs_year][bs_month - 1]
    if not 1 <= bs_day <= max_day:
        raise ValueError(f"Invalid BS day {bs_day} for {bs_year}-{bs_month:02d}; max {max_day}")

    ad = date.fromisoformat(base.ad_date)
    for year in range(base.bs_year, bs_year):
        ad += timedelta(days=sum(table[year]))
    for month in range(1, bs_month):
        ad += timedelta(days=table[bs_year][month - 1])
    return ad + timedelta(days=bs_day - 1)


def _classify_month_mismatch(year: int) -> str:
    if year < 2070:
        return "historical"
    return "overlap"


def build_report() -> dict[str, object]:
    backend = load_backend_calendar()
    frontend = load_frontend_calendar()
    backend_base = _parse_backend_base()
    frontend_base = _parse_frontend_base()

    backend_years = sorted(backend)
    frontend_years = sorted(frontend)
    overlap_years = sorted(set(backend_years) & set(frontend_years))
    overlap_min = min(overlap_years) if overlap_years else None
    overlap_max = max(overlap_years) if overlap_years else None

    month_mismatches: list[MonthMismatch] = []
    for year in overlap_years:
        for index, (backend_days, frontend_days) in enumerate(zip(backend[year], frontend[year]), start=1):
            if backend_days == frontend_days:
                continue
            month_mismatches.append(
                MonthMismatch(
                    bs_year=year,
                    bs_month=index,
                    month_name=MONTH_NAMES[index - 1],
                    backend_days=backend_days,
                    frontend_days=frontend_days,
                    importance="high",
                    classification=_classify_month_mismatch(year),
                )
            )

    year_total_mismatches = [
        YearTotalMismatch(
            bs_year=year,
            backend_total_days=sum(backend[year]),
            frontend_total_days=sum(frontend[year]),
            importance="high",
        )
        for year in overlap_years
        if sum(backend[year]) != sum(frontend[year])
    ]

    examples: list[ShiftExample] = []
    example_dates: list[tuple[int, int, int, str]] = []
    for mismatch in month_mismatches:
        next_month = mismatch.bs_month + 1
        next_year = mismatch.bs_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        if next_year in backend and next_year in frontend:
            example_dates.append(
                (
                    next_year,
                    next_month,
                    1,
                    f"first day after {mismatch.bs_year} {mismatch.month_name} mismatch",
                )
            )
    if 2087 in backend and 2087 in frontend:
        example_dates.extend(
            [
                (2088, 1, 1, "overlap example after BS 2087 Mangsir mismatch"),
                (2089, 12, 30, "downstream overlap example after BS 2087 Mangsir mismatch"),
            ]
        )

    seen: set[tuple[int, int, int]] = set()
    for year, month, day, note in example_dates:
        key = (year, month, day)
        if key in seen or year not in backend or year not in frontend:
            continue
        seen.add(key)
        try:
            backend_ad = _bs_to_ad(backend, backend_base, year, month, day)
            frontend_ad = _bs_to_ad(frontend, frontend_base, year, month, day)
        except ValueError:
            continue
        delta = (frontend_ad - backend_ad).days
        if delta:
            examples.append(
                ShiftExample(
                    bs_date=f"{year}-{month:02d}-{day:02d}",
                    backend_ad=backend_ad.isoformat(),
                    frontend_ad=frontend_ad.isoformat(),
                    delta_days=delta,
                    note=note,
                )
            )

    return {
        "backend_calendar_source": str(BACKEND_SOURCE),
        "frontend_calendar_source": str(FRONTEND_SOURCE),
        "backend_runtime_usage": str(BACKEND_RUNTIME),
        "frontend_runtime_usage": [str(FRONTEND_RUNTIME), str(FRONTEND_DATEPICKER_RUNTIME)],
        "backend_base": asdict(backend_base),
        "frontend_base": asdict(frontend_base),
        "backend_bs_range": {"min": min(backend_years), "max": max(backend_years)},
        "frontend_bs_range": {"min": min(frontend_years), "max": max(frontend_years)},
        "overlap_bs_range": {"min": overlap_min, "max": overlap_max},
        "range_differences": {
            "classification": "informational",
            "note": "Different supported ranges may be intentional; this script treats only overlapping month-length/year-total divergence as failing.",
            "backend_only_years": _compact_ranges(sorted(set(backend_years) - set(frontend_years))),
            "frontend_only_years": _compact_ranges(sorted(set(frontend_years) - set(backend_years))),
        },
        "overlapping_month_length_mismatches": [asdict(item) for item in month_mismatches],
        "year_total_mismatches": [asdict(item) for item in year_total_mismatches],
        "shift_examples": [asdict(item) for item in examples],
        "duplicate_source_maintenance": {
            "classification": "maintainability_risk",
            "note": "The backend CSV and frontend JS table are separate committed calendar sources. This script does not infer whether one is generated from the other.",
        },
        "exit_policy": {
            "nonzero_on_overlapping_month_mismatch": True,
            "nonzero_on_year_total_mismatch": True,
            "nonzero_on_range_difference": False,
        },
    }


def _format_report(report: dict[str, object]) -> str:
    backend_range = report["backend_bs_range"]
    frontend_range = report["frontend_bs_range"]
    overlap_range = report["overlap_bs_range"]
    range_diff = report["range_differences"]
    month_mismatches = report["overlapping_month_length_mismatches"]
    year_total_mismatches = report["year_total_mismatches"]
    shift_examples = report["shift_examples"]

    lines = [
        f"Backend calendar source: {report['backend_calendar_source']}",
        f"Frontend calendar source: {report['frontend_calendar_source']}",
        "",
        f"Backend BS range: {backend_range['min']}-{backend_range['max']}",  # type: ignore[index]
        f"Frontend BS range: {frontend_range['min']}-{frontend_range['max']}",  # type: ignore[index]
        "Overlapping BS range: {min}-{max}".format(**overlap_range)  # type: ignore[arg-type]
        if overlap_range["min"] is not None  # type: ignore[index]
        else "Overlapping BS range: none",
        "",
        "Range differences:",
    ]
    backend_only = range_diff["backend_only_years"] or ["none"]  # type: ignore[index]
    frontend_only = range_diff["frontend_only_years"] or ["none"]  # type: ignore[index]
    lines.append(f"- Backend-only years: {', '.join(backend_only)}")
    lines.append(f"- Frontend-only years: {', '.join(frontend_only)}")
    lines.append("- Note: range differences may be intentional and are reported as informational.")
    lines.extend(["", "Overlapping month-length mismatches:"])
    if month_mismatches:
        for item in month_mismatches:  # type: ignore[assignment]
            lines.append(
                "- BS {bs_year} month {bs_month} ({month_name}): backend={backend_days} frontend={frontend_days} "
                "[{classification}]".format(**item)
            )
    else:
        lines.append("- none")
    lines.extend(["", "Year-total mismatches:"])
    if year_total_mismatches:
        for item in year_total_mismatches:  # type: ignore[assignment]
            lines.append(
                "- BS {bs_year}: backend={backend_total_days} frontend={frontend_total_days}".format(**item)
            )
    else:
        lines.append("- none")
    lines.extend(["", "Shift examples:"])
    if shift_examples:
        for item in shift_examples:  # type: ignore[assignment]
            lines.append(
                "- BS {bs_date}: backend AD={backend_ad} frontend AD={frontend_ad} "
                "(delta={delta_days:+d} day) - {note}".format(**item)
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "Runtime usage observations:",
            f"- Backend conversion/formatting code loads the CSV through {report['backend_runtime_usage']}.",
            "- Frontend date conversion/date-picker code uses NepaliDateLib/NepaliCalendarLib from the bundled JS table.",
            "",
            "Exit policy:",
            "- exits 1 when overlapping month-length or year-total mismatches exist",
            "- exits 0 for range differences alone",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON instead of text.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_report(report))

    return 1 if report["overlapping_month_length_mismatches"] or report["year_total_mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
