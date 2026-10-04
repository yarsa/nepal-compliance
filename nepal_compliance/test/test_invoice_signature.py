import unittest
from types import SimpleNamespace
from unittest.mock import patch

from nepal_compliance import utils


class TestInvoiceSignature(unittest.TestCase):
    def test_set_signed_by_records_the_submitting_user(self):
        doc = SimpleNamespace(doctype="Sales Invoice", signed_by=None)

        with patch.object(utils.frappe, "session", SimpleNamespace(user="accounts@example.com")):
            utils.set_signed_by(doc, "before_submit")

        self.assertEqual(doc.signed_by, "accounts@example.com")

    def test_set_signed_by_overwrites_a_stale_value(self):
        # An amended invoice is signed by whoever submits the amendment.
        doc = SimpleNamespace(doctype="Sales Invoice", signed_by="old@example.com")

        with patch.object(utils.frappe, "session", SimpleNamespace(user="new@example.com")):
            utils.set_signed_by(doc)

        self.assertEqual(doc.signed_by, "new@example.com")
