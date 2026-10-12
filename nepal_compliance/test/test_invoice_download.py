import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from nepal_compliance import invoice_download
from nepal_compliance.test.test_invoice_pdf import _pdf, _texts

FILES = {
    "/private/files/1-tax-invoice.pdf": _pdf(["TAX INVOICE 1"]),
    "/private/files/1-invoice.pdf": _pdf(["INVOICE 1"]),
    "/private/files/2-tax-invoice.pdf": _pdf(["TAX INVOICE 2"]),
    "/private/files/2-hand-bill.jpg": b"not a pdf",
    "/private/files/3-credit-note.pdf": _pdf(["CREDIT NOTE 3"]),
}
INVOICES = [
    frappe._dict(name="SINV-1", tax_invoice_attachment="/private/files/1-tax-invoice.pdf",
                 invoice_attachment="/private/files/1-invoice.pdf"),
    frappe._dict(name="SINV-2", tax_invoice_attachment="/private/files/2-tax-invoice.pdf",
                 invoice_attachment="/private/files/2-hand-bill.jpg"),
]


class TestDownloadAttachedInvoices(unittest.TestCase):
    def _download(self, copies, invoices=INVOICES):
        response = SimpleNamespace()
        db = MagicMock()
        db.get_value.side_effect = lambda doctype, filters, field: filters["file_url"]
        with patch.object(invoice_download.frappe, "get_list", return_value=invoices) as get_list, \
             patch.object(invoice_download.frappe, "db", db), \
             patch.object(invoice_download.frappe, "get_doc",
                          side_effect=lambda doctype, url: MagicMock(**{"get_content.return_value": FILES[url]})), \
             patch.object(invoice_download.frappe, "local", SimpleNamespace(response=response)):
            invoice_download.download_attached_invoices('["SINV-1", "SINV-2"]', copies)
        return response, get_list

    def test_both_puts_every_tax_invoice_before_every_invoice(self):
        response, get_list = self._download("both")

        pages = [text.strip() for text in _texts(response.filecontent)]
        self.assertEqual(pages, ["TAX INVOICE 1", "TAX INVOICE 2", "INVOICE 1"])  # the .jpg is left out
        self.assertEqual((response.filename, response.type), ("sales-invoices-both.pdf", "download"))
        # read through get_list, so only invoices the user may read are included
        self.assertEqual(get_list.call_args.kwargs["filters"], {"name": ["in", ["SINV-1", "SINV-2"]]})

    def test_vat_credit_note_comes_with_tax_invoice_and_both_only(self):
        credit_note = frappe._dict(name="SINV-3", is_return=1, tax_invoice_attachment="/private/files/3-credit-note.pdf",
                                   invoice_attachment=None)
        for copies, expected in (
            ("tax_invoice", ["TAX INVOICE 1", "TAX INVOICE 2", "CREDIT NOTE 3"]),
            ("both", ["TAX INVOICE 1", "TAX INVOICE 2", "CREDIT NOTE 3", "INVOICE 1"]),
            ("invoice", ["INVOICE 1"]),
        ):
            response, _get_list = self._download(copies, INVOICES + [credit_note])
            self.assertEqual([text.strip() for text in _texts(response.filecontent)], expected, copies)

    def test_one_copy_only(self):
        response, _get_list = self._download("invoice")

        self.assertEqual([text.strip() for text in _texts(response.filecontent)], ["INVOICE 1"])

    def test_nothing_to_download_or_unknown_choice_is_refused(self):
        with patch.object(invoice_download.frappe, "throw", side_effect=frappe.ValidationError) as throw:
            self.assertRaises(frappe.ValidationError, self._download, "invoice", [INVOICES[1]])
            self.assertRaises(frappe.ValidationError, self._download, "all")
        self.assertEqual(throw.call_count, 2)


if __name__ == "__main__":
    unittest.main()
