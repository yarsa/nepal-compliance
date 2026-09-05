# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and Contributors
# See license.txt

import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure frappe module is available for standalone test runners
try:
	import frappe
except ImportError:
	mock_frappe = MagicMock()
	sys.modules["frappe"] = mock_frappe
	sys.modules["frappe.utils"] = MagicMock()
	sys.modules["frappe.utils.data"] = MagicMock()

from nepal_compliance.nepali_num2words import _nepali_in_words, in_words


class TestNepaliInWordsBasic(unittest.TestCase):
	"""
	Unit tests for basic digit conversions in Nepali numbering system:
	zero, single digits (1-9), teens (10-19), and two-digit numbers (20-99).
	"""

	def test_zero(self):
		"""Test that 0 converts to 'Zero'."""
		self.assertEqual(_nepali_in_words(0), "Zero")

	def test_single_digits(self):
		"""Test numbers 1 through 9."""
		expected = {
			1: "One",
			2: "Two",
			3: "Three",
			4: "Four",
			5: "Five",
			6: "Six",
			7: "Seven",
			8: "Eight",
			9: "Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_teens(self):
		"""Test teen numbers 10 through 19."""
		expected = {
			10: "Ten",
			11: "Eleven",
			12: "Twelve",
			13: "Thirteen",
			14: "Fourteen",
			15: "Fifteen",
			16: "Sixteen",
			17: "Seventeen",
			18: "Eighteen",
			19: "Nineteen",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_multiples_of_ten(self):
		"""Test exact multiples of 10 from 20 to 90."""
		expected = {
			20: "Twenty",
			30: "Thirty",
			40: "Forty",
			50: "Fifty",
			60: "Sixty",
			70: "Seventy",
			80: "Eighty",
			90: "Ninety",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_two_digit_combinations(self):
		"""Test compound two-digit numbers."""
		expected = {
			21: "Twenty One",
			35: "Thirty Five",
			42: "Forty Two",
			58: "Fifty Eight",
			67: "Sixty Seven",
			73: "Seventy Three",
			84: "Eighty Four",
			99: "Ninety Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)


class TestNepaliInWordsHundredsAndThousands(unittest.TestCase):
	"""
	Unit tests for hundreds (10^2) and thousands (10^3) place values.
	"""

	def test_exact_hundreds(self):
		"""Test exact multiples of 100."""
		expected = {
			100: "One Hundred",
			200: "Two Hundred",
			500: "Five Hundred",
			900: "Nine Hundred",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_hundreds_combinations(self):
		"""Test hundreds with tens and units."""
		expected = {
			101: "One Hundred One",
			115: "One Hundred Fifteen",
			350: "Three Hundred Fifty",
			578: "Five Hundred Seventy Eight",
			999: "Nine Hundred Ninety Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_exact_thousands(self):
		"""Test exact thousands boundaries."""
		expected = {
			1000: "One Thousand",
			5000: "Five Thousand",
			10000: "Ten Thousand",
			50000: "Fifty Thousand",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_thousands_combinations_and_boundary(self):
		"""Test complex thousands and upper boundary before Lakh (99,999)."""
		expected = {
			1001: "One Thousand One",
			1050: "One Thousand Fifty",
			1100: "One Thousand One Hundred",
			1525: "One Thousand Five Hundred Twenty Five",
			15678: "Fifteen Thousand Six Hundred Seventy Eight",
			99999: "Ninety Nine Thousand Nine Hundred Ninety Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)


class TestNepaliInWordsLakhsAndCrores(unittest.TestCase):
	"""
	Unit tests for Lakh (10^5) and Crore (10^7) place values,
	including transition boundaries.
	"""

	def test_exact_lakh(self):
		"""Test exact Lakh boundaries (1,00,000 to 10,00,000)."""
		expected = {
			100000: "One Lakh",
			500000: "Five Lakh",
			1000000: "Ten Lakh",
			5000000: "Fifty Lakh",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_lakh_combinations_and_boundary(self):
		"""Test Lakh combinations and upper boundary before Crore (99,99,999)."""
		expected = {
			100001: "One Lakh One",
			100100: "One Lakh One Hundred",
			101000: "One Lakh One Thousand",
			150000: "One Lakh Fifty Thousand",
			2545678: "Twenty Five Lakh Forty Five Thousand Six Hundred Seventy Eight",
			9999999: "Ninety Nine Lakh Ninety Nine Thousand Nine Hundred Ninety Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_exact_crore(self):
		"""Test exact Crore boundaries (1,00,00,000 to 10,00,00,000)."""
		expected = {
			10000000: "One Crore",
			50000000: "Five Crore",
			100000000: "Ten Crore",
			500000000: "Fifty Crore",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_crore_combinations_and_boundary(self):
		"""Test Crore combinations and upper boundary before Arba (99,99,99,999)."""
		expected = {
			10000001: "One Crore One",
			10050000: "One Crore Fifty Thousand",
			752345678: "Seventy Five Crore Twenty Three Lakh Forty Five Thousand Six Hundred Seventy Eight",
			999999999: "Ninety Nine Crore Ninety Nine Lakh Ninety Nine Thousand Nine Hundred Ninety Nine",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)


class TestNepaliInWordsArbaAndKharba(unittest.TestCase):
	"""
	Unit tests for Arba (10^9) and Kharba (10^11) place values in the Nepali system.
	"""

	def test_exact_arba(self):
		"""Test exact Arba boundaries."""
		expected = {
			1000000000: "One Arba",
			5000000000: "Five Arba",
			10000000000: "Ten Arba",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_arba_combinations_and_boundary(self):
		"""Test Arba combinations and upper boundary before Kharba."""
		expected = {
			1000000005: "One Arba Five",
			2500000000: "Two Arba Fifty Crore",
			99999999999: (
				"Ninety Nine Arba Ninety Nine Crore Ninety Nine Lakh "
				"Ninety Nine Thousand Nine Hundred Ninety Nine"
			),
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_exact_kharba(self):
		"""Test exact Kharba boundaries up to 99 Kharba."""
		expected = {
			100000000000: "One Kharba",
			1000000000000: "Ten Kharba",
			9900000000000: "Ninety Nine Kharba",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)

	def test_kharba_upper_limit(self):
		"""Test maximum supported 99 Kharba number."""
		val = 9999999999999
		expected = (
			"Ninety Nine Kharba Ninety Nine Arba Ninety Nine Crore "
			"Ninety Nine Lakh Ninety Nine Thousand Nine Hundred Ninety Nine"
		)
		self.assertEqual(_nepali_in_words(val), expected)

	def test_beyond_99_kharba_fallback(self):
		"""
		Numbers exceeding 99 Kharba (e.g. 100 Kharba / 10^14) fall back
		to standard num2words English representation.
		"""
		val = 100000000000000
		res = _nepali_in_words(val)
		self.assertEqual(res, "one hundred trillion")


class TestNepaliInWordsNegatives(unittest.TestCase):
	"""
	Unit tests for negative number conversions prefixing 'Minus '.
	"""

	def test_negative_numbers(self):
		"""Test various negative values across scales."""
		expected = {
			-1: "Minus One",
			-25: "Minus Twenty Five",
			-100: "Minus One Hundred",
			-1000: "Minus One Thousand",
			-100000: "Minus One Lakh",
			-10000000: "Minus One Crore",
			-1000000000: "Minus One Arba",
			-100000000000: "Minus One Kharba",
		}
		for num, word in expected.items():
			with self.subTest(num=num):
				self.assertEqual(_nepali_in_words(num), word)


class TestInWordsWrapper(unittest.TestCase):
	"""
	Unit tests for the public in_words function, which overrides Frappe's
	in_words implementation based on currency, country, and mode.
	"""

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_npr_currency(self, mock_get_cached_doc):
		"""When currency is NPR, in_words(..., in_million=False) uses Nepali system."""
		mock_settings = MagicMock()
		mock_settings.currency = "NPR"
		mock_settings.country = "India"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words(100000, in_million=False)
		self.assertEqual(result, "One Lakh")

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_nepal_country(self, mock_get_cached_doc):
		"""When country is Nepal, in_words(..., in_million=False) uses Nepali system."""
		mock_settings = MagicMock()
		mock_settings.currency = "USD"
		mock_settings.country = "Nepal"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words(10000000, in_million=False)
		self.assertEqual(result, "One Crore")

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_decimal_float_input(self, mock_get_cached_doc):
		"""Decimal/float input is safely truncated to int and converted."""
		mock_settings = MagicMock()
		mock_settings.currency = "NPR"
		mock_settings.country = "Nepal"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words(1234.56, in_million=False)
		self.assertEqual(result, "One Thousand Two Hundred Thirty Four")

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_string_input(self, mock_get_cached_doc):
		"""Numeric string input is safely cast to integer and converted."""
		mock_settings = MagicMock()
		mock_settings.currency = "NPR"
		mock_settings.country = "Nepal"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words("500000", in_million=False)
		self.assertEqual(result, "Five Lakh")

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_negative_decimal_input(self, mock_get_cached_doc):
		"""Negative float/decimal input is converted with 'Minus' prefix."""
		mock_settings = MagicMock()
		mock_settings.currency = "NPR"
		mock_settings.country = "Nepal"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words(-25000.75, in_million=False)
		self.assertEqual(result, "Minus Twenty Five Thousand")

	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_non_nepal_defaults_to_indian_locale(self, mock_get_cached_doc):
		"""When currency is not NPR and country is not Nepal, falls back to en_IN."""
		mock_settings = MagicMock()
		mock_settings.currency = "USD"
		mock_settings.country = "United States"
		mock_get_cached_doc.return_value = mock_settings

		result = in_words(100000, in_million=False)
		self.assertIn("lakh", result.lower())

	@patch("nepal_compliance.nepali_num2words.frappe.log_error")
	@patch("nepal_compliance.nepali_num2words.frappe.get_cached_doc")
	def test_in_words_system_settings_exception_handling(self, mock_get_cached_doc, mock_log_error):
		"""If get_cached_doc fails, error is logged and fallback en_IN is used."""
		mock_get_cached_doc.side_effect = RuntimeError("Database connection failure")

		result = in_words(5000, in_million=False)
		mock_log_error.assert_called_once()
		self.assertIn("five thousand", result.lower())

	def test_in_words_in_million_default(self):
		"""When in_million=True (default), uses million format."""
		result = in_words(1000000, in_million=True)
		self.assertIn("million", result.lower())

	@patch("num2words.num2words")
	def test_in_words_fallback_on_unsupported_locale(self, mock_num2words):
		"""
		When num2words raises NotImplementedError for a locale,
		it falls back to 'en'.
		"""
		def side_effect(val, lang="en"):
			if lang != "en":
				raise NotImplementedError("Locale not implemented")
			return "one hundred"

		mock_num2words.side_effect = side_effect
		result = in_words(100, in_million=True)
		self.assertEqual(result, "one hundred")


if __name__ == "__main__":
	unittest.main()
