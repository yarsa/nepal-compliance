import frappe

# def delete_salary_component():

#     salary_component_names = ["Basic Salary", "Grade Amount"]  

#     for name in salary_component_names:
#         if frappe.db.exists("Salary Component", name):
#             frappe.delete_doc("Salary Component", name)

from migration.install import create_salary_component  

def delete_salary_component():
    # Call create_salary_component to get the salary components
    salary_components = create_salary_component()  

    # Delete each specified salary component
    for name in salary_components:
        if frappe.db.exists("Salary Component", name):
            frappe.delete_doc("Salary Component", name)
        else:
            frappe.msgprint(f"Salary Component '{name}' does not exist.")