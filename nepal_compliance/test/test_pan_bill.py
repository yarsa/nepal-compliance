import json
import unittest
from unittest.mock import Mock, patch

import frappe

from nepal_compliance import default_tax_template, utils


class TestPanBill(unittest.TestCase):
    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_pan_bill_suppresses_only_configured_vat(self, configured):
        configured.return_value = {
            "ACME": {"sales": "VAT Payable", "purchase": "VAT Receivable"}
        }
        item = frappe._dict(
            item_tax_rate=json.dumps(
                {"VAT Payable": 13, "VAT Receivable": 13, "Excise": 5}
            )
        )
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            is_pan_or_abbreviated_bill=1,
            items=[item],
        )

        utils.apply_pan_bill_vat_override(invoice)

        self.assertEqual(
            json.loads(item.item_tax_rate),
            {"Excise": 5, "VAT Receivable": 0},
        )

    @patch("nepal_compliance.utils.set_taxable_amounts")
    @patch("nepal_compliance.utils.get_configured_vat_accounts")
    def test_pan_bill_tds_uses_bill_total(self, configured, set_summary):
        configured.return_value = {
            "ACME": {"sales": "VAT Payable", "purchase": "VAT Receivable"}
        }
        set_summary.side_effect = lambda doc, _method: doc.update(
            {"summary_grand_total": 1000}
        )
        invoice = frappe._dict(
            doctype="Purchase Invoice",
            company="ACME",
            is_pan_or_abbreviated_bill=1,
        )

        base, reason = utils.get_purchase_taxable_tds_base(invoice)

        self.assertEqual(base, 1000)
        self.assertIsNone(reason)

    @patch("nepal_compliance.default_tax_template.frappe.get_doc")
    @patch("nepal_compliance.default_tax_template.frappe.db.exists")
    def test_company_nepal_tax_becomes_purchase_default(self, exists, get_doc):
        exists.side_effect = [True, None]
        template = frappe._dict(
            is_default=0,
            company="Yarsa Tech Pvt. Ltd.",
        )
        template.save = Mock()
        get_doc.return_value = template

        default_tax_template.set_default_purchase_tax_template()

        self.assertEqual(
            exists.call_args_list[1].args,
            (
                "Purchase Taxes and Charges Template",
                {
                    "company": "Yarsa Tech Pvt. Ltd.",
                    "is_default": 1,
                    "disabled": 0,
                },
            ),
        )
        template.save.assert_called_once_with(ignore_permissions=True)

    @patch("nepal_compliance.default_tax_template.frappe.get_doc")
    @patch("nepal_compliance.default_tax_template.frappe.db.exists")
    def test_existing_purchase_default_is_preserved(self, exists, get_doc):
        exists.side_effect = [True, "Existing Purchase Tax - YT"]
        template = frappe._dict(
            is_default=0,
            company="Yarsa Tech Pvt. Ltd.",
        )
        template.save = Mock()
        get_doc.return_value = template

        default_tax_template.set_default_purchase_tax_template()

        template.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
