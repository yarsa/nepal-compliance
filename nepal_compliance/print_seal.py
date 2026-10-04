"""Company stamp and user signature for invoice print formats.

Both images are private files that only System Managers (and the uploader, or
the signing user for their own signature) can download.
"""

import frappe

SETTINGS = "Nepal Compliance Settings"


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

