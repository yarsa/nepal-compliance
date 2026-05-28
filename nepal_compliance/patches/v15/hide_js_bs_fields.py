import frappe

def execute():
    custom_fields = frappe.db.sql(
        """
        SELECT name, dt, fieldname
        FROM `tabCustom Field`
        WHERE
            module = 'Nepal Compliance'
            AND (
                fieldname LIKE '%_bs'
                OR fieldname LIKE 'nepali_%'
                OR fieldname LIKE '%_nepali_%'
                OR fieldname LIKE '%nepali%'
            )
        """,
        as_dict=True,
    )

    if not custom_fields:
        return

    for cf in custom_fields:
        frappe.db.set_value(
            "Custom Field",
            cf.name,
            {
                "hidden": 1,
                "no_copy": 1
            }
        )

    # Clear meta cache
    affected_doctypes = set(cf.dt for cf in custom_fields)
    for dt in affected_doctypes:
        frappe.clear_cache(doctype=dt)
