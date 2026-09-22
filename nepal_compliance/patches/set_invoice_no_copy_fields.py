import frappe

from nepal_compliance.custom_field import create_custom_fields

NO_COPY_FIELDS = {
    "Sales Invoice": (
        "item_vat_detail",
        "cbms_status",
        "cbms_response",
        "customs_declaration_number",
        "customs_declaration_date",
        "customs_declaration_date_bs",
        "attach_sales_invoice",
    ),
    "Purchase Invoice": (
        "item_vat_detail",
        "customs_declaration_number",
        "attach_purchase_invoice",
    ),
}


def execute():
    """Mark per-invoice fields no_copy so Duplicate stops carrying them over.

    create_custom_fields only re-syncs label and permlevel on a field that already
    exists, so no_copy has to be set directly for sites that already have them.
    """
    create_custom_fields(quiet=True)

    for doctype, fieldnames in NO_COPY_FIELDS.items():
        for fieldname in fieldnames:
            name = frappe.db.exists(
                "Custom Field", {"dt": doctype, "fieldname": fieldname}
            )
            if name and not frappe.db.get_value("Custom Field", name, "no_copy"):
                frappe.db.set_value("Custom Field", name, "no_copy", 1)
        frappe.clear_cache(doctype=doctype)
