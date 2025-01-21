import frappe

@frappe.whitelist()
def get_purchase_sales_doctype():
    return set(frappe.get_hooks("purchase_sales"))