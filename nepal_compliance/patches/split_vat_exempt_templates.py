import frappe

from nepal_compliance.utils import get_or_create_vat_exempt_template


def execute():
    """Create side-specific templates while retaining ambiguous legacy records."""
    settings = frappe.get_single("Nepal Compliance Settings")
    for row in settings.get("vat_accounts") or []:
        if not row.company:
            continue
        for side, account in (
            ("sales", row.sales_vat_account),
            ("purchase", row.purchase_vat_account),
        ):
            if account:
                get_or_create_vat_exempt_template(row.company, account, side)
