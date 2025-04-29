import frappe
from frappe.utils import getdate, nowdate
from frappe import _

def validate_backdate_and_sequence(doc, method):

    if not frappe.db.exists("Nepal Compliance Settings"):
        return
    try:
        settings = frappe.get_single("Nepal Compliance Settings")

    except Exception:
        return


    allowed_doctypes = [d.doctypes for d in settings.restricted_doctypes]
    if doc.doctype not in allowed_doctypes:
        return

    user_roles = frappe.get_roles(frappe.session.user)
    override_roles = [r.role for r in settings.allowed_role]
    can_override = bool(set(user_roles).intersection(override_roles))

    max_days = settings.max_backdate_days_allowed or 0
    if max_days > 0:
        today = getdate(nowdate())
        posting_date = getdate(doc.posting_date)
        delta_days = (today - posting_date).days

        if delta_days > max_days and not can_override:
            frappe.throw(_(
                f"Back-dated entries are only allowed within {max_days} day(s). "
                f"This {doc.doctype} is {delta_days} day(s) old."
            ))

    if settings.prevent_out_of_sequence_doctype_submission and not can_override:
        future_invoice_exists = frappe.db.exists(
            doc.doctype,
            {
                "docstatus": 1,
                "posting_date": [">", doc.posting_date],
                "company": doc.company
            }
        )

        if future_invoice_exists:
            frappe.throw(_(
                f"You cannot submit this {doc.doctype} because a newer document "
                f"has already been submitted with a later posting date. "
                f"Please adjust the date or contact an authorized approver."
            ))

