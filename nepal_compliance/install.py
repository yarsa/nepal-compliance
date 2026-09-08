import frappe

from nepal_compliance.custom_code.payroll.income_tax_slab import create_income_tax_slabs_for_all_companies
from nepal_compliance.custom_field import create_custom_fields
from nepal_compliance.property_setter import create_property_setters
from nepal_compliance.custom_code.payroll.payroll_settings import modify_email_salary_slip_default
from nepal_compliance.custom_code.leave_type.leave_type import setup_default_leave_types
from nepal_compliance.custom_code.print_settings import print_cancelled_invoice
from nepal_compliance.custom_code.payroll.salary_component import create_multiple_salary_components
from nepal_compliance.default_tax_template import set_default_purchase_tax_template
from nepal_compliance.tds_withholding import setup_tds_on_taxable_amount_permissions

def install():
    """Create custom fields, property setters, and default Nepal Compliance data."""
    create_custom_fields()
    create_property_setters()
    set_default_purchase_tax_template()
    setup_tds_on_taxable_amount_permissions()
    create_multiple_salary_components()
    create_income_tax_slabs_for_all_companies()
    modify_email_salary_slip_default()
    setup_default_leave_types()
    print_cancelled_invoice()

def before_tests():
    """Clear cache and run ERPNext's before_tests hook for this app's test site."""
    frappe.clear_cache()
    from erpnext.setup.utils import before_tests as erpnext_before_tests
    erpnext_before_tests()