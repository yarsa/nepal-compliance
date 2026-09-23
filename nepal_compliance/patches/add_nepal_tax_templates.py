import frappe

from nepal_compliance.tax_templates import sync_nepal_tax_templates


def execute():
    """Create the managed Nepal tax templates on existing sites (idempotent)."""
    settings = frappe.get_single("Nepal Compliance Settings")
    for row in settings.get("vat_accounts") or []:
        if not row.company:
            continue
        sync_nepal_tax_templates(
            row.company,
            row.sales_vat_account,
            row.purchase_vat_account,
            row.get("excise_account"),
        )
