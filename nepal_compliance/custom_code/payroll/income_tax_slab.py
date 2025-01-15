import frappe 
from frappe import _

company = frappe.get_all("Company", fields=["name"])
@frappe.whitelist()
def create_income_tax_slab():
    doc = frappe.new_doc("Income Tax Slab")
    doc.name = "Ignore Slab Test"
    doc.disabled = 0
    doc.effective_from = "2025-07-16"
    doc.company = company
    doc.currency = "NPR"
    doc.standard_tax_exemption_amount = ""
    doc.allow_tax_exemption = 0
    doc.append("slabs", {
        "from_amount" : "Rs 0.00",
        "to_amount" : "Rs 1.00",
        "percent_deduction" : "0%",
        "condition" : ""
    })
    # doc.Docstatus = 1
    doc.save()
    doc.reload()
    doc.submit()