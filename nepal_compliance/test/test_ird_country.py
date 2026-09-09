import unittest
from unittest.mock import patch

import frappe

from nepal_compliance.ird_country import (
    is_foreign_country,
    resolve_ird_country,
    set_invoice_party_country,
)


class TestIRDCountry(unittest.TestCase):
    def test_nepal_and_missing_country_are_domestic(self):
        self.assertFalse(is_foreign_country(" Nepal "))
        self.assertFalse(is_foreign_country("NEPAL"))
        self.assertFalse(is_foreign_country(None))

    def test_non_nepal_country_is_foreign(self):
        self.assertTrue(is_foreign_country("India"))
        self.assertTrue(is_foreign_country("China"))

    def test_snapshot_takes_precedence_over_current_address(self):
        self.assertEqual(resolve_ird_country("India", "Nepal"), "India")

    def test_address_country_is_used_for_legacy_invoice(self):
        self.assertEqual(resolve_ird_country(None, " India "), "India")
        self.assertEqual(resolve_ird_country(None, None), "Nepal")

    @patch("nepal_compliance.ird_country.frappe")
    def test_sales_invoice_snapshots_customer_address_country(self, frappe_mock):
        get_value = frappe_mock.db.get_value
        get_value.return_value = "India"
        doc = frappe._dict(
            doctype="Sales Invoice",
            docstatus=0,
            customer_address="Customer Billing",
        )

        set_invoice_party_country(doc)

        get_value.assert_called_once_with("Address", "Customer Billing", "country")
        self.assertEqual(doc.ird_party_country, "India")

    @patch("nepal_compliance.ird_country.frappe")
    def test_purchase_invoice_snapshots_supplier_address_country(self, frappe_mock):
        get_value = frappe_mock.db.get_value
        get_value.return_value = "China"
        doc = frappe._dict(
            doctype="Purchase Invoice",
            docstatus=0,
            supplier_address="Supplier Billing",
        )

        set_invoice_party_country(doc)

        get_value.assert_called_once_with("Address", "Supplier Billing", "country")
        self.assertEqual(doc.ird_party_country, "China")

    @patch("nepal_compliance.ird_country.frappe")
    def test_missing_address_defaults_to_nepal(self, frappe_mock):
        get_value = frappe_mock.db.get_value
        doc = frappe._dict(doctype="Sales Invoice", docstatus=0)

        set_invoice_party_country(doc)

        get_value.assert_not_called()
        self.assertEqual(doc.ird_party_country, "Nepal")

    @patch("nepal_compliance.ird_country.frappe")
    def test_submitted_invoice_keeps_existing_snapshot(self, frappe_mock):
        get_value = frappe_mock.db.get_value
        doc = frappe._dict(
            doctype="Sales Invoice",
            docstatus=1,
            customer_address="Customer Billing",
            ird_party_country="India",
        )

        set_invoice_party_country(doc)

        get_value.assert_not_called()
        self.assertEqual(doc.ird_party_country, "India")

    @patch("nepal_compliance.ird_country.frappe")
    def test_submitted_invoice_without_snapshot_is_not_changed_directly(
        self, frappe_mock
    ):
        get_value = frappe_mock.db.get_value
        doc = frappe._dict(
            doctype="Purchase Invoice",
            docstatus=1,
            supplier_address="Supplier Billing",
        )

        set_invoice_party_country(doc)

        get_value.assert_not_called()
        self.assertIsNone(doc.ird_party_country)
