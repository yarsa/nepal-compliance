import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def on_cancel(self):
        allowed_roles = ("Accounts Manager",)
        user_roles = frappe.get_roles(frappe.session.user)
        if not any(role in allowed_roles for role in user_roles):
            role_name = ", ".join(allowed_roles)
            frappe.throw(_("You cannot cancel <b>{0}</b>, Only allowed for <b>{1}</b>. Please create a Return / Credit Note instead.").format(self.name, role_name))

        super().on_cancel()
