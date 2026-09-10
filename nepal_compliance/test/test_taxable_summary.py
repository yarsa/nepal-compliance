import json
import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import utils


class TestTaxableSummaryCalculation(unittest.TestCase):
    def make_invoice(self, taxable_vat=544.61):
        return frappe._dict(
            doctype="Purchase Invoice",
            company="Yarsa Labs",
            grand_total=32762.94,
            items=[
                frappe._dict(
                    item_code="Taxable",
                    net_amount=4189.33,
                    is_nontaxable_item=0,
                ),
                frappe._dict(
                    item_code="Non-Taxable",
                    net_amount=28029,
                    is_nontaxable_item=1,
                ),
            ],
            taxes=[
                frappe._dict(
                    account_head="VAT Payable",
                    tax_amount_after_discount_amount=taxable_vat,
                    tax_amount=taxable_vat,
                    item_wise_tax_detail=json.dumps(
                        {"Taxable": [13, taxable_vat]}
                    ),
                    add_deduct_tax="Add",
                    is_tax_withholding_account=0,
                )
            ],
        )

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_csv_example_uses_non_taxable_item_flag(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice()

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 4189.33)
        self.assertEqual(invoice.non_taxable_amount, 28029)
        self.assertEqual(invoice.vat_amount, 544.61)
        self.assertEqual(invoice.summary_grand_total, 32762.94)
        self.assertEqual(check["expected_vat"], 544.61)
        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_mismatch_retains_recorded_vat(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice(taxable_vat=500)

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.vat_amount, 500)
        self.assertEqual(check["expected_vat"], 544.61)
        self.assertEqual(check["vat_difference"], -44.61)
        self.assertTrue(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_pan_bill_makes_every_item_non_taxable(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice(taxable_vat=0)
        invoice.is_pan_or_abbreviated_bill = 1

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 0)
        self.assertEqual(invoice.non_taxable_amount, 32218.33)
        self.assertEqual(check["expected_vat"], 0)
        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_purchase_invoice_without_tax_rows_is_fully_non_taxable(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice(taxable_vat=0)
        invoice.taxes = []
        invoice.grand_total = 32218.33

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 0)
        self.assertEqual(invoice.non_taxable_amount, 32218.33)
        self.assertEqual(invoice.vat_amount, 0)
        self.assertEqual(check["expected_vat"], 0)
        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_purchase_invoice_with_zero_vat_is_fully_non_taxable(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice(taxable_vat=0)

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 0)
        self.assertEqual(invoice.non_taxable_amount, 32218.33)
        self.assertEqual(invoice.vat_amount, 0)
        self.assertEqual(check["expected_vat"], 0)
        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_sub_paisa_difference_is_within_rounding_tolerance(self, configured):
        configured.return_value = {
            "Yarsa Labs": {"purchase": "VAT Payable", "sales": "VAT Payable"}
        }
        invoice = self.make_invoice(taxable_vat=544.614)

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_vat_on_previous_row_is_detected(self, configured):
        configured.return_value = {
            "ACME": {"sales": "VAT Payable", "purchase": "VAT Receivable"}
        }
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            taxes=[
                frappe._dict(
                    account_head="Import Duty",
                    charge_type="On Net Total",
                ),
                frappe._dict(
                    account_head="VAT Receivable",
                    charge_type="On Previous Row Total",
                ),
            ],
        )

        self.assertTrue(utils.vat_charged_on_added_taxes(invoice))

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_on_net_total_vat_is_not_added_taxes(self, configured):
        configured.return_value = {
            "ACME": {"sales": "VAT Payable", "purchase": "VAT Receivable"}
        }
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            taxes=[
                frappe._dict(
                    account_head="VAT Receivable",
                    charge_type="On Net Total",
                ),
            ],
        )

        self.assertFalse(utils.vat_charged_on_added_taxes(invoice))

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_previous_row_vat_includes_excise_in_taxable_base(self, configured):
        configured.return_value = {
            "ACME": {"sales": "VAT Payable", "purchase": "VAT Receivable"}
        }
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            grand_total=5753.9318,
            items=[
                frappe._dict(
                    item_code="Y101642",
                    net_amount=4849.5,
                    is_nontaxable_item=0,
                )
            ],
            taxes=[
                frappe._dict(
                    account_head="Import Duty",
                    charge_type="On Net Total",
                    tax_amount=0,
                    tax_amount_after_discount_amount=0,
                    add_deduct_tax="Add",
                    item_wise_tax_detail={"Y101642": [0.0, 0.0]},
                ),
                frappe._dict(
                    account_head="Excise",
                    charge_type="On Previous Row Total",
                    tax_amount=242.475,
                    tax_amount_after_discount_amount=242.475,
                    add_deduct_tax="Add",
                    item_wise_tax_detail={"Y101642": [5.0, 242.475]},
                ),
                frappe._dict(
                    account_head="VAT Receivable",
                    charge_type="On Previous Row Total",
                    tax_amount=661.9568,
                    tax_amount_after_discount_amount=661.9568,
                    add_deduct_tax="Add",
                    item_wise_tax_detail={"Y101642": [13.0, 661.95675]},
                ),
            ],
        )

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 5091.98)
        self.assertEqual(invoice.non_taxable_amount, 0)
        self.assertEqual(check["expected_vat"], 661.96)
        self.assertEqual(check["recorded_vat"], 661.96)
        self.assertFalse(check["has_vat_mismatch"])
        self.assertTrue(check["vat_on_added_taxes"])


if __name__ == "__main__":
    unittest.main()
