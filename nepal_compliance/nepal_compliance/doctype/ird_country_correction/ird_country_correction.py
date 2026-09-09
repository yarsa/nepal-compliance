# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import escape_html, get_link_to_form, now_datetime

from nepal_compliance.ird_country import resolve_ird_country

INVOICE_ADDRESS_FIELDS = {
    "Sales Invoice": "customer_address",
    "Purchase Invoice": "supplier_address",
}


def get_invoice_country(invoice_doc) -> str:
    """Resolve an invoice's snapshot or selected party-address country."""
    address_field = INVOICE_ADDRESS_FIELDS[invoice_doc.doctype]
    address_name = invoice_doc.get(address_field)
    address_country = (
        frappe.db.get_value("Address", address_name, "country")
        if address_name
        else None
    )
    return resolve_ird_country(invoice_doc.get("ird_party_country"), address_country)


def get_permitted_invoice(invoice_type: str, invoice_name: str):
    """Return a submitted invoice the user may read and submit."""
    if invoice_type not in INVOICE_ADDRESS_FIELDS:
        frappe.throw(_("Only Sales Invoice and Purchase Invoice can be corrected."))

    invoice_doc = frappe.get_doc(invoice_type, invoice_name)
    invoice_doc.check_permission("read")
    if not frappe.has_permission(invoice_type, "submit", doc=invoice_doc):
        frappe.throw(
            _("You need Submit permission for {0} to correct its IRD country.").format(
                invoice_type
            ),
            frappe.PermissionError,
        )
    if invoice_doc.docstatus != 1:
        frappe.throw(_("Only submitted invoices can be corrected."))
    return invoice_doc


@frappe.whitelist()
def get_invoice_details(invoice_type: str, invoice: str) -> dict:
    """Return current country and company for the correction form."""
    invoice_doc = get_permitted_invoice(invoice_type, invoice)
    return {
        "company": invoice_doc.company,
        "current_country": get_invoice_country(invoice_doc),
    }


class IRDCountryCorrection(Document):
    def validate(self):
        """Load the authoritative current country and reject no-op corrections."""
        if self.reason:
            self.reason = self.reason.strip()
        if not self.invoice_type or not self.invoice:
            return

        invoice_doc = get_permitted_invoice(self.invoice_type, self.invoice)
        self.company = invoice_doc.company
        self.current_country = get_invoice_country(invoice_doc)

        if (
            self.new_country
            and self.new_country.casefold() == self.current_country.casefold()
        ):
            frappe.throw(_("New Country must be different from Current Country."))

    def before_submit(self):
        """Apply the correction atomically and add a detailed invoice comment."""
        invoice_doc = get_permitted_invoice(self.invoice_type, self.invoice)
        current_country = get_invoice_country(invoice_doc)
        if current_country.casefold() != self.current_country.casefold():
            frappe.throw(
                _(
                    "The invoice country changed after this correction was saved. "
                    "Reload and review it before submitting."
                )
            )
        if self.new_country.casefold() == current_country.casefold():
            frappe.throw(_("New Country must be different from Current Country."))

        self.corrected_by = frappe.session.user
        self.corrected_on = now_datetime()
        frappe.db.set_value(
            self.invoice_type,
            self.invoice,
            "ird_party_country",
            self.new_country,
        )

        invoice_doc.add_comment(
            "Info",
            _(
                "IRD party country changed from <b>{0}</b> to <b>{1}</b> by {2} "
                "on {3} through {4}.<br><b>Reason:</b> {5}"
            ).format(
                escape_html(current_country),
                escape_html(self.new_country),
                escape_html(frappe.session.user),
                escape_html(str(self.corrected_on)),
                get_link_to_form(self.doctype, self.name),
                escape_html(self.reason),
            ),
        )

    def before_cancel(self):
        """Keep submitted correction records immutable."""
        frappe.throw(
            _("Submitted IRD Country Corrections cannot be cancelled."),
            frappe.PermissionError,
        )
