import frappe
def print_cancelled_invoice():
    try:
        if not frappe.db.exists("Print Settings"):
            if not frappe.db.exists("DocType", "Print Settings"):
                frappe.log_error(
                    message=error_msg,
                )
                raise frappe.ValidationError(error_msg)
        doc = frappe.get_doc("Print Settings")
        doc.allow_print_for_cancelled = 1
        doc.save(ignore_permissions=True)
        frappe.clear_cache()
        frappe.db.commit()
                
    except Exception as e:
        error_msg = f"Error updating Payroll Settings value: {str(e)}"
        raise e