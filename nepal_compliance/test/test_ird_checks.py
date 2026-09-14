import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import ird_checks, utils


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

    def test_missing_country_uses_nepal_pan_rule(self):
        context = frappe._dict(doctype="Sales Invoice", tax_id="123")
        party = frappe._dict(customer_type="Company", customer_group="Commercial")

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

    def test_vat_purchase_requires_supplier_tax_id_when_enabled(self):
        self.settings.enable_party_tax_id_check = 0
        self.settings.enable_purchase_vat_tax_id_check = 1
        context = frappe._dict(
            doctype="Purchase Invoice",
            check_vat_amount=130,
            tax_id="",
            ird_party_country="Nepal",
        )
        party = frappe._dict(
            supplier_type="Company",
            supplier_group="Foreign",
            tax_id="",
        )

        errors = ird_checks.check_party_tax_id(context, party, self.settings)

        self.assertEqual(errors[0]["code"], "missing_tax_id")

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

    def test_vat_check_uses_precise_register_amounts(self):
        context = frappe._dict(
            taxable_amount=311504.42,
            vat_amount=40495.58,
            check_taxable_amount=311504.4248,
            check_non_taxable_amount=0,
            check_vat_amount=40495.5752,
            summary_grand_total=352000,
        )

        self.assertEqual(ird_checks.check_amounts(context, self.settings), [])

        context.check_vat_amount = 40495.5753
        errors = ird_checks.check_amounts(context, self.settings)
        self.assertEqual([error["code"] for error in errors], ["vat_mismatch"])

    def test_report_taxable_base_preserves_added_tax_precision(self):
        item = frappe._dict(item_code="ITEM-1", net_amount=4849.5)
        vat_map = {"ITEM-1": [13, 661.95675]}

        taxable = utils.item_taxable_amount(item, 661.95675, vat_map, 4)

        self.assertEqual(taxable, 5091.975)

    def test_total_check_accepts_enabled_rounding(self):
        context = frappe._dict(
            check_taxable_amount=100.35,
            check_non_taxable_amount=0,
            check_vat_amount=13.0455,
            summary_grand_total=113,
            disable_rounded_total=0,
        )

        self.assertEqual(ird_checks.check_amounts(context, self.settings), [])

        context.disable_rounded_total = 1
        errors = ird_checks.check_amounts(context, self.settings)
        self.assertEqual([error["code"] for error in errors], ["total_mismatch"])

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

    def test_enabled_sidebar_attachment_satisfies_purchase_check(self):
        self.settings.consider_sidebar_purchase_attachments = 1
        context = frappe._dict(
            doctype="Purchase Invoice",
            attach_purchase_invoice=None,
            has_sidebar_purchase_attachment=1,
        )

        self.assertEqual(ird_checks.check_attachment(context, self.settings), [])

    def test_selected_attachment_field_satisfies_purchase_check(self):
        context = frappe._dict(
            doctype="Purchase Invoice",
            attach_purchase_invoice=None,
            has_accepted_purchase_attachment=1,
        )

        self.assertEqual(ird_checks.check_attachment(context, self.settings), [])

    @patch("nepal_compliance.ird_checks.frappe.get_all")
    def test_selected_custom_fields_are_resolved_safely(self, get_all):
        get_all.return_value = ["custom_bill_photo"]
        settings = frappe._dict(
            accepted_purchase_attachment_fields=[
                frappe._dict(custom_field="Purchase Invoice-custom_bill_photo")
            ]
        )

        fields = ird_checks._accepted_purchase_attachment_fields(settings)

        self.assertEqual(
            fields, {"attach_purchase_invoice", "custom_bill_photo"}
        )
        get_all.assert_called_once()

    @patch("nepal_compliance.ird_checks.frappe.get_all")
    def test_invoice_context_detects_only_direct_sidebar_file(self, get_all):
        get_all.side_effect = [
            [frappe._dict(name="PINV-1", supplier_address=None)],
            [
                frappe._dict(
                    attached_to_name="PINV-1",
                    attached_to_field=None,
                    file_url="/private/files/bill.pdf",
                ),
                frappe._dict(
                    attached_to_name="PINV-1",
                    attached_to_field="qr_code",
                    file_url="/private/files/qr.png",
                ),
            ],
        ]
        settings = frappe._dict(
            enable_purchase_attachment_check=1,
            consider_sidebar_purchase_attachments=1,
        )

        contexts = ird_checks._invoice_contexts(
            "Purchase Invoice", ["PINV-1"], settings
        )

        self.assertTrue(contexts["PINV-1"].has_sidebar_purchase_attachment)

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

    def test_summary_filter_selects_taxable_error_and_zero_value_rows(self):
        rows = [
            frappe._dict(
                invoice="A",
                invoice_name="A",
                total=113,
                taxable_amount=100,
                compliance_error_codes=[],
            ),
            frappe._dict(
                invoice="B",
                invoice_name="B",
                total=100,
                tax_exempt=100,
                compliance_error_codes=["vat_mismatch"],
            ),
            frappe._dict(
                invoice="C",
                invoice_name="C",
                total=0,
                compliance_error_codes=[],
            ),
        ]

        taxable = ird_checks.filter_summary_rows(rows, {"ird_summary_view": "taxable"})
        errors = ird_checks.filter_summary_rows(rows, {"ird_summary_view": "errors"})
        zero_value = ird_checks.filter_summary_rows(
            rows, {"ird_summary_view": "zero_value"}
        )

        self.assertEqual([row.invoice for row in taxable], ["A"])
        self.assertEqual([row.invoice for row in errors], ["B"])
        self.assertEqual([row.invoice for row in zero_value], ["C"])

    def test_checks_column_is_second_only_when_enabled(self):
        base = [
            {"fieldname": "invoice_date"},
            {"fieldname": "invoice"},
        ]

        self.assertEqual(ird_checks.check_columns(base, frappe._dict()), base)

        columns = ird_checks.check_columns(
            base, frappe._dict(enable_vat_amount_check=1)
        )
        self.assertEqual(columns[1]["fieldname"], "compliance_checks")
        self.assertNotIn("adjustment_notes", [column["fieldname"] for column in columns])

    def test_return_check_adds_adjustment_note_column(self):
        columns = ird_checks.check_columns(
            [{"fieldname": "invoice_date"}],
            frappe._dict(enable_return_match_check=1),
        )

        self.assertEqual(columns[1]["fieldname"], "compliance_checks")
        self.assertEqual(columns[-1]["fieldname"], "adjustment_notes")

    def test_report_check_amounts_combine_all_taxable_buckets(self):
        contexts = {"PINV-1": frappe._dict(is_return=0)}
        rows = [
            frappe._dict(
                invoice_name="PINV-1",
                taxable_amount=100,
                tax_amount=13,
                taxable_import_non_capital_amount=200,
                taxable_import_non_capital_tax=26,
                capital_taxable_amount=300,
                capital_taxable_tax=39,
                tax_exempt=50,
            )
        ]

        ird_checks._report_check_amounts(rows, contexts)

        self.assertEqual(contexts["PINV-1"].check_taxable_amount, 600)
        self.assertEqual(contexts["PINV-1"].check_vat_amount, 78)
        self.assertEqual(contexts["PINV-1"].check_non_taxable_amount, 50)

    @patch("nepal_compliance.ird_checks._invoice_hover_items", return_value={})
    @patch("nepal_compliance.ird_checks._submitted_returns", return_value={})
    @patch("nepal_compliance.ird_checks.frappe.get_cached_doc")
    @patch("nepal_compliance.ird_checks._parties")
    @patch("nepal_compliance.ird_checks._invoice_contexts")
    def test_decorate_rows_adds_errors_and_filters(
        self, contexts, parties, get_settings, _returns, _hover_items
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
        self.assertEqual(result[0].party_type, "Company")
        self.assertEqual(result[0].party_group, "Commercial")

    def test_return_without_original_invoice_is_error(self):
        context = frappe._dict(is_return=1, return_against=None)
        self.settings.enable_return_match_check = 1

        errors = ird_checks.check_return_reference(context, self.settings)

        self.assertEqual(errors[0]["code"], "missing_return_against")

    @patch("nepal_compliance.ird_checks.frappe.get_all")
    def test_submitted_notes_are_grouped_by_original(self, get_all):
        get_all.return_value = [
            frappe._dict(name="CN-1", return_against="SINV-1"),
            frappe._dict(name="CN-2", return_against="SINV-1"),
        ]

        grouped = ird_checks._submitted_returns("Sales Invoice", ["SINV-1"])

        self.assertEqual(grouped["SINV-1"], ["CN-1", "CN-2"])


if __name__ == "__main__":
    unittest.main()
