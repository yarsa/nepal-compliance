import frappe

from nepal_compliance.custom_code.payroll.income_tax_slab import create_income_tax_slabs_for_all_companies
from nepal_compliance.custom_field import create_custom_fields
from nepal_compliance.custom_code.payroll.payroll_settings import modify_email_salary_slip_default
from nepal_compliance.custom_code.leave_type.leave_type import setup_default_leave_types
from nepal_compliance.custom_code.print_settings import print_cancelled_invoice
from nepal_compliance.custom_code.payroll.salary_structure import create_salary_structures

def install():
    create_custom_fields()
    create_income_tax_slabs_for_all_companies()
    modify_email_salary_slip_default()
    # setup_default_leave_types()
    print_cancelled_invoice()
    frappe.enqueue("nepal_compliance.custom_code.payroll.salary_structure.create_salary_structures", queue="default", job_name="Create Salary Structures")
