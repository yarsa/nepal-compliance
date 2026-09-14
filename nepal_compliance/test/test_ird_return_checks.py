import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import ird_return_checks


class TestIrdReturnChecks(unittest.TestCase):
    def setUp(self):
        self.source = frappe._dict(
            name="SINV-1",
            customer="CUST-1",
            company="ACME",
            currency="NPR",
            conversion_rate=1,
        )
        self.note = frappe._dict(
            name="CN-1",
            customer="CUST-1",
            company="ACME",
            currency="NPR",
            conversion_rate=1,
            taxable_amount=-400,
            non_taxable_amount=0,
            vat_amount=-52,
            summary_grand_total=-452,
        )
        self.source_item = frappe._dict(
            name="SOURCE-ROW",
            parent="SINV-1",
            item_code="Item",
            uom="Nos",
            qty=10,
            rate=100,
            net_rate=100,
            net_amount=1000,
            item_tax_template="Nepal Tax",
        )
        self.note_item = frappe._dict(
            name="RETURN-ROW",
            parent="CN-1",
            item_code="Item",
            uom="Nos",
            qty=-4,
            rate=100,
            net_rate=100,
            net_amount=-400,
            item_tax_template="Nepal Tax",
            sales_invoice_item="SOURCE-ROW",
        )

    def test_valid_partial_credit_note_matches(self):
        differences = ird_return_checks._compare_pair(
            "Sales Invoice",
            self.note,
            self.source,
            {"SINV-1": [self.source_item], "CN-1": [self.note_item]},
            "sales_invoice_item",
            {("SINV-1", "SOURCE-ROW"): 130, ("CN-1", "RETURN-ROW"): -52},
        )

        self.assertEqual(differences, [])

    def test_rate_and_proportional_total_mismatch_are_reported(self):
        self.note_item.rate = 110
        self.note.summary_grand_total = -500

        differences = ird_return_checks._compare_pair(
            "Sales Invoice",
            self.note,
            self.source,
            {"SINV-1": [self.source_item], "CN-1": [self.note_item]},
            "sales_invoice_item",
            {("SINV-1", "SOURCE-ROW"): 130, ("CN-1", "RETURN-ROW"): -52},
        )

        self.assertTrue(any("Rate differs" in text for text in differences))
        self.assertTrue(any("Summary Grand Total" in text for text in differences))

    def test_unlinked_item_is_reported(self):
        self.note_item.sales_invoice_item = None

        differences = ird_return_checks._compare_pair(
            "Sales Invoice",
            self.note,
            self.source,
            {"SINV-1": [self.source_item], "CN-1": [self.note_item]},
            "sales_invoice_item",
            {},
        )

        self.assertTrue(any("not linked" in text for text in differences))

    @patch("nepal_compliance.ird_return_checks.frappe.get_all", return_value=[])
    def test_manual_items_load_item_name_for_vat_allocation(self, get_all):
        ird_return_checks._items("Sales Invoice", ["SINV-1"])

        self.assertIn("item_name", get_all.call_args.kwargs["fields"])

    def test_unconfigured_vat_skips_treatment_and_totals(self):
        differences = ird_return_checks._compare_pair(
            "Sales Invoice",
            self.note,
            self.source,
            {"SINV-1": [self.source_item], "CN-1": [self.note_item]},
            "sales_invoice_item",
            {},
            {"SINV-1": False, "CN-1": False},
        )

        self.assertEqual(differences, [])

    def test_configured_empty_vat_still_checks_totals(self):
        differences = ird_return_checks._compare_pair(
            "Sales Invoice",
            self.note,
            self.source,
            {"SINV-1": [self.source_item], "CN-1": [self.note_item]},
            "sales_invoice_item",
            {},
            {"SINV-1": True, "CN-1": True},
        )

        self.assertTrue(any("not proportional" in text for text in differences))

    def test_item_vat_preserves_configuration_state(self):
        docs = {
            "SINV-1": frappe._dict(name="SINV-1", company="ACME"),
            "CN-1": frappe._dict(name="CN-1", company="ACME"),
        }
        items = {"SINV-1": [self.source_item], "CN-1": [self.note_item]}
        breakup = {
            "SINV-1": {"item_vat": {"Item": 130}, "total_vat": 130, "configured": False},
            "CN-1": {"item_vat": {}, "total_vat": 0.0, "configured": False},
        }

        with patch(
            "nepal_compliance.ird_return_checks.get_vat_breakup",
            return_value=breakup,
        ):
            item_vat, configured = ird_return_checks._item_vat(
                "Sales Invoice", docs, items
            )

        self.assertFalse(configured["SINV-1"])
        self.assertFalse(configured["CN-1"])
        self.assertIn(("SINV-1", "SOURCE-ROW"), item_vat)


if __name__ == "__main__":
    unittest.main()
