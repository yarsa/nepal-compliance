# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

"""Shared posting-date filters for IRD sales and purchase registers."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.utils import cint, getdate

from nepal_compliance.nepali_date_utils.bs_periods import end_of
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs, bs_to_ad

BS_MONTH_NAMES_EN = (
	"Baisakh",
	"Jestha",
	"Ashadh",
	"Shrawan",
	"Bhadra",
	"Ashwin",
	"Kartik",
	"Mangsir",
	"Poush",
	"Magh",
	"Falgun",
	"Chaitra",
)

_MONTH_ALIASES = {
	"baisakh": 1,
	"baishakh": 1,
	"jestha": 2,
	"jeth": 2,
	"ashadh": 3,
	"asadh": 3,
	"ashad": 3,
	"asar": 3,
	"ashar": 3,
	"shrawan": 4,
	"shravan": 4,
	"sawan": 4,
	"saun": 4,
	"bhadra": 5,
	"bhadau": 5,
	"ashwin": 6,
	"aswin": 6,
	"ashoj": 6,
	"asoj": 6,
	"kartik": 7,
	"kattik": 7,
	"mangsir": 8,
	"mangshir": 8,
	"poush": 9,
	"paush": 9,
	"push": 9,
	"magh": 10,
	"falgun": 11,
	"phagun": 11,
	"chaitra": 12,
	"chait": 12,
	"बैशाख": 1,
	"जेष्ठ": 2,
	"जेठ": 2,
	"आषाढ": 3,
	"असार": 3,
	"श्रावण": 4,
	"साउन": 4,
	"भाद्र": 5,
	"भदौ": 5,
	"आश्विन": 6,
	"असोज": 6,
	"कार्तिक": 7,
	"मंसिर": 8,
	"पौष": 9,
	"पुष": 9,
	"माघ": 10,
	"फाल्गुन": 11,
	"फागुन": 11,
	"चैत्र": 12,
	"चैत": 12,
}

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_ISO_MONTH = re.compile(r"^(\d{4})-(\d{1,2})$")


def parse_bs_month(value) -> tuple[int, int]:
	"""Parse a BS month filter value into ``(year, month)``.

	Accepts ``YYYY-MM`` (preferred), English month labels, or Devanagari
	labels and digits, with an optional trailing AD hint.
	"""
	text = _cstr_strip(value).translate(_DEVANAGARI_DIGITS)
	if not text:
		frappe.throw(_("Please select a month."))

	match = _ISO_MONTH.match(text)
	if match:
		year, month = cint(match.group(1)), cint(match.group(2))
		_validate_bs_month(year, month, text)
		return year, month

	parts = text.replace(",", " ").split()
	if len(parts) >= 2:
		month = _MONTH_ALIASES.get(parts[0].lower()) or _MONTH_ALIASES.get(parts[0])
		year = cint(parts[1])
		if month and year:
			_validate_bs_month(year, month, text)
			return year, month

	frappe.throw(_("Invalid month {0}.").format(text))


def bs_month_to_ad_range(value) -> tuple:
	"""Return inclusive AD ``(from_date, to_date)`` for a BS month filter."""
	year, month = parse_bs_month(value)
	return bs_to_ad(year, month, 1), end_of(year, month)


def current_bs_month_key() -> str:
	"""Return the current BS month as ``YYYY-MM``."""
	bs = ad_to_bs(getdate())
	return f"{bs['year']:04d}-{bs['month']:02d}"


def fiscal_year_ad_range(name: str) -> tuple:
	"""Return inclusive AD ``(from_date, to_date)`` for a Fiscal Year."""
	row = frappe.db.get_value(
		"Fiscal Year",
		name,
		["year_start_date", "year_end_date"],
		as_dict=True,
	)
	if not row or not row.year_start_date or not row.year_end_date:
		frappe.throw(_("Fiscal Year {0} not found.").format(name))
	return getdate(row.year_start_date), getdate(row.year_end_date)


def apply_ird_posting_date_filters(filters, conditions, values, date_column: str) -> None:
	"""Restrict *date_column* using from/to, then month, then fiscal year.

	The month and fiscal-year filters fill from/to in the UI, so an explicit
	date range wins when present. Opening a register with no dates defaults to
	the current BS month.
	"""
	filters = filters or {}
	from_date = filters.get("from_nepali_date")
	to_date = filters.get("to_nepali_date")
	bs_month = filters.get("bs_month")
	fiscal_year = filters.get("fiscal_year")

	if from_date and to_date:
		from_date, to_date = getdate(from_date), getdate(to_date)
		if from_date > to_date:
			frappe.throw(_("From Date cannot be after To Date."))
		conditions.append(f"{date_column} BETWEEN %(from)s AND %(to)s")
		values["from"] = from_date
		values["to"] = to_date
		return
	if from_date:
		conditions.append(f"{date_column} >= %(from)s")
		values["from"] = getdate(from_date)
		return
	if to_date:
		conditions.append(f"{date_column} <= %(to)s")
		values["to"] = getdate(to_date)
		return
	if bs_month:
		start, end = bs_month_to_ad_range(bs_month)
		conditions.append(f"{date_column} BETWEEN %(from)s AND %(to)s")
		values["from"] = start
		values["to"] = end
		return
	if fiscal_year:
		start, end = fiscal_year_ad_range(fiscal_year)
		conditions.append(f"{date_column} BETWEEN %(from)s AND %(to)s")
		values["from"] = start
		values["to"] = end
		return

	start, end = bs_month_to_ad_range(current_bs_month_key())
	conditions.append(f"{date_column} BETWEEN %(from)s AND %(to)s")
	values["from"] = start
	values["to"] = end


def invoice_link_fields(doctype: str, name: str | None) -> dict:
	"""Hidden row keys used by the IRD register invoice formatter."""
	if not name:
		return {"invoice_name": "", "invoice_doctype": ""}
	return {"invoice_name": name, "invoice_doctype": doctype}


def _cstr_strip(value) -> str:
	"""Return a stripped string, treating None as empty."""
	if value is None:
		return ""
	return str(value).strip()


def _validate_bs_month(year: int, month: int, original: str) -> None:
	"""Reject month numbers outside 1–12."""
	if year < 2000 or month < 1 or month > 12:
		frappe.throw(_("Invalid month {0}.").format(original))
