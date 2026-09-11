import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import ird_checks


class TestIrdChecks(unittest.TestCase):
    def setUp(self):
        self.settings = frappe._dict(
            enable_party_tax_id_check=1,
            enable_vat_amount_check=1,
            enable_total_amount_check=1,
            enable_purchase_attachment_check=1,
            customer_tax_id_rules=[
                frappe._dict(match_by="Type", customer_type="Company")
            ],
            supplier_tax_id_rules=[
                frappe._dict(match_by="Group", supplier_group="Local")
            ],
        )

    def test_nepal_party_requires_nine_digit_tax_id(self):
        context = frappe._dict(
            doctype="Sales Invoice",
            tax_id="12A",
            ird_party_country="Nepal",
        )
        party = frappe._dict(
            customer_type="Company", customer_group="Commercial", tax_id=""
        )

        errors = ird_checks.check_party_tax_id(context, party, self.settings)

        self.assertEqual(errors[0]["code"], "invalid_nepal_tax_id")

    def test_unselected_party_rule_does_not_require_tax_id(self):
        context = frappe._dict(
            doctype="Purchase Invoice", tax_id="", ird_party_country="Nepal"
        )
        party = frappe._dict(
            supplier_type="Company", supplier_group="Foreign", tax_id=""
        )

        self.assertEqual(
            ird_checks.check_party_tax_id(context, party, self.settings), []
        )

    def test_vat_and_total_mismatches_are_separate_errors(self):
        context = frappe._dict(
            taxable_amount=1000,
            non_taxable_amount=100,
            vat_amount=120,
            summary_grand_total=1300,
        )

        errors = ird_checks.check_amounts(context, self.settings)

        self.assertEqual(
            {error["code"] for error in errors}, {"vat_mismatch", "total_mismatch"}
        )

    def test_pan_bill_expects_zero_vat(self):
        context = frappe._dict(
            taxable_amount=0,
            non_taxable_amount=1000,
            vat_amount=0,
            summary_grand_total=1000,
            is_pan_or_abbreviated_bill=1,
        )

        self.assertEqual(ird_checks.check_amounts(context, self.settings), [])

    def test_purchase_attachment_check(self):
        context = frappe._dict(
            doctype="Purchase Invoice", attach_purchase_invoice=None
        )

        errors = ird_checks.check_attachment(context, self.settings)

        self.assertEqual(errors[0]["code"], "missing_purchase_attachment")

    def test_filter_matches_any_selected_error(self):
        rows = [
            frappe._dict(invoice="A", compliance_error_codes=["vat_mismatch"]),
            frappe._dict(invoice="B", compliance_error_codes=["total_mismatch"]),
            frappe._dict(invoice="C", compliance_error_codes=[]),
        ]

        filtered = ird_checks.filter_rows(
            rows, {"error_types": '["vat_mismatch", "missing_tax_id"]'}
        )

        self.assertEqual([row.invoice for row in filtered], ["A"])

    @patch("nepal_compliance.ird_checks.frappe.get_cached_doc")
    @patch("nepal_compliance.ird_checks._parties")
    @patch("nepal_compliance.ird_checks._invoice_contexts")
    def test_decorate_rows_adds_errors_and_filters(
        self, contexts, parties, get_settings
    ):
        contexts.return_value = {
            "SINV-1": frappe._dict(
                name="SINV-1",
                doctype="Sales Invoice",
                customer="CUST-1",
                tax_id="123456789",
                ird_party_country="Nepal",
                taxable_amount=1000,
                non_taxable_amount=0,
                vat_amount=120,
                summary_grand_total=1120,
            )
        }
        parties.return_value = {
            "CUST-1": frappe._dict(
                customer_type="Company", customer_group="Commercial"
            )
        }
        get_settings.return_value = self.settings
        rows = [
            frappe._dict(
                invoice="SINV-1",
                invoice_name="SINV-1",
                invoice_doctype="Sales Invoice",
            )
        ]

        result = ird_checks.decorate_rows(
            rows, "Sales Invoice", {"error_types": ["vat_mismatch"]}
        )

        self.assertEqual(result[0].compliance_error_codes, ["vat_mismatch"])
        self.assertIn("VAT Mismatch", result[0].compliance_checks)


if __name__ == "__main__":
    unittest.main()
