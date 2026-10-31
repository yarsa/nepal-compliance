import unittest
from unittest.mock import patch

import frappe

from nepal_compliance.nepal_compliance.report.purchase_register_ird import (
    purchase_register_ird,
)
from nepal_compliance.nepal_compliance.report.purchase_return_register_ird import (
    purchase_return_register_ird,
)


def nepal_supplier_invoice(customs_declaration_number, sign=1):
    return frappe._dict(
        invoice="PINV-1",
        bill_no="SUP-1",
        bill_date=None,
        customs_declaration_number=customs_declaration_number,
        reason=None,
        rounded_total=sign * 1130,
        grand_total=sign * 1130,
        summary_grand_total=sign * 1130,
        posting_date="2026-01-01",
        supplier_name="Customs Office",
        invoice_pan="123456789",
        total=sign * 1000,
        total_tax=sign * 130,
        supplier="SUP-1",
        company="ACME",
        stored_taxable_amount=sign * 1000,
        stored_item_vat_detail=None,
        stored_party_country="Nepal",
        address_country="Nepal",
        supplier_tax_id="123456789",
        is_pan_or_abbreviated_bill=0,
    )


def register_row(report, customs_declaration_number, sign=1):
    """Run *report*.get_data over one Nepal-supplier invoice with Rs 1,000 + 13% VAT."""
    item = frappe._dict(
        parent="PINV-1", item_code="Item", net_amount=sign * 1000, asset_category=None, is_nontaxable_item=0
    )
    with patch.object(report, "report_permission_condition", return_value=""), patch.object(
        report, "use_legacy_ird_report_calculation", return_value=False
    ), patch.object(report, "get_vat_breakup", return_value={}), patch.object(
        report, "resolve_report_vat_source", return_value=({"Item": [13, sign * 130]}, True, {})
    ), patch.object(report, "invoice_ird_total", return_value=sign * 1130), patch.object(
        report.frappe, "get_all", return_value=[item]
    ), patch.object(
        report.frappe.db, "sql", return_value=[nepal_supplier_invoice(customs_declaration_number, sign)]
    ):
        if report is purchase_register_ird:
            with patch.object(report, "resolve_ird_fiscal_year_start", return_value=None):
                return report.get_data({})[0]
        return report.get_data({})[0]


class TestIrdCustomsImport(unittest.TestCase):
    def test_pragyapan_bill_from_nepal_supplier_is_an_import(self):
        for report, sign in ((purchase_register_ird, 1), (purchase_return_register_ird, -1)):
            with self.subTest(report=report.__name__):
                row = register_row(report, "PP-2083-001", sign)
                self.assertEqual(row["taxable_import_non_capital_amount"], 1000)
                self.assertEqual(row["taxable_import_non_capital_tax"], 130)
                self.assertEqual(row["taxable_amount"], 0)
                self.assertEqual(row["customs_declaration_number"], "PP-2083-001")

    def test_nepal_supplier_without_pragyapan_stays_domestic(self):
        for report, sign in ((purchase_register_ird, 1), (purchase_return_register_ird, -1)):
            with self.subTest(report=report.__name__):
                row = register_row(report, "  ", sign)
                self.assertEqual(row["taxable_import_non_capital_amount"], 0)
                self.assertEqual(abs(row["taxable_amount"]), 1000)
                self.assertEqual(row["customs_declaration_number"], "")


if __name__ == "__main__":
    unittest.main()
