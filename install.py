import frappe
from migration.api import create_income_tax_slab
from migration.custom_code.payroll.salary_component import create_salary_component


def install():
    create_salary_component()
    create_income_tax_slab()
