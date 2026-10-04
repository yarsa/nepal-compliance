import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from nepal_compliance import print_seal


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
