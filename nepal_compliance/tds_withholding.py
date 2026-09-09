import frappe
from frappe.permissions import add_permission, update_permission_property


DOCTYPE = "Tax Withholding Category"
PERMLEVEL = 1
ROLES = ("Accounts Manager", "System Manager")


def setup_tds_on_taxable_amount_permissions():
    """Allow Accounts Manager (and System Manager) to edit permlevel-1 TDS base field."""
    for role in ROLES:
        if not frappe.db.exists(
            "Custom DocPerm",
            {"parent": DOCTYPE, "role": role, "permlevel": PERMLEVEL, "if_owner": 0},
        ):
            add_permission(DOCTYPE, role, permlevel=PERMLEVEL, ptype="read")
        for ptype in ("read", "write"):
            update_permission_property(DOCTYPE, role, PERMLEVEL, ptype, 1)
    frappe.clear_cache(doctype=DOCTYPE)


def enable_tds_on_taxable_amount_for_existing_categories():
    """Default existing Tax Withholding Categories to calculate TDS on taxable amount."""
    if not frappe.db.has_column(DOCTYPE, "calculate_tds_on_taxable_amount"):
        return
    frappe.db.sql(
        """
        UPDATE `tabTax Withholding Category`
        SET calculate_tds_on_taxable_amount = 1
        WHERE IFNULL(calculate_tds_on_taxable_amount, 0) = 0
        """
    )
