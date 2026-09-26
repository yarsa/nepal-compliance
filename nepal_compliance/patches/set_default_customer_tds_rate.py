import frappe


def execute():
    """Fill the Customer TDS Rate on sites whose settings were saved before the field existed."""
    if not frappe.db.get_single_value("Nepal Compliance Settings", "customer_tds_rate"):
        frappe.db.set_single_value("Nepal Compliance Settings", "customer_tds_rate", 1.5)
