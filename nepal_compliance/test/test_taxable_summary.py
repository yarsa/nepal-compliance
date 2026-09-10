import json
import unittest
from unittest.mock import Mock, patch

import frappe

from nepal_compliance import taxable_summary, utils


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


class TestSelectableTaxableSummary(unittest.TestCase):
    def test_document_types_separate_invoices_and_returns(self):
        self.assertEqual(
            taxable_summary._document_type("Sales Invoice", 0),
            "Sales Invoice",
        )
        self.assertEqual(
            taxable_summary._document_type("Sales Invoice", 1),
            "Sales Return",
        )
        self.assertEqual(
            taxable_summary._document_type("Purchase Invoice", 0),
            "Purchase Invoice",
        )
        self.assertEqual(
            taxable_summary._document_type("Purchase Invoice", 1),
            "Purchase Return",
        )

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
        change = {
            "calculation_check": {
                "has_vat_mismatch": True,
            }
        }
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
        self.assertEqual(result["calculation_warnings"], 1)

    @patch("nepal_compliance.taxable_summary._iter_invoice_rows", return_value=iter([]))
    def test_missing_selection_is_reported_as_stale(self, _iter_rows):
        result = taxable_summary._run_apply(
            "2026-01-01",
            "2026-12-31",
            [{"doctype": "Sales Invoice", "name": "SINV-MISSING"}],
            True,
        )

        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["stale"], 1)

    @patch("nepal_compliance.taxable_summary.enqueue")
    @patch("nepal_compliance.taxable_summary._count_invoices", return_value=501)
    @patch("nepal_compliance.taxable_summary._resolve_dates")
    @patch("nepal_compliance.taxable_summary._ensure_permission")
    def test_background_preview_propagates_option_and_request(
        self, _permission, resolve_dates, _count, enqueue
    ):
        resolve_dates.return_value = ("2026-01-01", "2026-12-31")

        result = taxable_summary.preview_taxable_summary_refresh(
            "2026-01-01",
            "2026-12-31",
            consider_is_non_taxable_item=1,
            request_id="preview-request",
        )

        self.assertTrue(result["queued"])
        self.assertEqual(result["request_id"], "preview-request")
        self.assertTrue(enqueue.call_args.kwargs["consider_is_non_taxable_item"])
        self.assertEqual(
            enqueue.call_args.kwargs["request_id"], "preview-request"
        )

    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.frappe.db.set_value")
    def test_comment_includes_old_and_new_bill_total(self, _set_value, get_doc):
        doc = Mock()
        get_doc.return_value = doc
        change = {
            "doctype": "Purchase Invoice",
            "name": "PINV-1",
            "old_taxable_amount": 0,
            "new_taxable_amount": 100,
            "old_non_taxable_amount": 100,
            "new_non_taxable_amount": 0,
            "old_vat_amount": 13,
            "new_vat_amount": 13,
            "old_summary_grand_total": 113,
            "new_summary_grand_total": 113,
            "summary_grand_total": 113,
            "item_vat_detail": None,
            "calculation_check": None,
        }

        taxable_summary._apply_change(change)

        comment = doc.add_comment.call_args.args[1]
        self.assertIn("Bill Total: 113.0 → 113.0", comment)
        doc.add_tag.assert_not_called()

    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.frappe.db.set_value")
    def test_mismatch_adds_error_tag_and_comment(self, _set_value, get_doc):
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
        self.assertTrue(any("Expected VAT 233.54" in text for text in comments))

    def test_csv_includes_selected_preview_rows(self):
        data = taxable_summary.taxable_summary_csv_data(
            [
                {
                    "document_type": "Purchase Invoice",
                    "doctype": "Purchase Invoice",
                    "name": "YTPI-2083/84-00268",
                    "posting_date": "2026-08-24",
                    "company": "Yarsa Tech Pvt. Ltd.",
                    "old_taxable_amount": 4849.5,
                    "new_taxable_amount": 4849.5,
                    "old_non_taxable_amount": 0,
                    "new_non_taxable_amount": 0,
                    "old_vat_amount": 661.96,
                    "new_vat_amount": 661.96,
                    "old_summary_grand_total": 5753.93,
                    "new_summary_grand_total": 5753.93,
                    "would_change": False,
                    "vat_on_added_taxes": True,
                    "calculation_check": {
                        "expected_vat": 630.44,
                        "recorded_vat": 661.96,
                        "vat_difference": 31.52,
                        "has_vat_mismatch": True,
                    },
                }
            ]
        )

        self.assertEqual(data[0], taxable_summary.TAXABLE_SUMMARY_CSV_COLUMNS)
        self.assertEqual(data[1][1], "YTPI-2083/84-00268")
        self.assertEqual(data[1][13], "VAT Accounting Error")
        self.assertEqual(data[1][17], "Error")

    @patch("nepal_compliance.taxable_summary._ensure_permission")
    def test_csv_download_requires_selected_rows(self, _permission):
        with self.assertRaises(frappe.ValidationError):
            taxable_summary.download_taxable_summary_csv([])

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

    @patch("nepal_compliance.taxable_summary.frappe.has_permission", return_value=True)
    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.set_taxable_amounts")
    def test_previous_row_vat_can_be_applied(self, set_summary, get_doc, _perm):
        doc = frappe._dict(
            doctype="Purchase Invoice",
            taxable_amount=5091.98,
            non_taxable_amount=0,
            vat_amount=661.96,
            summary_grand_total=5753.93,
            item_vat_detail=None,
            taxes=[],
        )
        get_doc.return_value = doc

        def mutate(invoice, _method, consider_is_non_taxable_item=False):
            invoice.taxable_amount = 5091.98
            return {
                "expected_vat": 661.96,
                "recorded_vat": 661.96,
                "vat_difference": 0,
                "has_vat_mismatch": False,
                "vat_on_added_taxes": True,
            }

        set_summary.side_effect = mutate
        row = frappe._dict(
            name="YTPI-1",
            company="ACME",
            posting_date="2026-08-24",
            is_return=0,
            taxable_amount=4849.5,
            non_taxable_amount=0,
            vat_amount=661.96,
            summary_grand_total=5753.93,
        )

        status, change = taxable_summary._compute_refresh_row(
            "Purchase Invoice", row, True
        )

        self.assertEqual(status, "changed")
        self.assertTrue(change["would_change"])
        self.assertEqual(change["new_taxable_amount"], 5091.98)

    @patch("nepal_compliance.taxable_summary.frappe.db.commit")
    @patch("nepal_compliance.taxable_summary._apply_change")
    @patch("nepal_compliance.taxable_summary._compute_refresh_row")
    @patch("nepal_compliance.taxable_summary._iter_invoice_rows")
    def test_apply_updates_previous_row_vat_invoice(
        self, iter_rows, compute, apply_change, _commit
    ):
        row = frappe._dict(name="YTPI-1")
        iter_rows.return_value = iter([("Purchase Invoice", row)])
        change = {
            "vat_on_added_taxes": True,
            "calculation_check": {"has_vat_mismatch": False},
        }
        compute.return_value = ("changed", change)

        result = taxable_summary._run_apply(
            "2026-01-01",
            "2026-12-31",
            [{"doctype": "Purchase Invoice", "name": "YTPI-1"}],
            True,
        )

        apply_change.assert_called_once_with(change)
        self.assertEqual(result["updated"], 1)

    @patch("nepal_compliance.taxable_summary.frappe.db.commit")
    @patch("nepal_compliance.taxable_summary._flag_invoice")
    @patch("nepal_compliance.taxable_summary._apply_change")
    @patch("nepal_compliance.taxable_summary._compute_refresh_row")
    @patch("nepal_compliance.taxable_summary._iter_invoice_rows")
    def test_apply_tags_warning_only_vat_error(
        self, iter_rows, compute, apply_change, flag_invoice, _commit
    ):
        row = frappe._dict(name="YTCN-1")
        iter_rows.return_value = iter([("Sales Invoice", row)])
        change = {
            "would_change": False,
            "calculation_check": {
                "expected_vat": 233.54,
                "recorded_vat": 216.28,
                "vat_difference": -17.26,
                "has_vat_mismatch": True,
            },
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

    def test_paisa_taxable_rounding_is_ignored(self):
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
        self.assertFalse(
            taxable_summary._figures_changed(old, new, disable_rounded_total=0)
        )

    def test_sub_rupee_bill_total_rounding_is_ignored(self):
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
        self.assertFalse(
            taxable_summary._figures_changed(old, new, disable_rounded_total=1)
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

    @patch("nepal_compliance.taxable_summary.frappe.has_permission", return_value=True)
    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.set_taxable_amounts")
    def test_compute_skips_minor_rounding(self, set_summary, get_doc, _perm):
        doc = frappe._dict(
            doctype="Sales Invoice",
            disable_rounded_total=0,
            taxable_amount=681.42,
            non_taxable_amount=0,
            vat_amount=88.58,
            summary_grand_total=770,
            item_vat_detail=None,
        )
        get_doc.return_value = doc

        def mutate(invoice, _method, consider_is_non_taxable_item=False):
            invoice.taxable_amount = 681.42
            return {
                "expected_vat": 88.58,
                "recorded_vat": 88.58,
                "vat_difference": 0,
                "has_vat_mismatch": False,
                "vat_on_added_taxes": False,
            }

        set_summary.side_effect = mutate
        row = frappe._dict(
            name="YTSI-1",
            company="ACME",
            posting_date="2026-07-20",
            is_return=0,
            taxable_amount=681.41,
            non_taxable_amount=0,
            vat_amount=88.58,
            summary_grand_total=770,
        )

        status, change = taxable_summary._compute_refresh_row(
            "Sales Invoice", row, True
        )

        self.assertEqual(status, "unchanged")
        self.assertIsNone(change)

    @patch("nepal_compliance.taxable_summary.frappe.has_permission", return_value=True)
    @patch("nepal_compliance.taxable_summary.frappe.get_doc")
    @patch("nepal_compliance.taxable_summary.set_taxable_amounts")
    def test_compute_returns_warning_for_vat_accounting_error(
        self, set_summary, get_doc, _perm
    ):
        doc = frappe._dict(
            doctype="Sales Invoice",
            disable_rounded_total=0,
            taxable_amount=1796.44,
            non_taxable_amount=0,
            vat_amount=216.28,
            summary_grand_total=2012.72,
            item_vat_detail=None,
        )
        get_doc.return_value = doc

        def mutate(invoice, _method, consider_is_non_taxable_item=False):
            return {
                "expected_vat": 233.54,
                "recorded_vat": 216.28,
                "vat_difference": -17.26,
                "has_vat_mismatch": True,
                "vat_on_added_taxes": False,
            }

        set_summary.side_effect = mutate
        row = frappe._dict(
            name="YTCN-1",
            company="ACME",
            posting_date="2026-07-20",
            is_return=1,
            taxable_amount=1796.44,
            non_taxable_amount=0,
            vat_amount=216.28,
            summary_grand_total=2012.72,
        )

        status, change = taxable_summary._compute_refresh_row(
            "Sales Invoice", row, True
        )

        self.assertEqual(status, "warning")
        self.assertFalse(change["would_change"])
        self.assertTrue(change["calculation_check"]["has_vat_mismatch"])


if __name__ == "__main__":
    unittest.main()
