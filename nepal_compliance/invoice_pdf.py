"""Attach the PDF of each submitted Sales Invoice.

Runs on on_change, which Frappe calls on submit only after every app's
on_submit has finished. Rendered through Frappe's printview like any print, so
the Access Log records it. A VAT-registered company gets the TAX INVOICE copy in Tax Invoice and the
INVOICE copy in Invoice; any other company gets the whole PDF in Attach Sales
Invoice. When that fails, nothing is attached and the invoice is tagged.
"""

import re
from io import BytesIO

import frappe
from frappe import _
from frappe.desk.doctype.tag.tag import DocTags
from frappe.utils import cint, strip_html
from pypdf import PdfReader, PdfWriter

SETTINGS = "Nepal Compliance Settings"
NOT_ATTACHED_TAG = "Invoice PDF Not Attached"
VAT_FIELDS = (("tax_invoice_attachment", "tax-invoice"), ("invoice_attachment", "invoice"))
PAN_FIELDS = (("attach_sales_invoice", None),)


def attach_invoice_pdf(doc, method=None):
    """Sales Invoice on_change, on submit only: attach the PDF in the company's print format.

    Uses the company's row in Print Format by Company. Skipped for a manual (hand
    bill) invoice, whose hand bill is the original, and when the target fields
    already hold a file. Never blocks the submission.
    """
    if getattr(doc, "_action", None) != "submit" or (doc.get("manual_invoice_no") or "").strip():
        return
    row = frappe.db.get_value(
        "Nepal Compliance Company Print Format",
        {"parent": SETTINGS, "parenttype": SETTINGS, "company": doc.company},
        ["print_format", "attach_invoice_pdf_on_submit", "vat_registered"],
        as_dict=True,
    ) or {}
    if not cint(row.get("attach_invoice_pdf_on_submit")):
        return
    vat_registered = cint(row.get("vat_registered"))
    fields = VAT_FIELDS if vat_registered else PAN_FIELDS
    if any(doc.get(field) for field, _suffix in fields):
        return

    print_format = row.print_format
    try:
        pdf = frappe.get_print(doc.doctype, doc.name, print_format, as_pdf=True)
        parts = split_tax_invoice(pdf) if vat_registered else [pdf]
    except Exception:
        _not_attached(doc, _("Its PDF could not be made in print format {0}.").format(frappe.bold(print_format)))
        return
    if not parts:
        _not_attached(
            doc,
            _("Print format {0} does not print a TAX INVOICE followed by an INVOICE copy. Use VAT Invoice - Standard.").format(
                frappe.bold(print_format)
            ),
            with_traceback=False,
        )
        return

    frappe.db.savepoint("attach_invoice_pdf")
    try:
        urls = {field: _save_file(doc, field, suffix, part) for (field, suffix), part in zip(fields, parts)}
    except Exception:
        frappe.db.rollback(save_point="attach_invoice_pdf")
        _not_attached(doc, _("Its PDF could not be saved."))
        return
    doc.db_set(urls, update_modified=False)


def clear_not_attached_tag(doc, method=None):
    """Sales Invoice on_update_after_submit: drop the tag once a file is attached."""
    if any(doc.get(field) and doc.has_value_changed(field) for field, _suffix in VAT_FIELDS + PAN_FIELDS):
        tags = DocTags(doc.doctype)
        if NOT_ATTACHED_TAG in tags.get_tags(doc.name).split(","):
            tags.remove(doc.name, NOT_ATTACHED_TAG)


def _not_attached(doc, reason, with_traceback=True):
    """Tag the invoice, log why, and tell the user its PDF was not attached."""
    DocTags(doc.doctype).add(doc.name, NOT_ATTACHED_TAG)
    # Without a message, log_error records the current traceback.
    frappe.log_error(
        f"Invoice PDF not attached to {doc.name}", None if with_traceback else strip_html(reason),
        reference_doctype=doc.doctype, reference_name=doc.name,
    )
    frappe.msgprint(
        _("Sales Invoice {0} was submitted without its PDF attached. {1} It is tagged {2}.").format(
            frappe.bold(doc.name), reason, frappe.bold(NOT_ATTACHED_TAG)
        ),
        title=_("Invoice PDF Not Attached"),
        indicator="orange",
    )


def _save_file(doc, field, suffix, pdf):
    name = doc.name.replace(" ", "-").replace("/", "-")
    file = frappe.get_doc({
        "doctype": "File",
        "file_name": f"{name}-{suffix}.pdf" if suffix else f"{name}.pdf",
        "attached_to_doctype": doc.doctype,
        "attached_to_name": doc.name,
        "attached_to_field": field,
        "is_private": 1,
        "content": pdf,
    })
    file.insert(ignore_permissions=True)
    return file.file_url


def split_tax_invoice(pdf):
    """Return [tax invoice PDF, invoice PDF], or None unless pdf holds both copies.

    Page titles are whole lines, matched ignoring case and spacing ("Invoice No" never matches).
    """
    reader = PdfReader(BytesIO(pdf))
    titles = [
        {re.sub(r"\s+", "", line).upper() for line in (page.extract_text() or "").splitlines()}
        for page in reader.pages
    ]
    if not titles or "TAXINVOICE" not in titles[0]:
        return None
    start = next((i for i, lines in enumerate(titles) if "INVOICE" in lines and "TAXINVOICE" not in lines), None)
    if start is None:
        return None
    return [_pages(reader.pages[:start]), _pages(reader.pages[start:])]


def _pages(pages):
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    with BytesIO() as output:
        writer.write(output)
        return output.getvalue()
