import frappe

from nepal_compliance.custom_code.payroll.salary_component import create_salary_component

def delete_salary_component():
    # Calling create_salary_component to get the salary components
    salary_components = create_salary_component()  

    # Deleting each specified salary component
    for name in salary_components:
        if frappe.db.exists("Salary Component", name):
            frappe.delete_doc("Salary Component", name)
        else:
            frappe.msgprint(f"Salary Component '{name}' does not exist.")