import frappe 

def get_boot_info(bootinfo):
    if frappe.session.user != "Guest":
        frappe.clear_cache(user = frappe.session.user)
        user_doc = frappe.get_doc("User", frappe.session.user)
        bootinfo["user"]["use_ad_date"] = user_doc.get("use_ad_date", 0)