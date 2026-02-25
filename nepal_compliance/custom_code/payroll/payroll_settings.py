import frappe
from frappe import _
def modify_email_salary_slip_default():
    try:
        if not frappe.db.exists("DocType", "Payroll Settings"):
            error_msg = _("Payroll Settings DocType not found. HRMS app may not be installed.")
            frappe.log_error(
                message=error_msg,
                title="HRMS App Not Installed"
            )
            raise frappe.ValidationError(error_msg)
        doc = frappe.get_doc("Payroll Settings")
        doc.email_salary_slip_to_employee = 0
        doc.save(ignore_permissions=True)
        frappe.clear_cache()
        frappe.db.commit()
                
    except Exception as e:
        error_msg = f"Error updating Payroll Settings value: {str(e)}"
        raise e
