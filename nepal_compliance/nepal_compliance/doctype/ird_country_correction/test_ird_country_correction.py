import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from nepal_compliance.nepal_compliance.doctype.ird_country_correction import (
    ird_country_correction as correction_module,
)
from nepal_compliance.nepal_compliance.doctype.ird_country_correction.ird_country_correction import (
    IRDCountryCorrection,
    get_invoice_country,
    get_permitted_invoice,
)


class TestIRDCountryCorrection(unittest.TestCase):
    @patch.object(correction_module, "frappe")
    def test_invoice_snapshot_takes_precedence_over_address(self, frappe_mock):
        invoice = MagicMock(doctype="Sales Invoice")
        invoice.get.side_effect = {
            "customer_address": "ADDR-1",
            "ird_party_country": "India",
        }.get
        frappe_mock.db.get_value.return_value = "Nepal"

        self.assertEqual(get_invoice_country(invoice), "India")

    @patch.object(correction_module, "frappe")
    def test_legacy_invoice_uses_selected_address(self, frappe_mock):
        invoice = MagicMock(doctype="Purchase Invoice")
        invoice.get.side_effect = {
            "supplier_address": "ADDR-2",
            "ird_party_country": None,
        }.get
        frappe_mock.db.get_value.return_value = "China"

        self.assertEqual(get_invoice_country(invoice), "China")

    @patch.object(correction_module, "frappe")
    def test_source_invoice_submit_permission_is_required(self, frappe_mock):
        invoice = MagicMock(docstatus=1)
        frappe_mock.get_doc.return_value = invoice
        frappe_mock.has_permission.return_value = False
        frappe_mock.PermissionError = PermissionError
        frappe_mock.throw.side_effect = PermissionError

        with self.assertRaises(PermissionError):
            get_permitted_invoice("Sales Invoice", "SINV-1")

        invoice.check_permission.assert_called_once_with("read")
        frappe_mock.has_permission.assert_called_once_with(
            "Sales Invoice", "submit", doc=invoice
        )

    @patch.object(correction_module, "get_link_to_form", return_value="CORRECTION-LINK")
    @patch.object(correction_module, "now_datetime", return_value="2026-08-30 09:00:00")
    @patch.object(correction_module, "get_invoice_country", return_value="Nepal")
    @patch.object(correction_module, "get_permitted_invoice")
    @patch.object(correction_module, "frappe")
    def test_submit_updates_snapshot_and_adds_audit_comment(
        self,
        frappe_mock,
        get_invoice,
        _get_country,
        _now,
        _get_link,
    ):
        invoice = MagicMock()
        get_invoice.return_value = invoice
        frappe_mock.session.user = "manager@example.com"
        correction = SimpleNamespace(
            invoice_type="Sales Invoice",
            invoice="SINV-1",
            current_country="Nepal",
            new_country="India",
            reason="Wrong address <script>",
            doctype="IRD Country Correction",
            name="IRD-COUNTRY-2026-00001",
        )

        IRDCountryCorrection.before_submit(correction)

        frappe_mock.db.set_value.assert_called_once_with(
            "Sales Invoice", "SINV-1", "ird_party_country", "India"
        )
        comment = invoice.add_comment.call_args.args[1]
        self.assertIn("Nepal", comment)
        self.assertIn("India", comment)
        self.assertIn("manager@example.com", comment)
        self.assertIn("Wrong address &lt;script&gt;", comment)
        self.assertNotIn("Wrong address <script>", comment)
        self.assertEqual(correction.corrected_by, "manager@example.com")

    @patch.object(correction_module, "get_invoice_country", return_value="India")
    @patch.object(correction_module, "get_permitted_invoice", return_value=MagicMock())
    @patch.object(correction_module, "frappe")
    def test_submit_rejects_stale_current_country(
        self, frappe_mock, _get_invoice, _get_country
    ):
        frappe_mock.throw.side_effect = RuntimeError
        correction = SimpleNamespace(
            invoice_type="Sales Invoice",
            invoice="SINV-1",
            current_country="Nepal",
            new_country="China",
        )

        with self.assertRaises(RuntimeError):
            IRDCountryCorrection.before_submit(correction)

        frappe_mock.db.set_value.assert_not_called()
