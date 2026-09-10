import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import utils


class TestTaxableSummaryCalculation(unittest.TestCase):
    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_non_taxable_item_flag_classifies_item_totals(self, configured):
        configured.return_value = {
            "ACME": {"purchase": "VAT Receivable", "sales": "VAT Payable"}
        }
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            grand_total=32762.94,
            items=[
                frappe._dict(
                    item_code="Taxable", net_amount=4189.33, is_nontaxable_item=0
                ),
                frappe._dict(
                    item_code="Non-Taxable",
                    net_amount=28029,
                    is_nontaxable_item=1,
                ),
            ],
            taxes=[
                frappe._dict(
                    account_head="VAT Receivable",
                    tax_amount_after_discount_amount=544.61,
                    item_wise_tax_detail={"Taxable": [13, 544.61]},
                )
            ],
        )

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 4189.33)
        self.assertEqual(invoice.non_taxable_amount, 28029)
        self.assertEqual(invoice.vat_amount, 544.61)
        self.assertFalse(check["has_vat_mismatch"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_previous_row_vat_includes_excise_in_taxable_base(self, configured):
        configured.return_value = {
            "ACME": {"purchase": "VAT Receivable", "sales": "VAT Payable"}
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
                    tax_amount_after_discount_amount=0,
                    item_wise_tax_detail={"Y101642": [0, 0]},
                ),
                frappe._dict(
                    account_head="Excise",
                    charge_type="On Previous Row Total",
                    tax_amount_after_discount_amount=242.475,
                    item_wise_tax_detail={"Y101642": [5, 242.475]},
                ),
                frappe._dict(
                    account_head="VAT Receivable",
                    charge_type="On Previous Row Total",
                    tax_amount_after_discount_amount=661.9568,
                    item_wise_tax_detail={"Y101642": [13, 661.95675]},
                ),
            ],
        )

        check = utils.set_taxable_amounts(
            invoice, None, consider_is_non_taxable_item=True
        )

        self.assertEqual(invoice.taxable_amount, 5091.98)
        self.assertEqual(check["expected_vat"], 661.96)
        self.assertEqual(check["recorded_vat"], 661.96)
        self.assertFalse(check["has_vat_mismatch"])
        self.assertTrue(check["vat_on_added_taxes"])

    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_on_net_total_vat_does_not_include_added_taxes(self, configured):
        configured.return_value = {
            "ACME": {"purchase": "VAT Receivable", "sales": "VAT Payable"}
        }
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            taxes=[
                frappe._dict(
                    account_head="VAT Receivable",
                    charge_type="On Net Total",
                )
            ],
        )

        self.assertFalse(utils.vat_charged_on_added_taxes(invoice))


if __name__ == "__main__":
    unittest.main()
