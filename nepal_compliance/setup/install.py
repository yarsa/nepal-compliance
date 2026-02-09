import frappe
from frappe import delete_doc, _
from frappe.model.document import Document
from frappe.utils import nowdate
from typing import Optional

@frappe.whitelist()
def generate_test_masters(docname: Optional[str] = None) -> bool:
    if not docname:
        frappe.throw(_("Missing IRD Certification document name."))
    settings = frappe.get_doc("IRD Certification", docname)
    company_name = settings.company or "Test Pvt Ltd"
    customer_name = "Test Customer One"
    supplier_name = "Test Supplier One"

    masters_created = False

    try:
        if not frappe.db.exists("Company", company_name):
            abbr = "".join([word[0].upper() for word in company_name.split()[:3]])
            frappe.get_doc({
                "doctype": "Company",
                "company_name": company_name,
                "abbr": abbr,
                "default_currency": "NPR",
                "country": "Nepal",
                "email": "support@gmail.com",
                "tax_id": "682343213",
            }).insert(ignore_permissions=True)
            masters_created = True

        if not frappe.db.exists("Address", {"address_title": company_name}):
            frappe.get_doc({
                "doctype": "Address",
                "address_title": company_name,
                "address_line1": "Lalitpur Office, Kathmandu",
                "city": "Kathmandu",
                "country": "Nepal",
                "phone": "+977 9834234524",
                "is_your_company_address": 1,
                "links": [{"link_doctype": "Company", "link_name": company_name}]
            }).insert()
            masters_created = True

        if not frappe.db.exists("Item", "Test Item 1"):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": "Test Item 1",
                "item_name": "Test Item 1",
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 1
            }).insert()
            masters_created = True

        if not frappe.db.exists("Customer", customer_name):
            frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_group": "Commercial",
                "territory": "Nepal",
                "tax_id": "423423453"
            }).insert()
            masters_created = True

        if not frappe.db.exists("Address", {"address_title": customer_name}):
            frappe.get_doc({
                "doctype": "Address",
                "address_title": customer_name,
                "address_line1": "Lalitpur Office, Kathmandu",
                "city": "Kathmandu",
                "country": "Nepal",
                "phone": "+977 9834234524",
                "links": [{"link_doctype": "Customer", "link_name": customer_name}]
            }).insert()
            masters_created = True

        if not frappe.db.exists("Supplier", supplier_name):
            frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": supplier_name,
                "supplier_type": "Company",
                "tax_id": "234234234"
            }).insert()
            masters_created = True

        if not frappe.db.exists("Address", {"address_title": supplier_name}):
            frappe.get_doc({
                "doctype": "Address",
                "address_title": supplier_name,
                "address_line1": "Lalitpur Office, Kathmandu",
                "city": "Kathmandu",
                "country": "Nepal",
                "phone": "+977 9834234524",
                "links": [{"link_doctype": "Supplier", "link_name": supplier_name}]
            }).insert()
            masters_created = True

        frappe.db.commit()

        if masters_created:
            frappe.msgprint(_("Test masters created successfully. Now, generate test transactions."))
        else:
            frappe.msgprint(_("Test masters already exist."))

        return masters_created

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Error in generate_test_masters")
        frappe.throw(f"Failed to create test masters: {e}")

@frappe.whitelist()
def generate_test_transactions(docname: Optional[str] = None) -> bool:
    if not docname:
        frappe.throw(_("Missing IRD Certification document name."))
    try:
        doc = frappe.get_doc("IRD Certification", docname)
        company_name = doc.company or "Test Pvt Ltd"

        abbr = frappe.db.get_value("Company", company_name, "abbr")
        if not abbr:
            frappe.throw(f"Company '{company_name}' not found or has no abbreviation.")

        sales_tax_template = f"Nepal Tax - {abbr}"
        purchase_tax_template = f"Nepal Tax - {abbr}"

        if not frappe.db.exists("Sales Taxes and Charges Template", sales_tax_template):
            frappe.throw(f"Sales Taxes and Charges Template '{sales_tax_template}' not found.")
        if not frappe.db.exists("Purchase Taxes and Charges Template", purchase_tax_template):
            frappe.throw(f"Purchase Taxes and Charges Template '{purchase_tax_template}' not found.")

        def cleanup_duplicate_vat_rows(tax_template_name, doctype):
            tax_template = frappe.get_doc(doctype, tax_template_name)
            vat_rows = [tax for tax in tax_template.taxes if tax.account_head and "VAT" in (tax.account_head or "").upper()]
            if len(vat_rows) > 1:
                for tax in vat_rows[1:]:
                    tax_template.taxes.remove(tax)
                tax_template.save()
                frappe.msgprint(f"Removed duplicate VAT rows from {doctype} '{tax_template_name}'.")

        cleanup_duplicate_vat_rows(sales_tax_template, "Sales Taxes and Charges Template")
        cleanup_duplicate_vat_rows(purchase_tax_template, "Purchase Taxes and Charges Template")

        transactions_created = False

        warehouse = f"Stores - {abbr}"
        if not frappe.db.exists("Warehouse", warehouse):
            frappe.throw(f"Warehouse '{warehouse}' not found. Please create it first.")

        if not frappe.db.exists("Sales Invoice", {"customer": "Test Customer One", "company": company_name}):
            si = frappe.get_doc({
                "doctype": "Sales Invoice",
                "company": company_name,
                "customer": "Test Customer One",
                "posting_date": nowdate(),
                "tax_id": "423423453",
                "update_stock": 1,
                "set_warehouse": f"Stores - {abbr}",
                "taxes_and_charges": sales_tax_template,
                "items": [{
                    "item_code": "Test Item 1",
                    "qty": 2,
                    "rate": 1000,
                    "price_list_rate": 1000
                }],
            }).insert()

            sr = frappe.get_doc({
                "doctype": "Sales Invoice",
                "company": company_name,
                "customer": "Test Customer One",
                "is_return": 1,
                "return_against": si.name,
                "posting_date": nowdate(),
                "tax_id": "423423453",
                "taxes_and_charges": sales_tax_template,
                "reason": "For verification to start billing",
                "items": [{
                    "item_code": "Test Item 1",
                    "qty": -2,
                    "rate": 1000
                }],
            }).insert()
            transactions_created = True

        if not frappe.db.exists("Purchase Invoice", {"supplier": "Test Supplier One", "company": company_name}):
            pi = frappe.get_doc({
                "doctype": "Purchase Invoice",
                "company": company_name,
                "supplier": "Test Supplier One",
                "posting_date": nowdate(),
                "update_stock": 1,
                "set_warehouse": f"Stores - {abbr}",
                "taxes_and_charges": purchase_tax_template,
                "items": [{
                    "item_code": "Test Item 1",
                    "qty": 2,
                    "rate": 1000,
                    "price_list_rate": 1000
                }],
            }).insert()

            pr = frappe.get_doc({
                "doctype": "Purchase Invoice",
                "company": company_name,
                "supplier": "Test Supplier One",
                "is_return": 1,
                "return_against": pi.name,
                "reason": "For verification to start billing",
                "posting_date": nowdate(),
                "taxes_and_charges": purchase_tax_template,
                "items": [{
                    "item_code": "Test Item 1",
                    "qty": -2,
                    "rate": 1000
                }],
            }).insert()
            transactions_created = True

        if transactions_created and doc:
            doc.test_data_created = 1
            doc.save(ignore_permissions=True)

        frappe.db.commit()

        if transactions_created:
            frappe.msgprint(_("Test transactions created successfully."))
        else:
            frappe.msgprint(_("Test transactions already exist."))

        return transactions_created

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Error in generate_test_transactions")
        frappe.throw(f"Failed to create test transactions: {e}")


@frappe.whitelist()
def check_test_data_status(docname: Optional[str] = None) -> dict[str, bool]:
    if not docname:
        frappe.throw(_("Missing IRD Certification document name."))
    
    if not frappe.db.exists("IRD Certification", docname):
        frappe.throw(_("IRD Certification document {0} not found.").format(docname))
        
    settings = frappe.get_doc("IRD Certification", docname)
    company_name = settings.company or "Test Pvt Ltd"
    customer_name = "Test Customer One"
    supplier_name = "Test Supplier One"
    item_code = "Test Item 1"

    masters_exist = all([
        frappe.db.exists("Company", company_name),
        frappe.db.exists("Customer", customer_name),
        frappe.db.exists("Supplier", supplier_name),
        frappe.db.exists("Item", item_code)
    ])

    transactions_exist = any([
        frappe.db.exists("Sales Invoice", {"customer": customer_name, "company": company_name}),
        frappe.db.exists("Purchase Invoice", {"supplier": supplier_name, "company": company_name})
    ])

    return {
        "masters_created": masters_exist,
        "transactions_created": transactions_exist
    }