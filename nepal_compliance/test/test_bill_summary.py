import unittest
from unittest.mock import Mock, patch

import frappe

from nepal_compliance import utils


def unsaved_invoice(doctype="Sales Invoice"):
    doc = frappe._dict(doctype=doctype, name="new-sales-invoice-1", owner="Administrator")
    doc.calculate_taxes_and_totals = Mock()
    return doc


@patch("nepal_compliance.utils.frappe.has_permission", return_value=True)
class TestLiveBillSummary(unittest.TestCase):
    @patch("nepal_compliance.utils.set_taxable_amounts")
    @patch("nepal_compliance.utils.frappe.get_doc")
    def test_totals_run_before_the_summary_and_only_its_figures_return(self, get_doc, summary, _perm):
        doc = unsaved_invoice()
        get_doc.return_value = doc

        def fill(invoice, _method):
            # the item discount is only spread over the rows once ERPNext has totalled them
            invoice.calculate_taxes_and_totals.assert_called_once_with()
            invoice.update(bill_subtotal=1450, taxable_discount=190, taxable_amount=810, item_vat_detail="{}")

        summary.side_effect = fill

        result = utils.get_bill_summary('{"doctype": "Sales Invoice"}')

        self.assertEqual(set(result), set(utils.BILL_SUMMARY_FIELDS))
        self.assertEqual((result["bill_subtotal"], result["taxable_discount"]), (1450, 190))

    @patch("nepal_compliance.utils._", side_effect=lambda text: text)
    @patch("nepal_compliance.utils.frappe.throw", side_effect=frappe.ValidationError)
    @patch("nepal_compliance.utils.frappe.get_doc")
    def test_other_doctypes_are_refused(self, get_doc, throw, _translate, _perm):
        doc = unsaved_invoice("Journal Entry")
        get_doc.return_value = doc
        with self.assertRaises(frappe.ValidationError):
            utils.get_bill_summary({"doctype": "Journal Entry"})
        doc.calculate_taxes_and_totals.assert_not_called()

    @patch("nepal_compliance.utils.frappe.clear_messages")
    @patch("nepal_compliance.utils.frappe.get_doc")
    def test_a_half_filled_form_returns_nothing_without_a_message(self, get_doc, clear_messages, _perm):
        doc = unsaved_invoice()
        doc.calculate_taxes_and_totals.side_effect = frappe.ValidationError
        get_doc.return_value = doc

        self.assertIsNone(utils.get_bill_summary({"doctype": "Sales Invoice"}))
        clear_messages.assert_called_once_with()

    @patch("nepal_compliance.excise._company_excise_config", return_value=(None, False))
    @patch("nepal_compliance.utils.get_configured_vat_accounts", return_value={"ACME": {"sales": "VAT Payable"}})
    @patch("nepal_compliance.utils.frappe.get_doc")
    def test_live_summary_shows_no_discount_for_a_rate_above_the_price_list(self, get_doc, _vat, _excise, _perm):
        # the real summary runs here: ERPNext's discount_amount is -141.59 for a rate above
        # the price list, which used to show as Subtotal 2,017.70 and Discount -141.59
        doc = unsaved_invoice()
        doc.update(
            company="ACME",
            ignore_pricing_rule=1,
            items=[frappe._dict(item_code="A", qty=1, price_list_rate=2017.70, rate=2159.29, discount_amount=-141.59, net_amount=2159.29)],
            taxes=[
                frappe._dict(
                    account_head="VAT Payable",
                    rate=13,
                    tax_amount_after_discount_amount=280.71,
                    item_wise_tax_detail={"A": [13, 280.71]},
                )
            ],
            grand_total=2440,
        )
        get_doc.return_value = doc

        result = utils.get_bill_summary({"doctype": "Sales Invoice"})

        self.assertAlmostEqual(result["taxable_discount"], 0)
        self.assertAlmostEqual(result["bill_subtotal"], 2159.29)
        self.assertAlmostEqual(result["bill_subtotal"] - result["taxable_discount"], result["taxable_amount"] + result["non_taxable_amount"])


if __name__ == "__main__":
    unittest.main()
