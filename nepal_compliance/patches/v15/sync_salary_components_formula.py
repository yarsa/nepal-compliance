import frappe

def execute():
    from nepal_compliance.custom_code.payroll.salary_component import update_salary_component_formulas
    update_salary_component_formulas()