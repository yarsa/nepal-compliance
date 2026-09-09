import frappe

DEFAULT_COUNTRY = "Nepal"


def resolve_ird_country(stored_country=None, address_country=None) -> str:
    """Return the frozen invoice country, linked-address country, or Nepal."""
    for country in (stored_country, address_country):
        if country and str(country).strip():
            return str(country).strip()
    return DEFAULT_COUNTRY


def is_foreign_country(country) -> bool:
    """Return whether a normalized country should be treated as foreign."""
    return resolve_ird_country(country).casefold() != DEFAULT_COUNTRY.casefold()


def set_invoice_party_country(doc, method=None) -> None:
    """Freeze the selected customer or supplier address country on a draft invoice."""
    if doc.doctype == "Sales Invoice":
        address_name = doc.get("customer_address")
    elif doc.doctype == "Purchase Invoice":
        address_name = doc.get("supplier_address")
    else:
        return

    # Submitted invoices can only be changed through IRD Country Correction.
    if doc.docstatus:
        return

    address_country = (
        frappe.db.get_value("Address", address_name, "country")
        if address_name
        else None
    )
    doc.ird_party_country = resolve_ird_country(address_country=address_country)
