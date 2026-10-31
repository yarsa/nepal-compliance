import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import ird_filters
from nepal_compliance.nepal_compliance.report.purchase_register_ird import (
    purchase_register_ird,
)
from nepal_compliance.nepal_compliance.report.purchase_return_register_ird import (
    purchase_return_register_ird,
)
from nepal_compliance.nepal_compliance.report.purchase_vat_register import (
    purchase_vat_register,
)

COMPANY = "_Test IRD Exclusion Company"
POSTING_DATE = "2026-01-15"
# name -> (is_return, return_against, exclude_from_ird_register)
INVOICES = {
    "_T-IRD-EXCL-CI": (0, None, 1),
    "_T-IRD-EXCL-PP": (0, None, 0),
    "_T-IRD-EXCL-CI-RET": (1, "_T-IRD-EXCL-CI", 0),
    "_T-IRD-EXCL-PP-RET": (1, "_T-IRD-EXCL-PP", 0),
}


class TestIrdPurchaseExclusionCondition(unittest.TestCase):
    def test_no_condition_until_the_column_exists(self):
        with patch.object(ird_filters.frappe.db, "has_column", return_value=False):
            self.assertEqual(ird_filters.ird_purchase_exclusion_condition("pi"), "")

    def test_condition_drops_flagged_invoices_and_their_returns(self):
        with patch.object(ird_filters.frappe.db, "has_column", return_value=True):
            condition = ird_filters.ird_purchase_exclusion_condition("pi")
        self.assertIn("pi.exclude_from_ird_register = 0", condition)
        self.assertIn("ird_excluded.name = pi.return_against", condition)

    @patch.object(purchase_vat_register, "ird_purchase_exclusion_condition", return_value="EXCLUDED")
    @patch.object(purchase_vat_register.frappe.db, "sql", return_value=[])
    def test_purchase_vat_register_applies_the_condition(self, sql, _condition):
        purchase_vat_register.execute(frappe._dict())
        self.assertIn("AND EXCLUDED", sql.call_args.args[0])


class TestIrdPurchaseRegisterExclusion(unittest.TestCase):
    """Run the registers' real SQL over bare invoice rows, rolled back afterwards."""

    def setUp(self):
        if not frappe.db.has_column("Purchase Invoice", "exclude_from_ird_register"):
            self.skipTest("exclude_from_ird_register is not on this site yet")
        frappe.db.savepoint("ird_exclusion")
        for name, (is_return, return_against, excluded) in INVOICES.items():
            frappe.db.sql(
                """INSERT INTO `tabPurchase Invoice`
                (name, docstatus, is_return, return_against, exclude_from_ird_register,
                company, posting_date, creation, modified)
                VALUES (%s, 1, %s, %s, %s, %s, %s, NOW(), NOW())""",
                (name, is_return, return_against, excluded, COMPANY, POSTING_DATE),
            )

    def tearDown(self):
        frappe.db.rollback(save_point="ird_exclusion")

    def _invoice_names(self, report):
        filters = {"company": COMPANY, "from_nepali_date": POSTING_DATE, "to_nepali_date": POSTING_DATE}
        with patch.object(report, "use_legacy_ird_report_calculation", return_value=True), patch.object(
            report, "report_permission_condition", return_value=""
        ):
            if report is purchase_register_ird:
                with patch.object(report, "resolve_ird_fiscal_year_start", return_value=None):
                    rows = report.get_data(filters)
            else:
                rows = report.get_data(filters)
        return {row.get("invoice_name") for row in rows}

    def test_flagged_invoice_is_absent_from_purchase_register(self):
        self.assertEqual(self._invoice_names(purchase_register_ird), {"_T-IRD-EXCL-PP"})

    def test_return_of_flagged_invoice_is_absent_from_return_register(self):
        self.assertEqual(self._invoice_names(purchase_return_register_ird), {"_T-IRD-EXCL-PP-RET"})


if __name__ == "__main__":
    unittest.main()
