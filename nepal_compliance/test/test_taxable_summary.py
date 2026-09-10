import unittest
from unittest.mock import Mock, patch

import frappe

from nepal_compliance import taxable_summary, utils


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


class TestSelectableTaxableSummary(unittest.TestCase):
    def test_refresh_endpoints_are_post_only(self):
        allowed = frappe.allowed_http_methods_for_whitelisted_func
        self.assertEqual(
            allowed[taxable_summary.preview_taxable_summary_refresh], ["POST"]
        )
        self.assertEqual(
            allowed[taxable_summary.apply_taxable_summary_refresh], ["POST"]
        )
        self.assertEqual(
            allowed[taxable_summary.download_taxable_summary_csv], ["POST"]
        )

    @patch("nepal_compliance.taxable_summary.frappe.db.commit")
    @patch("nepal_compliance.taxable_summary._apply_change")
    @patch("nepal_compliance.taxable_summary._compute_refresh_row")
    @patch("nepal_compliance.taxable_summary._iter_invoice_rows")
    def test_apply_updates_only_selected_invoice(
        self, iter_rows, compute, apply_change, _commit
    ):
        selected_row = frappe._dict(name="PINV-1")
        other_row = frappe._dict(name="PINV-2")
        iter_rows.return_value = iter(
            [
                ("Purchase Invoice", selected_row),
                ("Purchase Invoice", other_row),
            ]
        )
        change = {"calculation_check": {"has_vat_mismatch": False}}
        compute.return_value = ("changed", change)

        result = taxable_summary._run_apply(
            "2026-01-01",
            "2026-12-31",
            [{"doctype": "Purchase Invoice", "name": "PINV-1"}],
            True,
        )

        compute.assert_called_once_with("Purchase Invoice", selected_row, True)
        apply_change.assert_called_once_with(change)
        self.assertEqual(result["updated"], 1)

    def test_csv_contains_selected_preview_row(self):
        data = taxable_summary.taxable_summary_csv_data(
            [
                {
                    "document_type": "Purchase Invoice",
                    "name": "YTPI-1",
                    "posting_date": "2026-08-24",
                    "company": "ACME",
                    "old_taxable_amount": 4849.5,
                    "new_taxable_amount": 5091.98,
                    "old_non_taxable_amount": 0,
                    "new_non_taxable_amount": 0,
                    "old_vat_amount": 661.96,
                    "new_vat_amount": 661.96,
                    "old_summary_grand_total": 5753.93,
                    "new_summary_grand_total": 5753.93,
                    "would_change": True,
                    "vat_on_added_taxes": True,
                    "calculation_check": {
                        "expected_vat": 661.96,
                        "recorded_vat": 661.96,
                        "vat_difference": 0,
                        "has_vat_mismatch": False,
                    },
                }
            ]
        )

        self.assertEqual(data[0], taxable_summary.TAXABLE_SUMMARY_CSV_COLUMNS)
        self.assertEqual(data[1][1], "YTPI-1")
        self.assertEqual(data[1][13], "Includes added taxes")
        self.assertEqual(data[1][17], "OK")

    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.frappe.db.set_value")
    def test_vat_mismatch_adds_error_tag_and_comment(self, _set_value, get_doc):
        doc = Mock()
        get_doc.return_value = doc
        change = {
            "doctype": "Sales Invoice",
            "name": "YTCN-1",
            "old_taxable_amount": 1663.7,
            "new_taxable_amount": 1796.44,
            "old_non_taxable_amount": 132.74,
            "new_non_taxable_amount": 0,
            "old_vat_amount": 216.28,
            "new_vat_amount": 216.28,
            "old_summary_grand_total": 2012.72,
            "new_summary_grand_total": 2012.72,
            "summary_grand_total": 2012.72,
            "item_vat_detail": None,
            "calculation_check": {
                "expected_vat": 233.54,
                "recorded_vat": 216.28,
                "vat_difference": -17.26,
                "has_vat_mismatch": True,
            },
        }

        taxable_summary._apply_change(change)

        doc.add_tag.assert_called_once_with("VAT Accounting Error")
        comments = [call.args[1] for call in doc.add_comment.call_args_list]
        self.assertTrue(any("VAT Accounting Error" in text for text in comments))
        self.assertTrue(any("accounting has 216.28" in text for text in comments))

    @patch("nepal_compliance.taxable_summary.frappe.db.commit")
    @patch("nepal_compliance.taxable_summary._flag_invoice")
    @patch("nepal_compliance.taxable_summary._apply_change")
    @patch("nepal_compliance.taxable_summary._compute_refresh_row")
    @patch("nepal_compliance.taxable_summary._iter_invoice_rows")
    def test_warning_only_invoice_is_tagged_without_summary_write(
        self, iter_rows, compute, apply_change, flag_invoice, _commit
    ):
        row = frappe._dict(name="YTCN-1")
        iter_rows.return_value = iter([("Sales Invoice", row)])
        change = {
            "would_change": False,
            "calculation_check": {"has_vat_mismatch": True},
        }
        compute.return_value = ("warning", change)

        result = taxable_summary._run_apply(
            "2026-01-01",
            "2026-12-31",
            [{"doctype": "Sales Invoice", "name": "YTCN-1"}],
            True,
        )

        apply_change.assert_not_called()
        flag_invoice.assert_called_once_with(change)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["calculation_warnings"], 1)

    def test_paisa_taxable_difference_is_ignored(self):
        old = frappe._dict(
            taxable_amount=681.41,
            non_taxable_amount=0,
            vat_amount=88.58,
            summary_grand_total=770,
        )
        new = frappe._dict(
            taxable_amount=681.42,
            non_taxable_amount=0,
            vat_amount=88.58,
            summary_grand_total=770,
        )

        self.assertFalse(
            taxable_summary._figures_changed(old, new, disable_rounded_total=1)
        )

    def test_sub_rupee_bill_total_difference_is_ignored(self):
        old = frappe._dict(
            taxable_amount=35690,
            non_taxable_amount=0,
            vat_amount=4639.7,
            summary_grand_total=40330,
        )
        new = frappe._dict(
            taxable_amount=35690,
            non_taxable_amount=0,
            vat_amount=4639.7,
            summary_grand_total=40329.7,
        )

        self.assertFalse(
            taxable_summary._figures_changed(old, new, disable_rounded_total=0)
        )

    def test_real_taxable_change_is_not_ignored(self):
        old = frappe._dict(
            taxable_amount=4849.5,
            non_taxable_amount=0,
            vat_amount=661.96,
            summary_grand_total=5753.93,
        )
        new = frappe._dict(
            taxable_amount=5091.98,
            non_taxable_amount=0,
            vat_amount=661.96,
            summary_grand_total=5753.93,
        )

        self.assertTrue(
            taxable_summary._figures_changed(old, new, disable_rounded_total=0)
        )


if __name__ == "__main__":
    unittest.main()
