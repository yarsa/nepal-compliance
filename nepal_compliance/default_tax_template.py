import frappe


DEFAULT_PURCHASE_TAX_TEMPLATE = "Nepal Tax - YT"


def set_default_purchase_tax_template():
    """Make Nepal Tax - YT the default Purchase Taxes and Charges Template."""
    if not frappe.db.exists(
        "Purchase Taxes and Charges Template",
        {"name": DEFAULT_PURCHASE_TAX_TEMPLATE, "disabled": 0},
    ):
        return

    template = frappe.get_doc(
        "Purchase Taxes and Charges Template", DEFAULT_PURCHASE_TAX_TEMPLATE
    )
    if template.is_default:
        return
    if frappe.db.exists(
        "Purchase Taxes and Charges Template",
        {"company": template.company, "is_default": 1, "disabled": 0},
    ):
        return

    template.is_default = 1
    template.save(ignore_permissions=True)
