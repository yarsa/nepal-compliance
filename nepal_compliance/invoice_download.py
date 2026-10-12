"""Merge the attached invoice copies of many Sales Invoices into one PDF download."""

from io import BytesIO

import frappe
from frappe import _
from pypdf import PdfWriter

COPY_FIELDS = {
    "tax_invoice": ("tax_invoice_attachment",),
    "invoice": ("invoice_attachment",),
    "both": ("tax_invoice_attachment", "invoice_attachment"),
}


@frappe.whitelist(methods=["POST"])
def download_attached_invoices(names: str | list, copies: str = "both"):
    """Download the chosen copies of the given invoices as one PDF.

    With both, every tax invoice comes first, then every invoice copy, each in
    posting order. Invoices the user may not read, and missing or non-PDF
    attachments, are left out.
    """
    if copies not in COPY_FIELDS:
        frappe.throw(_("Choose Tax Invoice, Invoice or Both."))
    fields = COPY_FIELDS[copies]
    invoices = frappe.get_list(
        "Sales Invoice",
        filters={"name": ["in", frappe.parse_json(names)]},
        fields=["name", *fields],
        order_by="posting_date asc, name asc",
        limit_page_length=0,
    )
    writer = PdfWriter()
    for field in fields:
        for invoice in invoices:
            content = _attached_pdf(invoice.name, invoice.get(field))
            if content:
                writer.append(BytesIO(content))
    if not writer.pages:
        frappe.throw(_("None of the selected invoices has that copy attached."))

    with BytesIO() as output:
        writer.write(output)
        frappe.local.response.filename = "sales-invoices-{0}.pdf".format(copies.replace("_", "-"))
        frappe.local.response.filecontent = output.getvalue()
        frappe.local.response.type = "download"


def _attached_pdf(invoice, file_url):
    """The content of the PDF attached to ``invoice`` at ``file_url``, if any."""
    if not (file_url or "").lower().endswith(".pdf"):
        return None
    name = frappe.db.get_value(
        "File",
        {"file_url": file_url, "attached_to_doctype": "Sales Invoice", "attached_to_name": invoice},
        "name",
    )
    return frappe.get_doc("File", name).get_content() if name else None
