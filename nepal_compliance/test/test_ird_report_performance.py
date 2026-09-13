import unittest
from unittest.mock import patch

import frappe

from nepal_compliance.nepal_compliance.report.sales_register_ird import (
    sales_register_ird,
)


class TestIrdReportPerformance(unittest.TestCase):
    @patch.object(sales_register_ird, "use_legacy_ird_report_calculation", return_value=True)
    @patch.object(sales_register_ird.frappe, "get_all", return_value=[])
    @patch.object(sales_register_ird.frappe.db, "sql")
    def test_sales_items_are_loaded_in_one_query(self, sql, get_all, _legacy):
        sql.return_value = [
            frappe._dict(
                invoice=name,
                company="ACME",
                customer="Customer",
                posting_date="2026-01-01",
            )
            for name in ("SINV-1", "SINV-2")
        ]

        sales_register_ird.get_data({})

        get_all.assert_called_once()
        self.assertEqual(
            get_all.call_args.kwargs["filters"],
            {"parent": ["in", ["SINV-1", "SINV-2"]]},
        )


if __name__ == "__main__":
    unittest.main()
