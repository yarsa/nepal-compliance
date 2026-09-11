import unittest

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


if __name__ == "__main__":
    unittest.main()
