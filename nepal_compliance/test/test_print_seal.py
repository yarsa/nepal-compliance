import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from nepal_compliance import print_seal


def _invoice(**kwargs):
    values = {"doctype": "Sales Invoice", "docstatus": 1, "company": "Yarsa", "signed_by": "signer@example.com"}
    values.update(kwargs)
    return frappe._dict(values)


def _db(**values):
    return SimpleNamespace(get_value=lambda doctype, name, field: values.get(field))


class TestGetPrintSeal(unittest.TestCase):
    def _seal(self, doc, rows, can_print=True):
        with patch.object(print_seal.frappe, "has_permission", return_value=can_print), \
             patch.object(print_seal.frappe, "get_all", return_value=rows), \
             patch.object(print_seal.frappe, "db", _db(company_stamp="/private/files/s.png",
                                                      signature_image="/private/files/g.png")), \
             patch.object(print_seal, "_image_data_uri", side_effect=lambda url: f"data:{url}"):
            return print_seal.get_print_seal(doc, "VAT Invoice - Standard")

    def test_embeds_stamp_and_signature_with_sizes_and_offsets(self):
        row = frappe._dict(show_stamp=1, stamp_height=25, stamp_offset_x=3, stamp_offset_y=2,
                           show_signature=1, signature_height=10, signature_offset_x=-4, signature_offset_y=-1)
        seal = self._seal(_invoice(), [row])

        self.assertEqual(seal.stamp, "data:/private/files/s.png")
        self.assertEqual(seal.signature, "data:/private/files/g.png")
        self.assertEqual(seal.stamp_style, "height: 25.0mm; left: 3.0mm; bottom: -10.0mm;")
        self.assertEqual(seal.signature_style, "height: 10.0mm; margin-left: -4.0mm; bottom: 2.0mm;")

    def test_original_size_drops_the_height(self):
        row = frappe._dict(show_stamp=1, stamp_original_size=1, stamp_height=25)
        seal = self._seal(_invoice(), [row])

        self.assertNotIn("height", seal.stamp_style)
        self.assertIsNone(seal.signature)

    def test_nothing_without_a_settings_row_for_the_format(self):
        seal = self._seal(_invoice(), [])
        self.assertIsNone(seal.stamp)
        self.assertIsNone(seal.signature)

    def test_nothing_on_drafts_or_when_the_user_cannot_print(self):
        row = frappe._dict(show_stamp=1, show_signature=1)
        self.assertIsNone(self._seal(_invoice(docstatus=0), [row]).stamp)
        self.assertIsNone(self._seal(_invoice(), [row], can_print=False).stamp)

    def test_no_signature_when_the_invoice_has_no_signer(self):
        # Invoices submitted before Signed By existed keep the blank line.
        row = frappe._dict(show_stamp=1, show_signature=1)
        seal = self._seal(_invoice(signed_by=None), [row])
        self.assertIsNotNone(seal.stamp)
        self.assertIsNone(seal.signature)


class TestSecureFiles(unittest.TestCase):
    def test_company_stamp_is_made_private_and_attached_to_settings(self):
        file = MagicMock(is_private=0, file_url="/files/stamp.png")

        def save(**kwargs):
            file.file_url = "/private/files/stamp.png"

        file.save.side_effect = save
        company = frappe._dict(doctype="Company", name="Yarsa", company_stamp="/files/stamp.png")
        with patch.object(print_seal.frappe, "db", SimpleNamespace(exists=lambda *a, **k: False)), \
             patch.object(print_seal.frappe, "get_all", return_value=["FILE-1"]), \
             patch.object(print_seal.frappe, "get_doc", return_value=file):
            print_seal.secure_company_stamp(company)

        self.assertEqual(file.is_private, 1)
        self.assertEqual(
            (file.attached_to_doctype, file.attached_to_name, file.attached_to_field),
            (print_seal.SETTINGS, print_seal.SETTINGS, None),
        )
        self.assertEqual(company.company_stamp, "/private/files/stamp.png")

    def test_already_secured_stamp_is_left_alone(self):
        company = frappe._dict(doctype="Company", name="Yarsa", company_stamp="/private/files/stamp.png")
        with patch.object(print_seal.frappe, "db", SimpleNamespace(exists=lambda *a, **k: True)), \
             patch.object(print_seal.frappe, "get_doc") as get_doc:
            print_seal.secure_company_stamp(company)

        get_doc.assert_not_called()
        self.assertEqual(company.company_stamp, "/private/files/stamp.png")

    def test_private_signature_stays_attached_to_its_user(self):
        file = MagicMock(is_private=1, file_url="/private/files/sign.png")
        user = frappe._dict(doctype="User", name="a@example.com", signature_image="/private/files/sign.png")
        with patch.object(print_seal.frappe, "get_all", return_value=["FILE-2"]), \
             patch.object(print_seal.frappe, "get_doc", return_value=file):
            print_seal.secure_user_signature(user)

        file.save.assert_not_called()
        self.assertEqual(user.signature_image, "/private/files/sign.png")

    def test_detach_removes_only_the_company_attachment_record(self):
        company = frappe._dict(doctype="Company", name="Yarsa", company_stamp="/private/files/stamp.png")
        db = SimpleNamespace(exists=lambda *a, **k: True, delete=MagicMock())
        with patch.object(print_seal.frappe, "db", db):
            print_seal.detach_company_stamp(company)

        db.delete.assert_called_once_with("File", {
            "file_url": "/private/files/stamp.png",
            "attached_to_doctype": "Company",
            "attached_to_name": "Yarsa",
            "attached_to_field": "company_stamp",
        })
