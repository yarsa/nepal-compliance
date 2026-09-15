import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import ird_sequence


class TestIrdSequence(unittest.TestCase):
    def test_missing_ranges_are_compact(self):
        self.assertEqual(
            ird_sequence._missing_ranges([1, 2, 5, 9]),
            [(3, 4), (6, 8)],
        )

    @patch("nepal_compliance.ird_sequence.frappe.db.sql")
    def test_gap_rows_are_grouped_by_company_and_prefix(self, sql):
        sql.return_value = [
            frappe._dict(name="SINV-0001", company="ACME"),
            frappe._dict(name="SINV-0003", company="ACME"),
            frappe._dict(name="RET-0001", company="ACME"),
            frappe._dict(name="RET-0002", company="ACME"),
        ]

        rows = ird_sequence._gap_rows(
            {"from_nepali_date": "2026-01-01", "to_nepali_date": "2026-01-31"},
            False,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].invoice, "Missing: SINV-0002")
        self.assertEqual(rows[0].compliance_error_codes, ["invoice_sequence_gap"])

    @patch("nepal_compliance.ird_sequence._gap_rows")
    @patch("nepal_compliance.ird_sequence.frappe.get_cached_doc")
    def test_disabled_sequence_check_does_not_query(self, settings, gap_rows):
        settings.return_value = frappe._dict(enable_sales_invoice_number_check=0)

        rows = [frappe._dict(invoice="SINV-0001")]
        self.assertIs(ird_sequence.append_sequence_gaps(rows, {}), rows)
        gap_rows.assert_not_called()


if __name__ == "__main__":
    unittest.main()
