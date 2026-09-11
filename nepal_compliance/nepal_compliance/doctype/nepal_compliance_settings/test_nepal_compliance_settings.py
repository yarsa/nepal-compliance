# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and Contributors
# For license information, please see LICENSE at the root of this repository

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
