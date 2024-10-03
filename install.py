import frappe

from migration.custom_code.payroll.salary_component import create_salary_component
from migration.custom_code.payroll.income_tax_slab import create_income_tax_slab


def install():
    create_salary_component()
    create_income_tax_slab()
