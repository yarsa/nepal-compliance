"""Non-VAT registered Nepal supplier rules."""

import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_default_address


def _is_nepal(country):
    return str(country or "").strip().casefold() == "nepal"


def supplier_billing_country(supplier, address_name=None, supplier_country=None):
    address_name = address_name or get_default_address("Supplier", supplier)
    address_country = (
        frappe.db.get_value("Address", address_name, "country") if address_name else None
    )
    return address_country or supplier_country


def validate_non_vat_supplier(doc, method=None):
    """Restrict the PAN marker to Nepal Company suppliers."""
    if not doc.get("is_not_vat_registered"):
        return
    if doc.get("supplier_type") != "Company":
        frappe.throw(
            _("Only a Company supplier can be marked as not VAT registered.")
        )
    country = supplier_billing_country(
        doc.name, supplier_country=doc.get("country")
    )
    if not _is_nepal(country):
        frappe.throw(
            _("A non-VAT registered supplier must have a Nepal billing address or country.")
        )


def set_pan_bill_from_supplier(doc, method=None):
    """Mark eligible Purchase Orders/Invoices without clearing manual flags."""
    if doc.doctype not in ("Purchase Order", "Purchase Invoice") or not doc.get(
        "supplier"
    ):
        return
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    if not settings.get("enable_supplier_pan_automation"):
        return
    supplier = frappe.db.get_value(
        "Supplier",
        doc.supplier,
        ["supplier_type", "country", "is_not_vat_registered"],
        as_dict=True,
    )
    if (
        not supplier
        or supplier.supplier_type != "Company"
        or not supplier.is_not_vat_registered
    ):
        return
    country = supplier_billing_country(
        doc.supplier,
        doc.get("supplier_address"),
        supplier.country,
    )
    if _is_nepal(country):
        doc.is_pan_or_abbreviated_bill = 1
