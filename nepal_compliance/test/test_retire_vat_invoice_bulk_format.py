import unittest
from unittest.mock import MagicMock, call, patch

import frappe

from nepal_compliance.patches import retire_vat_invoice_bulk_format as patch_module

BULK = patch_module.BULK
STANDARD = patch_module.STANDARD


class TestRetireVatInvoiceBulkFormat(unittest.TestCase):
    def _run(self, exists=True, standard_seals=(), bulk_seals=()):
        db = MagicMock()
        db.exists.return_value = exists
        seals = {STANDARD: list(standard_seals), BULK: list(bulk_seals)}
        get_all = lambda doctype, filters, fields: seals[filters["print_format"]]
        with patch.object(patch_module.frappe, "db", db), \
             patch.object(patch_module.frappe, "get_all", side_effect=get_all), \
             patch.object(patch_module.frappe, "clear_cache"):
            patch_module.execute()
        return db

    def test_settings_move_to_the_standard_format_and_bulk_is_disabled(self):
        db = self._run(bulk_seals=[frappe._dict(name="SEAL-B", company="ACME")])

        db.set_value.assert_has_calls([
            call("Nepal Compliance Company Print Format",
                 {"parent": "Nepal Compliance Settings", "print_format": BULK}, "print_format", STANDARD),
            call("Nepal Compliance Print Seal", "SEAL-B", "print_format", STANDARD),
            call("Property Setter",
                 {"doc_type": "Sales Invoice", "property": "default_print_format", "value": BULK}, "value", STANDARD),
            call("Print Format", BULK, "disabled", 1),
        ])
        db.delete.assert_not_called()

    def test_bulk_seal_row_is_dropped_where_the_standard_format_has_one(self):
        db = self._run(
            standard_seals=[frappe._dict(name="SEAL-S", company=None)],
            bulk_seals=[frappe._dict(name="SEAL-B", company=None), frappe._dict(name="SEAL-C", company="ACME")],
        )

        db.delete.assert_called_once_with("Nepal Compliance Print Seal", {"name": "SEAL-B"})
        self.assertIn(call("Nepal Compliance Print Seal", "SEAL-C", "print_format", STANDARD), db.set_value.call_args_list)

    def test_sites_without_the_bulk_format_are_left_alone(self):
        db = self._run(exists=False)

        db.set_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()
