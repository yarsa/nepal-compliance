import frappe

def get_boot_info(bootinfo):
    if frappe.session.user == "Guest":
        return

    try:
        user_doc = frappe.get_cached_doc("User", frappe.session.user)
        bootinfo["use_ad_date"] = bool(user_doc.get("use_ad_date", 0))
    except Exception:
        frappe.log_error(
            "Failed to retrieve User document for boot info",
            "Nepal Compliance"
        )
        bootinfo["use_ad_date"] = False

    try:
        settings = frappe.get_cached_doc("Nepal Compliance Settings")
        bootinfo["nepal_compliance"] = {
            "date_format": settings.date_format or "YYYY-MM-DD"
        }
    except Exception:
        frappe.log_error(
            "Failed to retrieve Nepal Compliance Settings for boot info",
            "Nepal Compliance"
        )
        bootinfo["nepal_compliance"] = {
            "date_format": "YYYY-MM-DD"
        }