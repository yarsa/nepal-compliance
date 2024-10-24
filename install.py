import frappe

from migration.custom_code.payroll.salary_component import create_salary_component
from migration.custom_code.payroll.income_tax_slab import create_income_tax_slab
from migration.custom_code.leave_type.leave_type import create_leave_type

def install():
    create_salary_component()
    create_income_tax_slab()
    create_leave_type(**leave_type)
