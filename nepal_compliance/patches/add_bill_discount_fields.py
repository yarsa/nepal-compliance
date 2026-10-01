import frappe

from nepal_compliance.custom_field import create_custom_fields
from nepal_compliance.utils import set_taxable_amounts


def execute():
    """Create the bill Subtotal and Discount fields and fill them on existing bills (idempotent)."""
    create_custom_fields(quiet=True)
    frappe.clear_cache()

    for doctype in ("Sales Invoice", "Purchase Invoice", "Sales Order"):
        # only bills with items have a Subtotal, so 0 means not filled yet
        names = frappe.get_all(doctype, filters={"docstatus": ["<", 2], "bill_subtotal": 0}, pluck="name")
        for count, name in enumerate(names, start=1):
            doc = frappe.get_doc(doctype, name)
            set_taxable_amounts(doc, None)
            frappe.db.set_value(
                doctype,
                name,
                {"bill_subtotal": doc.bill_subtotal, "taxable_discount": doc.taxable_discount},
                update_modified=False,
            )
            if count % 100 == 0:
                frappe.db.commit()
