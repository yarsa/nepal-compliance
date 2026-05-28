import frappe

def execute():
    component_names = ["income_tax_married", "income_tax_unmarried"]
    
    for name in component_names:
        component = frappe.db.exists("Salary Component", name)
        if component:
            frappe.db.set_value("Salary Component", name, "is_income_tax_component", 1)
            frappe.db.commit()
        else:
            frappe.logger().info(f"Salary Component '{name}' not found during patch.")