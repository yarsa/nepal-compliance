from datetime import date

from frappe.tests.utils import FrappeTestCase

from nepal_compliance.nepali_date_utils.bs_periods import (
	advance,
	bs_month_end_series,
	end_of,
	next_fiscal_period_end,
)


class TestBsPeriods(FrappeTestCase):
	"""BS month arithmetic and Nepali fiscal period-end alignment."""

	def test_advance_wraps_year(self):
		"""advance moves (year, month) forward across year boundaries."""
		self.assertEqual(advance(2082, 12, 1), (2083, 1))
		self.assertEqual(advance(2082, 3, 12), (2083, 3))
		self.assertEqual(advance(2082, 1, 0), (2082, 1))

	def test_monthly_frequency_keeps_every_month(self):
		"""freq=1 treats every BS month as a fiscal period end."""
		for m in range(1, 13):
			self.assertEqual(next_fiscal_period_end(2082, m, 1), (2082, m))

	def test_quarterly_aligns_to_fiscal_quarter_ends(self):
		"""freq=3 rounds up to Ashwin/Poush/Chaitra/Ashadh ends (FY from 1 Shrawan)."""
		cases = {
			4: (2082, 6),   # Shrawan -> Ashwin end
			6: (2082, 6),   # already on a quarter end
			8: (2082, 9),   # Kartik -> Poush end
			10: (2082, 12), # Magh -> Chaitra end
			1: (2082, 3),   # Baishakh -> Ashadh end (same BS year)
			3: (2082, 3),   # Ashadh is the FY end
		}
		for start, expected in cases.items():
			self.assertEqual(next_fiscal_period_end(2082, start, 3), expected, f"month {start}")

	def test_yearly_aligns_to_ashadh_end(self):
		"""freq=12 always lands on end of Ashadh, rolling forward after it."""
		self.assertEqual(next_fiscal_period_end(2082, 3, 12), (2082, 3))
		self.assertEqual(next_fiscal_period_end(2082, 4, 12), (2083, 3))
		self.assertEqual(next_fiscal_period_end(2082, 10, 12), (2083, 3))

	def test_half_yearly_aligns_to_poush_or_ashadh(self):
		"""freq=6 rounds up to Poush or Ashadh ends."""
		self.assertEqual(next_fiscal_period_end(2082, 4, 6), (2082, 9))
		self.assertEqual(next_fiscal_period_end(2082, 9, 6), (2082, 9))
		self.assertEqual(next_fiscal_period_end(2082, 10, 6), (2083, 3))

	def test_fiscal_series_stays_on_period_ends(self):
		"""Advancing by freq from a fiscal period end stays on period ends."""
		y, m = next_fiscal_period_end(2082, 5, 3)
		series = [(y, m)]
		for _ in range(3):
			y, m = advance(y, m, 3)
			series.append((y, m))
		self.assertEqual(series, [(2082, 6), (2082, 9), (2082, 12), (2083, 3)])

	def test_end_of_matches_known_bs_month_ends(self):
		"""end_of returns the AD date of the last day of the BS month."""
		self.assertEqual(end_of(2082, 3), date(2025, 7, 16))   # Ashadh 2082 (32 days)
		self.assertEqual(end_of(2081, 12), date(2025, 4, 13))  # Chaitra 2081 (31 days)

	def test_bs_month_end_series(self):
		"""The whitelisted series returns consecutive BS month-end AD dates."""
		out = bs_month_end_series("2025-01-15", 3)
		self.assertEqual(
			[(r["key"], r["end_ad"]) for r in out],
			[
				("2081-10", "2025-02-12"),
				("2081-11", "2025-03-13"),
				("2081-12", "2025-04-13"),
			],
		)
