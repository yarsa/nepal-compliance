import unittest
from datetime import date
from unittest.mock import patch

import frappe

from nepal_compliance.ird_filters import (
	apply_ird_posting_date_filters,
	bs_month_to_ad_range,
	current_bs_month_key,
	invoice_link_fields,
	parse_bs_month,
)


class TestIRDFilters(unittest.TestCase):
	def test_parse_iso_month(self):
		self.assertEqual(parse_bs_month("2083-01"), (2083, 1))
		self.assertEqual(parse_bs_month("2083-1"), (2083, 1))

	def test_parse_named_month(self):
		self.assertEqual(parse_bs_month("Baisakh 2083"), (2083, 1))
		self.assertEqual(parse_bs_month("Baisakh 2083 (Apr 2026)"), (2083, 1))
		self.assertEqual(parse_bs_month("Baishakh 2083"), (2083, 1))
		self.assertEqual(parse_bs_month("भाद्र २०८३"), (2083, 5))
		self.assertEqual(parse_bs_month("भाद्र 2083"), (2083, 5))

	def test_parse_invalid_month(self):
		with self.assertRaises(frappe.ValidationError):
			parse_bs_month("2083-13")
		with self.assertRaises(frappe.ValidationError):
			parse_bs_month("not-a-month")

	def test_baisakh_2083_ad_range(self):
		start, end = bs_month_to_ad_range("2083-01")
		self.assertEqual(start, date(2026, 4, 14))
		self.assertEqual(end, date(2026, 5, 14))

	def test_apply_from_to_overrides_month(self):
		conditions = []
		values = {}
		apply_ird_posting_date_filters(
			{"bs_month": "2083-01", "from_nepali_date": "2020-01-01", "to_nepali_date": "2020-12-31"},
			conditions,
			values,
			"si.posting_date",
		)
		self.assertEqual(conditions, ["si.posting_date BETWEEN %(from)s AND %(to)s"])
		self.assertEqual(values["from"], date(2020, 1, 1))
		self.assertEqual(values["to"], date(2020, 12, 31))

	def test_apply_rejects_reversed_date_range(self):
		with self.assertRaises(frappe.ValidationError):
			apply_ird_posting_date_filters(
				{"from_nepali_date": "2026-05-14", "to_nepali_date": "2026-04-14"},
				[],
				{},
				"si.posting_date",
			)

	def test_apply_bs_month_when_no_dates(self):
		conditions = []
		values = {}
		apply_ird_posting_date_filters(
			{"bs_month": "2083-01"},
			conditions,
			values,
			"si.posting_date",
		)
		self.assertEqual(conditions, ["si.posting_date BETWEEN %(from)s AND %(to)s"])
		self.assertEqual(values["from"], date(2026, 4, 14))
		self.assertEqual(values["to"], date(2026, 5, 14))

	@patch("nepal_compliance.ird_filters.fiscal_year_ad_range")
	def test_apply_fiscal_year_when_dates_and_month_are_empty(self, fiscal_year_ad_range):
		fiscal_year_ad_range.return_value = date(2025, 7, 17), date(2026, 7, 16)
		conditions = []
		values = {}

		apply_ird_posting_date_filters(
			{"fiscal_year": "2082-2083"},
			conditions,
			values,
			"si.posting_date",
		)

		fiscal_year_ad_range.assert_called_once_with("2082-2083")
		self.assertEqual(conditions, ["si.posting_date BETWEEN %(from)s AND %(to)s"])
		self.assertEqual(values["from"], date(2025, 7, 17))
		self.assertEqual(values["to"], date(2026, 7, 16))

	def test_apply_legacy_from_to(self):
		conditions = []
		values = {}
		apply_ird_posting_date_filters(
			{"from_nepali_date": "2026-04-14", "to_nepali_date": "2026-05-14"},
			conditions,
			values,
			"pi.posting_date",
		)
		self.assertEqual(conditions, ["pi.posting_date BETWEEN %(from)s AND %(to)s"])
		self.assertEqual(values["from"], date(2026, 4, 14))
		self.assertEqual(values["to"], date(2026, 5, 14))

	def test_apply_one_sided_date_ranges(self):
		conditions = []
		values = {}
		apply_ird_posting_date_filters(
			{"from_nepali_date": "2026-04-14"},
			conditions,
			values,
			"pi.posting_date",
		)
		self.assertEqual(conditions, ["pi.posting_date >= %(from)s"])
		self.assertEqual(values, {"from": date(2026, 4, 14)})

		conditions = []
		values = {}
		apply_ird_posting_date_filters(
			{"to_nepali_date": "2026-05-14"},
			conditions,
			values,
			"pi.posting_date",
		)
		self.assertEqual(conditions, ["pi.posting_date <= %(to)s"])
		self.assertEqual(values, {"to": date(2026, 5, 14)})

	def test_invoice_link_fields(self):
		self.assertEqual(
			invoice_link_fields("Purchase Invoice", "PINV-0001"),
			{"invoice_name": "PINV-0001", "invoice_doctype": "Purchase Invoice"},
		)
		self.assertEqual(invoice_link_fields("Sales Invoice", None), {"invoice_name": "", "invoice_doctype": ""})

	def test_apply_defaults_to_current_bs_month(self):
		conditions = []
		values = {}
		apply_ird_posting_date_filters({}, conditions, values, "si.posting_date")
		start, end = bs_month_to_ad_range(current_bs_month_key())
		self.assertEqual(conditions, ["si.posting_date BETWEEN %(from)s AND %(to)s"])
		self.assertEqual(values["from"], start)
		self.assertEqual(values["to"], end)
