"""Retire VAT Invoice - Standard (Bulk), which differed from VAT Invoice - Standard
only in its column widths. Settings that used it move to the standard format, and
it is disabled rather than deleted, so prints that name it stay valid."""

import frappe

SETTINGS = "Nepal Compliance Settings"
BULK = "VAT Invoice - Standard (Bulk)"
STANDARD = "VAT Invoice - Standard"


def execute():
    if not frappe.db.exists("Print Format", BULK):
        return
    frappe.db.set_value(
        "Nepal Compliance Company Print Format", {"parent": SETTINGS, "print_format": BULK}, "print_format", STANDARD
    )
    # One stamp and signature row per format and company: where the standard
    # format already has a row for that company, the bulk row is dropped.
    seal_rows = lambda print_format: frappe.get_all(
        "Nepal Compliance Print Seal",
        filters={"parent": SETTINGS, "print_format": print_format},
        fields=["name", "company"],
    )
    taken = {row.company or "" for row in seal_rows(STANDARD)}
    for row in seal_rows(BULK):
        if (row.company or "") in taken:
            frappe.db.delete("Nepal Compliance Print Seal", {"name": row.name})
        else:
            frappe.db.set_value("Nepal Compliance Print Seal", row.name, "print_format", STANDARD)
            taken.add(row.company or "")
    frappe.db.set_value(
        "Property Setter",
        {"doc_type": "Sales Invoice", "property": "default_print_format", "value": BULK},
        "value",
        STANDARD,
    )
    frappe.db.set_value("Print Format", BULK, "disabled", 1)
    frappe.clear_cache(doctype="Sales Invoice")
