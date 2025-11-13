import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.safe_exec import safe_eval
from frappe.model.naming import make_autoname

def prevent_invoice_deletion(doc, method):
    if (doc.docstatus == 1):
        frappe.throw(_(f"Deletion of {doc.name} is not allowed due to compliance rule."))

def custom_autoname(doc, method):
    try:
        full_series = doc.naming_series
        if not full_series:
            naming_field = frappe.get_meta(doc.doctype).get_field("naming_series")
            if naming_field and naming_field.options:
                options = [opt.strip() for opt in naming_field.options.split("\n") if opt.strip()]
                if options:
                    full_series = options[0]
                else:
                    frappe.throw(_("No valid naming series found for {0}").format(doc.doctype))
            else:
                frappe.throw(_("No naming series found for {0}").format(doc.doctype))
        max_attempts = 50
        for attempt in range(max_attempts):
            proposed_name = make_autoname(full_series, doc=doc)
            if not proposed_name:
                frappe.throw(_("Failed to generate name using series {0}").format(full_series))
             
            if not frappe.db.exists(doc.doctype, proposed_name):
                doc.name = proposed_name
                return

        frappe.throw(_("Could not generate unique name after {0} attempts").format(max_attempts))
    except Exception as e:
        frappe.log_error(f"Custom autoname error: {str(e)}")
        raise

@frappe.whitelist()
def evaluate_tax_formula(formula, taxable_salary):
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
    if doc.get("__islocal") and doc.is_opening == "Yes":
        if doc.doctype == "Purchase Invoice":
            if doc.supplier and not doc.vat_number:
                try:
                    supplier_vat = frappe.db.get_value("Supplier", doc.supplier, "supplier_vat_number")
                    if supplier_vat:
                        doc.vat_number = supplier_vat
                except Exception as e:
                    frappe.log_error(f"Error fetching supplier VAT: {str(e)}")
            if doc.company and not doc.customer_vat_number:
                try:
                    company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                    if company_vat:
                        doc.customer_vat_number = company_vat
                except Exception as e:
                    frappe.log_error(f"Error fetching company VAT: {str(e)}")
        elif doc.doctype == "Sales Invoice":
            if doc.customer and not doc.vat_number:
                customer_vat = frappe.db.get_value("Customer", doc.customer, "customer_vat_number")
                if customer_vat:
                    doc.vat_number = customer_vat
            if doc.company and not doc.supplier_vat_number:
                company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                if company_vat:
                    doc.supplier_vat_number = company_vat

def load_nepali_date(doc, method):
    if not hasattr(doc, "nepali_date") or not hasattr(doc, "posting_date"):
        return

    posting_date_str = str(doc.posting_date).strip()
    nepali_date_str = str(doc.nepali_date).strip() if doc.nepali_date else ""

    if nepali_date_str and posting_date_str != nepali_date_str:
        doc.nepali_date = None

def bill_no_required(doc, method):
    if doc.doctype != "Purchase Invoice":
        return
    
    if not doc.get("bill_no") or not str(doc.bill_no).strip():
        frappe.throw(_("<b>Supplier Invoice No</b> is mandatory before submitting a Purchase Invoice. This is required for auditing."))