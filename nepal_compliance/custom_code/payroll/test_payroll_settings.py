import frappe
from frappe.tests.utils import FrappeTestCase
from frappe import ValidationError
from nepal_compliance.custom_code.payroll.payroll_settings import modify_email_salary_slip_default

class TestModifyEmailSalarySlipDefault(FrappeTestCase):

    def setUp(self):
        # Ensure Payroll Settings exists for test
        if not frappe.db.exists("Payroll Settings", "Payroll Settings"):
            if not frappe.db.exists("DocType", "Payroll Settings"):
                # Create Payroll Settings DocType in test db if needed
                frappe.get_doc({
                    "doctype": "DocType",
                    "name": "Payroll Settings",
                    "module": "HR",
                    "custom": 1,
                    "fields": [
                        {"fieldname": "email_salary_slip_to_employee", "fieldtype": "Check"}
                    ]
                }).insert(ignore_permissions=True)

            # Create Payroll Settings document
            frappe.get_doc({
                "doctype": "Payroll Settings",
                "email_salary_slip_to_employee": 1
            }).insert(ignore_permissions=True)

    def tearDown(self):
        """ Cleanup test data
        Ensure DocType name is restored in case the negative test left it renamed """
        frappe.db.sql(
            "UPDATE tabDocType SET name='Payroll Settings' WHERE name='Payroll Settings Backup'"
        )
        frappe.clear_cache(doctype="Payroll Settings")
        if frappe.db.exists("Payroll Settings", "Payroll Settings"):
            frappe.delete_doc("Payroll Settings", "Payroll Settings", force=True)

    def test_modify_email_salary_slip_default_updates_field(self):
        # Should set email_salary_slip_to_employee = 0
        modify_email_salary_slip_default()

        doc = frappe.get_doc("Payroll Settings")
        self.assertEqual(doc.email_salary_slip_to_employee, 0)

    def test_modify_email_salary_slip_default_no_payroll_settings_doc(self):
        # Should raise ValidationError if Payroll Settings DocType missing
        # Remove Payroll Settings doc to simulate missing DocType
        if frappe.db.exists("Payroll Settings"):
            frappe.delete_doc("Payroll Settings", "Payroll Settings", force=True)

        # Temporarily rename DocType to simulate missing DocType
        frappe.db.sql("UPDATE tabDocType SET name='Payroll Settings Backup' WHERE name='Payroll Settings'")

        from unittest.mock import patch

        with patch("frappe.db.exists", return_value=False):
            with self.assertRaises(ValidationError):
                modify_email_salary_slip_default()
