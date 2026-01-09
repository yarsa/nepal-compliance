import frappe

def nepal_compliance_enabled() -> bool:
    try:
        settings = frappe.get_single("Nepal Compliance Settings")
        return bool(settings.enable_nepali_date)
    except Exception as e:
        frappe.log_error(f"Error checking Nepal Compliance settings: {e}", "Nepal Compliance Settings Check")
        return False
