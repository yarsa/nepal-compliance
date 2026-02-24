import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, today, flt, add_years
from nepal_compliance.api.employee_benefit_claim import get_max_amount_eligible


class TestEmployeeBenefitClaim(FrappeTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        company = frappe.get_all("Company", limit=1)
        if not company:
            frappe.throw("No Company found. ERPNext must be installed.")

        cls.company = company[0].name

    # Helper Factory Method to create Employee with specified parameters
    def create_employee(self, months_back=12, revised_salary=1000000, ctc=1200000):
        return frappe.get_doc({
            "doctype": "Employee",
            "first_name": "Test",
            "last_name": "Employee",
            "gender": "Male",
            "date_of_birth": add_years(today(), -30),
            "company": self.company,
            "date_of_joining": add_months(today(), -months_back),
            "revised_salary": revised_salary,
            "ctc": ctc,
        }).insert(ignore_permissions=True)

    # TEST CASES
    def test_employee_completed_12_months(self):
        """Employee >= 12 months should get 60% of base salary"""
        emp = self.create_employee(months_back=12)

        amount = get_max_amount_eligible(emp.name, today())
        expected = flt(1000000 * 0.6)

        self.assertEqual(amount, expected)

    def test_employee_less_than_12_months(self):
        """Employee with 6 months should get prorated amount"""
        emp = self.create_employee(months_back=6)

        amount = get_max_amount_eligible(emp.name, today())
        expected = flt((1000000 * 0.6 / 12) * 6)

        self.assertEqual(amount, expected)

    def test_employee_without_salary(self):
        """Employee without salary should return 0"""
        emp = self.create_employee(
            months_back=12,
            revised_salary=0,
            ctc=0
        )

        amount = get_max_amount_eligible(emp.name, today())
        self.assertEqual(amount, 0.0)

    def test_future_joining_date(self):
        """Future joining date should return 0"""
        emp = self.create_employee(
            months_back=-2,
            revised_salary=1000000
        )

        amount = get_max_amount_eligible(emp.name, today())
        self.assertEqual(amount, 0.0)
