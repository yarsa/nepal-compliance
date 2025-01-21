import frappe
import frappe.defaults

@frappe.whitelist()
def get_audit_trail_doctypes():
    return set(frappe.get_hooks("doctype_lists"))