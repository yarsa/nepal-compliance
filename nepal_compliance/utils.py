import frappe
from frappe import _
from frappe.utils import flt 

def prevent_invoice_deletion(doc, method):
    frappe.throw(_(f"Deletion of {doc.name} is not allowed due to compliance rule."))

@frappe.whitelist()
def evaluate_tax_formula(formula, taxable_salary):
    try:
        taxable_salary = flt(taxable_salary)
        context = {
            'taxable_salary': taxable_salary,
            'if': lambda x, y, z: y if x else z
        }
        result = eval(formula, {"__builtins__": {}}, context)
        return flt(result)    
    except Exception as e:
        frappe.log_error(f"Tax Formula Evaluation Error: {str(e)}\nFormula: {formula}")
        return 0
    