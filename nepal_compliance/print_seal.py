"""Company stamp and user signature for invoice print formats.

Both images are private files that only System Managers (and the uploader, or
the signing user for their own signature) can download. Print formats never
link to the files: get_print_seal reads them on the server and embeds them in
the rendered page as data URIs, so anyone allowed to print the invoice sees the
seal without being able to fetch the image itself.
"""

import base64
import mimetypes

import frappe
from frappe.utils import cint, flt

SETTINGS = "Nepal Compliance Settings"
SEAL_FIELDS = [
    "company", "show_stamp", "stamp_original_size", "stamp_height", "stamp_offset_x", "stamp_offset_y",
    "show_signature", "signature_original_size", "signature_height", "signature_offset_x", "signature_offset_y",
]


def secure_company_stamp(doc, method=None):
    """Company validate: make the stamp private and attach it to the settings.

    Files are downloadable by anyone who can read the document they are attached
    to, and most roles can read Company, so the stamp is attached to Nepal
    Compliance Settings (System Manager only) instead.
    """
    if doc.get("company_stamp"):
        doc.company_stamp = _make_private(doc.company_stamp, doc, "company_stamp", (SETTINGS, SETTINGS, None))


def detach_company_stamp(doc, method=None):
    """Company on_change: drop the attachment Frappe re-creates on every save.

    frappe's attach_files_to_document (an on_update hook for every doctype)
    attaches each Attach field's file back to the document, which would make the
    stamp downloadable by Company readers again. Only the record is removed; the
    file itself stays, attached to the settings.
    """
    url = doc.get("company_stamp")
    if not url or not frappe.db.exists("File", {"file_url": url, "attached_to_doctype": SETTINGS}):
        return
    frappe.db.delete("File", {
        "file_url": url,
        "attached_to_doctype": "Company",
        "attached_to_name": doc.name,
        "attached_to_field": "company_stamp",
    })


def secure_user_signature(doc, method=None):
    """User validate: keep the signature private, attached to its own User.

    Only System Managers and the user themselves can read a User record, so
    attaching it there already limits downloads to them.
    """
    if doc.get("signature_image"):
        doc.signature_image = _make_private(doc.signature_image, doc, "signature_image")


def _make_private(file_url, doc, fieldname, attach_to=None):
    """Make the File behind file_url private (moving it on disk) and return its URL.

    attach_to, as (doctype, name, field), re-attaches it elsewhere.
    """
    if attach_to and frappe.db.exists(
        "File", {"file_url": file_url, "is_private": 1,
                 "attached_to_doctype": attach_to[0], "attached_to_name": attach_to[1]}
    ):
        return file_url

    names = frappe.get_all(
        "File",
        filters={"file_url": file_url, "attached_to_doctype": doc.doctype, "attached_to_name": doc.name,
                 "attached_to_field": fieldname},
        pluck="name",
    ) or frappe.get_all(
        # A file picked from the library may still be unattached; never take over
        # a file that belongs to some other document.
        "File", filters={"file_url": file_url, "attached_to_doctype": ["is", "not set"]}, pluck="name", limit=1
    )
    if not names:
        return file_url

    file = frappe.get_doc("File", names[0])
    if file.is_private and not attach_to:
        return file_url

    file.is_private = 1
    if attach_to:
        file.attached_to_doctype, file.attached_to_name, file.attached_to_field = attach_to
    # Saving with is_private set moves the file from public/ to private/ on disk,
    # so no public copy is left behind.
    file.save(ignore_permissions=True)
    return file.file_url


def get_print_seal(doc, print_format):
    """Jinja: the stamp and signature a print format should draw for doc.

    Reads the format's row for the document's company in Nepal Compliance
    Settings > Printing, else its row without a company. Returns empty values
    for unsubmitted documents, when no row applies, or when the current user may
    not print the document.
    """
    seal = frappe._dict(stamp=None, stamp_style="", signature=None, signature_style="")
    if cint(doc.get("docstatus")) != 1 or not frappe.has_permission(doc.doctype, "print", doc=doc):
        return seal

    rows = frappe.get_all(
        "Nepal Compliance Print Seal",
        filters={"parent": SETTINGS, "parenttype": SETTINGS, "print_format": print_format},
        fields=SEAL_FIELDS,
    )
    row = pick_seal_row(rows, doc.get("company"))
    if not row:
        return seal

    if row.show_stamp:
        seal.stamp = _image_data_uri(frappe.db.get_value("Company", doc.get("company"), "company_stamp"))
        seal.stamp_style = _image_style(row, "stamp", default_height=22, base_bottom=-8)
    if row.show_signature and doc.get("signed_by"):
        seal.signature = _image_data_uri(frappe.db.get_value("User", doc.signed_by, "signature_image"))
        seal.signature_style = _image_style(row, "signature", default_height=12, base_bottom=1)
    return seal


def pick_seal_row(rows, company):
    """The row for ``company``, else the one that applies to every company."""
    return next((r for r in rows if r.company == company), None) or next((r for r in rows if not r.company), None)


def get_sales_invoice_print_format(company):
    """The Sales Invoice print format set for ``company`` in the settings, if any."""
    if not company:
        return None
    return frappe.db.get_value(
        "Nepal Compliance Company Print Format",
        {"parent": SETTINGS, "parenttype": SETTINGS, "company": company},
        "print_format",
    )


def _image_style(row, prefix, default_height, base_bottom):
    """Inline CSS for one image: height (unless original size), offsets in mm."""
    style = []
    if not cint(row.get(f"{prefix}_original_size")):
        style.append(f"height: {flt(row.get(f'{prefix}_height')) or default_height}mm;")
    offset_x = flt(row.get(f"{prefix}_offset_x"))
    # The stamp is pinned by its left edge; the signature is centred, so it moves by margin.
    style.append(f"{'left' if prefix == 'stamp' else 'margin-left'}: {offset_x}mm;")
    style.append(f"bottom: {base_bottom - flt(row.get(f'{prefix}_offset_y'))}mm;")
    return " ".join(style)


def _image_data_uri(file_url):
    """Read an image File from disk, whatever the current user's file access."""
    if not file_url:
        return None
    mime_type = mimetypes.guess_type(file_url)[0]
    if not mime_type or not mime_type.startswith("image/"):
        return None
    name = frappe.db.get_value("File", {"file_url": file_url}, "name")
    if not name:
        return None
    try:
        content = frappe.get_doc("File", name).get_content()
    except Exception:
        frappe.log_error(title="Print seal image could not be read")
        return None
    if isinstance(content, str):
        content = content.encode()
    return f"data:{mime_type};base64,{base64.b64encode(content).decode()}"
