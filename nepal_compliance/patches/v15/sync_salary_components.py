import frappe

def execute():
    from nepal_compliance.custom_code.payroll.salary_component import update_salary_component_formulas
    from nepal_compliance.custom_code.payroll.salary_component import create_multiple_salary_components
    create_multiple_salary_components()
    update_salary_component_formulas()