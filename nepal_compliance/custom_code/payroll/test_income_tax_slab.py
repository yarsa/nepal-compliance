import frappe
from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_years, add_days, getdate
from frappe import _
import hashlib
from erpnext.accounts.utils import get_fiscal_year
from nepal_compliance.custom_code.payroll.income_tax_slab import (
    create_income_tax_slab_for_company,
    get_fiscal_year_for_company,
)


class TestIncomeTaxSlab(FrappeTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._created_fiscal_year = False
        cls._preexisting_income_tax_slab = False

        # Ensure at least one company exists
        company = frappe.get_all("Company", limit=1)
        if not company:
            frappe.throw(_("No Company found. ERPNext must be installed."))

        cls.company = company[0].name
        cls.currency = frappe.get_value("Company", cls.company, "default_currency")
        slab_name = f"{cls.company} - Income Tax Slab"
        cls._preexisting_income_tax_slab = bool(frappe.db.exists("Income Tax Slab", slab_name))

        # Create a Fiscal Year for this company if not exists
        # if not frappe.get_all("Fiscal Year", filters={"company": cls.company}):
        try:
            fiscal_year_data = get_fiscal_year(today(), company=cls.company, as_dict=True)
            if fiscal_year_data:
                cls.fiscal_year = frappe.get_doc("Fiscal Year", fiscal_year_data.name)
            else:
                raise ValueError("No fiscal year found")
        except (frappe.ValidationError, ValueError):
            _suffix = hashlib.md5(cls.company.encode()).hexdigest()[:6]
            cls.fiscal_year = frappe.get_doc({
                "doctype": "Fiscal Year",
                "year": f"_Test 2090-2091 {_suffix}",
                "year_start_date": today(),
                "year_end_date": add_days(add_years(today(), 1), -1),
                "companies": [{"company": cls.company}],
                "nepali_year_start_date": today(),
            }).insert(ignore_permissions=True)
            cls._created_fiscal_year = True

    @classmethod
    def tearDownClass(cls):
        if cls._created_fiscal_year and hasattr(cls, "fiscal_year") and cls.fiscal_year:
            frappe.delete_doc("Fiscal Year", cls.fiscal_year.name, force=1)
        # Cleanup Income Tax Slab created during the test class lifecycle
        slab_name = f"{cls.company} - Income Tax Slab"
        if not cls._preexisting_income_tax_slab and frappe.db.exists("Income Tax Slab", slab_name):
            frappe.delete_doc("Income Tax Slab", slab_name, force=1)
        super().tearDownClass()

    # Test Cases
    def test_get_fiscal_year_for_company(self):
    # Should return the fiscal year applicable to the company for today.
    fy = get_fiscal_year_for_company(self.company)
    self.assertIsNotNone(fy)
    # ERPNext FYs may be global (no company restriction) or company-specific;
    # a global FY applies to every company, so accept either.
    linked = [c.company for c in fy.companies]
    self.assertTrue(not linked or self.company in linked)
    self.assertLessEqual(getdate(fy.year_start_date), getdate(today()))
    self.assertGreaterEqual(getdate(fy.year_end_date), getdate(today()))

    def test_create_income_tax_slab(self):
        #Should create income tax slab with correct slab count
        create_income_tax_slab_for_company(
            self.company,
            self.fiscal_year.year_start_date,
            self.currency,
            self.fiscal_year.nepali_year_start_date
        )

        slab_name = f"{self.company} - Income Tax Slab"
        self.assertTrue(frappe.db.exists("Income Tax Slab", slab_name))

        slab_doc = frappe.get_doc("Income Tax Slab", slab_name)

        # We defined 5 slabs in the source file
        self.assertEqual(len(slab_doc.slabs), 5)

    def test_idempotent_slab_creation(self):
        #Should not duplicate slabs when running creation twice
        create_income_tax_slab_for_company(
            self.company,
            self.fiscal_year.year_start_date,
            self.currency,
            self.fiscal_year.nepali_year_start_date
        )

        # Run again
        create_income_tax_slab_for_company(
            self.company,
            self.fiscal_year.year_start_date,
            self.currency,
            self.fiscal_year.nepali_year_start_date
        )

        slab_name = f"{self.company} - Income Tax Slab"
        slab_doc = frappe.get_doc("Income Tax Slab", slab_name)

        # Should still be 5 (no duplication)
        self.assertEqual(len(slab_doc.slabs), 5)

    def test_no_fiscal_year(self):
    with patch(
        "nepal_compliance.custom_code.payroll.income_tax_slab.get_fiscal_year",
        side_effect=frappe.exceptions.ValidationError,
    ):
        self.assertIsNone(get_fiscal_year_for_company("Any Company"))
