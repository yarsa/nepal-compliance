import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class CustomSalesInvoice(SalesInvoice):
    def on_cancel(self):
        frappe.throw(_(f"You cannot cancel {self.name}. Please create a Return / Credit Note instead."))
