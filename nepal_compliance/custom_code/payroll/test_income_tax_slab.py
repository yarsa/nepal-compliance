import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_years, add_days
from frappe import _
from erpnext.accounts.utils import get_fiscal_year
from nepal_compliance.custom_code.payroll.income_tax_slab import (
    create_income_tax_slab_for_company,
    get_fiscal_year_for_company,
)


class TestIncomeTaxSlab(FrappeTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Ensure at least one company exists
        company = frappe.get_all("Company", limit=1)
        if not company:
            frappe.throw(_("No Company found. ERPNext must be installed."))

        cls.company = company[0].name
        cls.currency = frappe.get_value("Company", cls.company, "default_currency")

        # Create a Fiscal Year for this company if not exists
        # if not frappe.get_all("Fiscal Year", filters={"company": cls.company}):
        try:
            fiscal_year_data = get_fiscal_year(today(), company=cls.company, as_dict=True)
            if fiscal_year_data:
                cls.fiscal_year = frappe.get_doc("Fiscal Year", fiscal_year_data.name)
            else:
                raise ValueError("No fiscal year found")
        except (frappe.ValidationError, ValueError):
            cls.fiscal_year = frappe.get_doc({
                "doctype": "Fiscal Year",
                "year": "2090-2091",
                "year_start_date": today(),
                "year_end_date": add_days(add_years(today(), 1), -1),
                "companies": [{"company": cls.company}],
                "nepali_year_start_date": today(),
            }).insert(ignore_permission=True)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'fiscal_year') and cls.fiscal_year:
            frappe.delete_doc("Fiscal Year", cls.fiscal_year.name, force=1)
        # Cleanup Income Tax Slab created during the test class lifecycle
        slab_name = f"{cls.company} - Income Tax Slab"
        if frappe.db.exists("Income Tax Slab", slab_name):
            frappe.delete_doc("Income Tax Slab", slab_name, force=1)
        super().tearDownClass()

    # Test Cases
    def test_get_fiscal_year_for_company(self):
        #Should return fiscal year document for company
        fy = get_fiscal_year_for_company(self.company)
        self.assertIsNotNone(fy)
        self.assertTrue(
            any(c.company == self.company for c in fy.companies)
        )

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

        # We defined 8 slabs in the source file
        self.assertEqual(len(slab_doc.slabs), 8)

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

        # Should still be 8 (no duplication)
        self.assertEqual(len(slab_doc.slabs), 8)

    def test_no_fiscal_year(self):
        #Should return None when fiscal year does not exist
        non_existing_company = "Invalid Company"
        fy = get_fiscal_year_for_company(non_existing_company)
        self.assertIsNone(fy)
