import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from nepal_compliance.nepal_compliance.doctype.nepal_compliance_settings import (
    nepal_compliance_settings as settings_module,
)

Settings = settings_module.NepalComplianceSettings


def _settings(value, changed=True, from_form=False):
    settings = frappe._dict(sales_invoice_print_format=value, has_value_changed=lambda field: changed)
    if from_form:
        settings["__onload"] = frappe._dict(shows_sales_invoice_print_format=1)
    return settings


class TestDefaultPrintFormat(unittest.TestCase):
    def _sync(self, settings, current_default):
        meta = SimpleNamespace(default_print_format=current_default)
        with patch.object(settings_module.frappe, "get_meta", return_value=meta), \
             patch.object(settings_module.frappe, "clear_cache"), \
             patch.object(settings_module, "make_property_setter") as make, \
             patch.object(settings_module, "delete_property_setter") as delete:
            Settings.sync_sales_invoice_print_format(settings)
        return make, delete

    def test_new_choice_becomes_the_sales_invoice_default(self):
        make, delete = self._sync(_settings("VAT Invoice - Standard"), current_default=None)

        make.assert_called_once_with(
            "Sales Invoice", None, "default_print_format", "VAT Invoice - Standard", "Data", for_doctype=True
        )
        delete.assert_not_called()

    def test_clearing_the_choice_restores_frappe_standard(self):
        make, delete = self._sync(_settings(None), current_default="VAT Invoice - Standard")

        delete.assert_called_once_with("Sales Invoice", "default_print_format")
        make.assert_not_called()

    def test_unchanged_field_never_touches_the_default(self):
        # A save from code that never loaded the form must not undo Customize Form.
        make, delete = self._sync(_settings(None, changed=False), current_default="Tax Invoice")

        make.assert_not_called()
        delete.assert_not_called()

    def test_choice_already_in_effect_is_not_rewritten(self):
        make, delete = self._sync(_settings("VAT Invoice - Standard"), current_default="VAT Invoice - Standard")

        make.assert_not_called()
        delete.assert_not_called()

    def test_onload_shows_the_default_in_effect(self):
        settings = frappe._dict(sales_invoice_print_format="Old Choice")
        settings.set_onload = lambda key, value: settings.setdefault("__onload", frappe._dict()).update({key: value})
        meta = SimpleNamespace(default_print_format="Set In Customize Form")
        with patch.object(settings_module.frappe, "get_meta", return_value=meta):
            Settings.onload(settings)

        self.assertEqual(settings.sales_invoice_print_format, "Set In Customize Form")
        self.assertTrue(settings["__onload"].shows_sales_invoice_print_format)

    def test_clearing_a_customize_form_default_from_the_form(self):
        # Stored value is empty and Customize Form set the default, so clearing
        # the field in the form leaves the stored value unchanged. The form save
        # must still remove the default it showed.
        settings = _settings(None, changed=False, from_form=True)
        make, delete = self._sync(settings, current_default="Set In Customize Form")

        delete.assert_called_once_with("Sales Invoice", "default_print_format")
        make.assert_not_called()

    def test_untouched_form_save_keeps_the_default(self):
        settings = _settings("Set In Customize Form", changed=True, from_form=True)
        make, delete = self._sync(settings, current_default="Set In Customize Form")

        make.assert_not_called()
        delete.assert_not_called()
