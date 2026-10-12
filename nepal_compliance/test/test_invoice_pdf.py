import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe
from pypdf import PdfReader

from nepal_compliance import invoice_pdf


def _pdf(*pages):
    """A PDF with one page per entry, each page holding those lines of text."""
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        stream = "BT /F1 12 Tf 72 720 Td " + " ".join(f"({line}) Tj 0 -20 Td" for line in lines) + " ET"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        objects.append(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {len(objects)} 0 R >>"
        )
        kids.append(f"{len(objects)} 0 R")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = "%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n" + "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    return out.encode("latin-1")


def _texts(pdf):
    return [page.extract_text() for page in PdfReader(BytesIO(pdf)).pages]


BOTH_COPIES = _pdf(["TAX INVOICE", "Invoice No: 1"], ["INVOICE", "Invoice No: 1"])


class TestAttachInvoicePdf(unittest.TestCase):
    def _attach(self, vat_registered=1, rendered=BOTH_COPIES, enabled=1, render_error=None, save_error=None,
                action="submit", **fields):
        doc = MagicMock(doctype="Sales Invoice", company="ABC Traders", _action=action)
        doc.name = "SINV/082-083/0001"
        doc.get.side_effect = fields.get
        db = MagicMock()
        db.get_value.return_value = frappe._dict(
            print_format="VAT Invoice - Standard", attach_invoice_pdf_on_submit=enabled, vat_registered=vat_registered
        )
        files = []

        def new_file(values):
            files.append(values)
            return MagicMock(file_url=f"/private/files/{values['file_name']}", **{"insert.side_effect": save_error})

        with patch.object(frappe, "db", db), \
             patch.object(frappe, "get_print", return_value=rendered, side_effect=render_error) as get_print, \
             patch.object(frappe, "get_doc", side_effect=new_file), \
             patch.object(frappe, "bold", side_effect=str), \
             patch.object(frappe, "log_error"), \
             patch.object(frappe, "msgprint"), \
             patch.object(invoice_pdf, "DocTags") as tags:
            invoice_pdf.attach_invoice_pdf(doc, "on_change")
        return SimpleNamespace(doc=doc, db=db, files=files, get_print=get_print, tags=tags.return_value)

    def assertTagged(self, run):
        run.doc.db_set.assert_not_called()
        run.tags.add.assert_called_once_with(run.doc.name, "Invoice PDF Not Attached")

    def test_vat_company_gets_each_copy_in_its_own_field(self):
        run = self._attach()

        run.get_print.assert_called_once_with("Sales Invoice", run.doc.name, "VAT Invoice - Standard", as_pdf=True)
        doctype, filters = run.db.get_value.call_args.args[:2]  # the company's Print Format by Company row
        self.assertEqual((doctype, filters["company"]), ("Nepal Compliance Company Print Format", "ABC Traders"))
        tax, office = run.files
        self.assertEqual((tax["attached_to_field"], tax["file_name"]), ("tax_invoice_attachment", "SINV-082-083-0001-tax-invoice.pdf"))
        self.assertEqual((office["attached_to_field"], office["file_name"]), ("invoice_attachment", "SINV-082-083-0001-invoice.pdf"))
        self.assertIn("TAX INVOICE", _texts(tax["content"])[0])
        self.assertEqual(len(_texts(office["content"])), 1)
        self.assertNotIn("TAX", _texts(office["content"])[0])
        run.doc.db_set.assert_called_once_with({
            "tax_invoice_attachment": "/private/files/SINV-082-083-0001-tax-invoice.pdf",
            "invoice_attachment": "/private/files/SINV-082-083-0001-invoice.pdf",
        }, update_modified=False)

    def test_other_company_gets_the_whole_pdf(self):
        pdf = _pdf(["INVOICE"])
        run = self._attach(vat_registered=0, rendered=pdf)

        (only,) = run.files
        self.assertEqual((only["attached_to_field"], only["content"]), ("attach_sales_invoice", pdf))
        run.doc.db_set.assert_called_once_with({"attach_sales_invoice": "/private/files/SINV-082-083-0001.pdf"}, update_modified=False)

    def test_vat_pdf_without_both_copies_is_tagged_not_attached(self):
        # e.g. the draft was printed, so the format now prints only an INVOICE copy
        run = self._attach(rendered=_pdf(["INVOICE", "COPY OF ORIGINAL 1"]))

        self.assertEqual(run.files, [])
        self.assertTagged(run)

    def test_failures_tag_without_blocking_the_submission(self):
        run = self._attach(render_error=RuntimeError("wkhtmltopdf failed"))
        self.assertTagged(run)
        run.db.rollback.assert_not_called()

        run = self._attach(save_error=OSError("disk full"))
        self.assertTagged(run)
        run.db.rollback.assert_called_once_with(save_point="attach_invoice_pdf")

    def test_skipped_cases_render_nothing(self):
        for kwargs in (
            {"action": "update_after_submit"},  # on_change also runs on later saves and on cancel
            {"action": "cancel"},
            {"enabled": 0},  # off for this company, or the company has no Print Format by Company row
            {"manual_invoice_no": "1043"},  # the hand bill is the original
            {"tax_invoice_attachment": "/private/files/x.pdf"},
            {"vat_registered": 0, "attach_sales_invoice": "/private/files/hand-bill.jpg"},
        ):
            run = self._attach(**kwargs)
            run.get_print.assert_not_called()
            run.tags.add.assert_not_called()


class TestClearNotAttachedTag(unittest.TestCase):
    def test_attaching_a_file_later_removes_the_tag(self):
        doc = MagicMock(doctype="Sales Invoice")
        doc.name = "SINV-1"
        doc.get.side_effect = {"invoice_attachment": "/private/files/x.pdf"}.get
        with patch.object(invoice_pdf, "DocTags") as tags:
            tags.return_value.get_tags.return_value = ",Invoice PDF Not Attached"
            invoice_pdf.clear_not_attached_tag(doc)
            doc.has_value_changed.return_value = False
            invoice_pdf.clear_not_attached_tag(doc)

        tags.return_value.remove.assert_called_once_with("SINV-1", "Invoice PDF Not Attached")


class TestSplitTaxInvoice(unittest.TestCase):
    def test_a_long_tax_invoice_keeps_all_its_pages(self):
        tax, office = invoice_pdf.split_tax_invoice(
            _pdf(["Tax  Invoice", "Item 1"], ["Item 40", "Invoice No: 1"], ["INVOICE", "Item 1"], ["Item 40"])
        )

        self.assertEqual([len(_texts(tax)), len(_texts(office))], [2, 2])

    def test_anything_but_both_copies_is_rejected(self):
        for pages in ([["TAX INVOICE"]], [["INVOICE"], ["TAX INVOICE"]], [["CREDIT NOTE"]]):
            self.assertIsNone(invoice_pdf.split_tax_invoice(_pdf(*pages)), pages)


if __name__ == "__main__":
    unittest.main()
