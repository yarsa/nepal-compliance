import frappe

def execute():
    """
    Marks specific salary components as income tax components if they exist.
    
    Iterates over the predefined salary component names "income_tax_married" and "income_tax_unmarried". For each, if the component exists in the database, sets its `is_income_tax_component` field to 1. Logs an informational message if a component is not found.
    """
    component_names = ["income_tax_married", "income_tax_unmarried"]
    
    for name in component_names:
        component = frappe.db.exists("Salary Component", name)
        if component:
            frappe.db.set_value("Salary Component", name, "is_income_tax_component", 1)
            frappe.db.commit()
        else:
            frappe.logger().info(f"Salary Component '{name}' not found during patch.")