import frappe
from frappe import _

def prvent_invoice_deletion(doc, method):
    frappe.throw(_(f"Deletion of {doc.names} is not allowed due to compliance rule."))

#hoooks -> "Purchase invoice" : {"on_trash": "nepal_compliance.utils.prevent_invoice_deletion"}