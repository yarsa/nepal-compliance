import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.safe_exec import safe_eval

def prevent_invoice_deletion(doc, method):
    frappe.throw(_(f"Deletion of {doc.name} is not allowed due to compliance rule."))

@frappe.whitelist()
def evaluate_tax_formula(formula, taxable_salary):
    """
    Safely evaluates a tax calculation formula using the provided taxable salary.
    
    Parameters:
    	formula (str): The tax formula to evaluate, expressed as a string.
    	taxable_salary (float or str): The taxable salary value to use in the formula.
    
    Returns:
    	float: The result of the evaluated formula, or 0 if evaluation fails.
    """
    try:
        taxable_salary = flt(taxable_salary)
        context = {
            'taxable_salary': taxable_salary,
            'if': lambda x, y, z: y if x else z
        }
        result = safe_eval(formula, {"__builtins__": {}}, context)
        return flt(result)    
    except Exception as e:
        frappe.log_error(f"Tax Formula Evaluation Error: {str(e)}\nFormula: {formula}")
        return 0


def set_vat_numbers(doc, method):
    """
    Assigns VAT numbers to new opening invoice documents based on related party and company records.
    
    For new "Purchase Invoice" and "Sales Invoice" documents marked as opening entries, this function populates missing VAT number fields by retrieving values from the associated Supplier, Customer, or Company records.
    """
    if doc.get("__islocal") and doc.is_opening == "Yes":
  
        if doc.doctype == "Purchase Invoice":
            if doc.supplier and not doc.vat_number:
                supplier_vat = frappe.db.get_value("Supplier", doc.supplier, "supplier_vat_number")
                if supplier_vat:
                    doc.vat_number = supplier_vat

            if doc.company and not doc.customer_vat_number:
                company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                if company_vat:
                    doc.customer_vat_number = company_vat

        elif doc.doctype == "Sales Invoice":
            if doc.customer and not doc.vat_number:
                customer_vat = frappe.db.get_value("Customer", doc.customer, "customer_vat_number")
                if customer_vat:
                    doc.vat_number = customer_vat

            if doc.company and not doc.supplier_vat_number:
                company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                if company_vat:
                    doc.supplier_vat_number = company_vat
