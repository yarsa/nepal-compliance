import frappe
from frappe import delete_doc, _

@frappe.whitelist()
def clear_test_data(docname=None):
    if not docname:
        frappe.throw(_("Missing IRD Certification document name."))

    if not frappe.db.exists("IRD Certification", docname):
        frappe.throw(_("IRD Certification document {0} not found.").format(docname))

    settings = frappe.get_doc("IRD Certification", docname)
    company_name = settings.company or "Test Pvt Ltd"

    cleanup_test_data(company_name)

    frappe.msgprint(_("All test masters and transactions for {0} have been deleted successfully.").format(company_name))


def safe_delete(doctype, name):
    try:
        if frappe.db.exists(doctype, name):
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            delete_doc(doctype, name, force=True)
        return True
    except frappe.LinkExistsError:
        frappe.logger().info(f"Skipping delete for {doctype} {name} due to links.")
        return False
    except Exception as e:
        frappe.logger().error(f"Failed to delete {doctype} {name}: {str(e)}")
        return False


def cleanup_test_data(company_name):
    customer_name = "Test Customer One"
    supplier_name = "Test Supplier One"
    item_code = "Test Item 1"

    try:
        sales_invoices = frappe.get_all(
            "Sales Invoice",
            filters={"customer": customer_name, "company": company_name},
            pluck="name"
        )
        for si in sales_invoices:
            safe_delete("Sales Invoice", si)

        purchase_invoices = frappe.get_all(
            "Purchase Invoice",
            filters={"supplier": supplier_name, "company": company_name},
            pluck="name"
        )
        for pi in purchase_invoices:
            safe_delete("Purchase Invoice", pi)

        safe_delete("Item", item_code)

        addresses = frappe.get_all(
            "Address",
            filters={"address_title": ["in", [customer_name, supplier_name, company_name]]},
            pluck="name"
        )
        for addr in addresses:
            safe_delete("Address", addr)

        safe_delete("Customer", customer_name)
        safe_delete("Supplier", supplier_name)

        if company_name == "Test Pvt Ltd":
            safe_delete("Company", company_name)
        
        if frappe.db.exists("IRD Certification"):
            settings = frappe.get_doc("IRD Certification")
            settings.test_data_created = 0
            settings.save(ignore_permissions=True)

    except Exception as e:
        frappe.db.rollback()
        frappe.logger().error(f"Cleanup failed for company {company_name}: {str(e)}")
        raise
