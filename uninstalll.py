import frappe

def delete_salary_component():

    salary_component_names = ["Basic Salary", "Grade Amount"]  

    for name in salary_component_names:
        if frappe.db.exists("Salary Component", name):
            frappe.delete_doc("Salary Component", name)