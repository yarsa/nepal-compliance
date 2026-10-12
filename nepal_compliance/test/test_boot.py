import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import boot

VAT_ACCOUNTS = {"ACME": {"sales": "VAT Payable - A", "purchase": "VAT Receivable - A"}}


def cached_doc(doctype, name=None):
    if doctype == "User":
        return frappe._dict(use_ad_date=0)
    return frappe._dict(enable_nepali_date=1, date_format="YYYY-MM-DD")


@patch("frappe.session", frappe._dict(user="accounts@example.com"))
class TestBootInfo(unittest.TestCase):
    @patch("nepal_compliance.boot.get_configured_vat_accounts", return_value=VAT_ACCOUNTS)
    @patch("nepal_compliance.boot.frappe.get_cached_doc", side_effect=cached_doc)
    def test_forms_get_the_vat_accounts_of_every_company(self, _cached_doc, _vat_accounts):
        bootinfo = frappe._dict()
        boot.get_boot_info(bootinfo)
        self.assertEqual(bootinfo["nepal_compliance"]["vat_accounts"], VAT_ACCOUNTS)

    @patch("nepal_compliance.boot.frappe.log_error")
    @patch("nepal_compliance.boot.frappe.get_cached_doc", side_effect=frappe.DoesNotExistError)
    def test_missing_settings_leave_no_vat_accounts(self, _cached_doc, _log_error):
        bootinfo = frappe._dict()
        boot.get_boot_info(bootinfo)
        self.assertEqual(bootinfo["nepal_compliance"]["vat_accounts"], {})


if __name__ == "__main__":
    unittest.main()
