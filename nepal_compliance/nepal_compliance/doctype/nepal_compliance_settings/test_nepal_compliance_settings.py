# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and Contributors
# For license information, please see LICENSE at the root of this repository

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from nepal_compliance.nepal_compliance.doctype.nepal_compliance_settings.nepal_compliance_settings import (
	NepalComplianceSettings,
)


class TestNepalComplianceSettings(FrappeTestCase):
	def test_party_tax_rules_require_both_sides(self):
		settings = frappe._dict(
			enable_party_tax_id_check=1,
			customer_tax_id_rules=[
				frappe._dict(idx=1, match_by="Type", customer_type="Company")
			],
			supplier_tax_id_rules=[],
		)

		with self.assertRaises(frappe.ValidationError):
			NepalComplianceSettings._validate_party_tax_id_rules(settings)

	def test_duplicate_party_tax_rule_is_rejected(self):
		rule = frappe._dict(idx=1, match_by="Group", customer_group="Commercial")
		settings = frappe._dict(
			enable_party_tax_id_check=1,
			customer_tax_id_rules=[rule, frappe._dict(rule, idx=2)],
			supplier_tax_id_rules=[
				frappe._dict(idx=1, match_by="Type", supplier_type="Company")
			],
		)

		with self.assertRaises(frappe.ValidationError):
			NepalComplianceSettings._validate_party_tax_id_rules(settings)

	def test_invalid_party_tax_rule_values_are_rejected(self):
		supplier_rule = frappe._dict(
			idx=1, match_by="Type", supplier_type="Company"
		)
		for customer_rule in (
			frappe._dict(idx=1, match_by="Region", customer_group="Commercial"),
			frappe._dict(idx=1, match_by="Type"),
		):
			settings = frappe._dict(
				enable_party_tax_id_check=1,
				customer_tax_id_rules=[customer_rule],
				supplier_tax_id_rules=[supplier_rule],
			)
			with self.subTest(rule=customer_rule):
				with self.assertRaises(frappe.ValidationError):
					NepalComplianceSettings._validate_party_tax_id_rules(settings)


CANDIDATES = "nepal_compliance.nepal_compliance.doctype.nepal_compliance_settings.nepal_compliance_settings.get_extra_field_candidates"


def essentials_row(idx, fieldname, document_type="Sales Invoice"):
	return frappe._dict(idx=idx, document_type=document_type, fieldname=fieldname)


class FakeSettings(frappe._dict):
	def get_doc_before_save(self):
		return self.get("_before")


class TestNepalEssentialsSettings(FrappeTestCase):
	@patch(CANDIDATES, return_value={"project": "Project"})
	def test_extra_field_gets_its_label(self, _candidates):
		row = essentials_row(1, "project")
		NepalComplianceSettings._validate_essentials_extra_fields(frappe._dict(essentials_extra_fields=[row]))
		self.assertEqual(row.field_label, "Project")

	@patch(CANDIDATES, return_value={"project": "Project"})
	def test_field_the_form_cannot_show_is_rejected(self, _candidates):
		settings = frappe._dict(essentials_extra_fields=[essentials_row(1, "customer")])
		with self.assertRaises(frappe.ValidationError):
			NepalComplianceSettings._validate_essentials_extra_fields(settings)

	@patch(CANDIDATES, return_value={"project": "Project"})
	def test_duplicate_extra_field_is_rejected(self, _candidates):
		settings = frappe._dict(essentials_extra_fields=[essentials_row(1, "project"), essentials_row(2, "project")])
		with self.assertRaises(frappe.ValidationError):
			NepalComplianceSettings._validate_essentials_extra_fields(settings)

	@patch(CANDIDATES, return_value={"project": "Project"})
	def test_same_field_on_two_forms_is_allowed(self, _candidates):
		rows = [essentials_row(1, "project"), essentials_row(2, "project", "Sales Order")]
		NepalComplianceSettings._validate_essentials_extra_fields(frappe._dict(essentials_extra_fields=rows))

	def test_layout_change_is_detected(self):
		before = FakeSettings(use_nepal_essentials_tab=1, essentials_extra_fields=[essentials_row(1, "project")])
		unchanged = FakeSettings(before, _before=before)
		ticked_off = FakeSettings(before, use_nepal_essentials_tab=0, _before=before)
		new_field = FakeSettings(before, essentials_extra_fields=[essentials_row(1, "cost_center")], _before=before)
		self.assertFalse(NepalComplianceSettings._form_layout_changed(unchanged))
		self.assertTrue(NepalComplianceSettings._form_layout_changed(ticked_off))
		self.assertTrue(NepalComplianceSettings._form_layout_changed(new_field))
		self.assertTrue(NepalComplianceSettings._form_layout_changed(FakeSettings(use_nepal_essentials_tab=1)))

	def test_removed_extra_fields_are_listed_by_form(self):
		before = FakeSettings(
			essentials_extra_fields=[essentials_row(1, "project"), essentials_row(2, "cost_center", "Sales Order")]
		)
		after = FakeSettings(essentials_extra_fields=[essentials_row(1, "project")], _before=before)
		self.assertEqual(NepalComplianceSettings._removed_essentials_fields(after), {"Sales Order": ["cost_center"]})
		self.assertEqual(NepalComplianceSettings._removed_essentials_fields(FakeSettings()), {})
