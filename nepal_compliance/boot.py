import frappe

def get_boot_info(bootinfo):
    if frappe.session.user != "Guest":
        frappe.clear_cache(user=frappe.session.user)

        try:
            user_doc = frappe.get_doc("User", frappe.session.user)
            bootinfo["use_ad_date"] = bool(user_doc.get("use_ad_date", 0))
        except Exception as e:
            frappe.log_error(f"Failed to retrieve User document for boot info: {str(e)}")
            bootinfo["use_ad_date"] = False

        try:
            settings = frappe.get_single("Nepal Compliance Settings")
            bootinfo["nepal_compliance"] = {
                "date_format": settings.date_format or "YYYY-MM-DD"
            }
        except Exception as e:
            frappe.log_error(f"Failed to retrieve Nepal Compliance Settings for boot info: {str(e)}")
            bootinfo["nepal_compliance"] = {
                "date_format": "YYYY-MM-DD"
            }