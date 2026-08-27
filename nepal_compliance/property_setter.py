import frappe

PROPERTY_SETTERS = [
    {
        "doc_type": "Purchase Invoice",
        "field_name": "supplier_invoice_details",
        "property": "collapsible",
        "property_type": "Check",
        "value": "0",
    },
]


def create_property_setters():
    for ps in PROPERTY_SETTERS:
        existing = frappe.db.exists(
            "Property Setter",
            {"doc_type": ps["doc_type"], "field_name": ps["field_name"], "property": ps["property"]},
        )
        if existing:
            if frappe.db.get_value("Property Setter", existing, "value") != ps["value"]:
                frappe.db.set_value("Property Setter", existing, "value", ps["value"])
            continue
        frappe.get_doc(
            {
                "doctype": "Property Setter",
                "doctype_or_field": "DocField",
                "module": "Nepal Compliance",
                **ps,
            }
        ).insert(ignore_permissions=True)
    frappe.clear_cache(doctype="Purchase Invoice")
