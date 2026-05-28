# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from PyPDF2 import PdfMerger
from PIL import Image
import io, os, zipfile
from frappe import _
from typing import Optional

class IRDCertification(Document):
    pass

def _safe_file_path(file_url):
    site_base = os.path.realpath(frappe.get_site_path())
    requested_path = os.path.realpath(os.path.join(site_base, file_url.lstrip("/")))

    if not requested_path.startswith(site_base + os.sep):
        frappe.throw(_("Invalid file path"))

    return requested_path

def _get_sorted_ird_files(docname):
    frappe.get_doc("IRD Certification", docname).check_permission("read")
    
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "IRD Certification",
            "attached_to_name": docname
        },
        fields=["name", "file_name", "file_url", "attached_to_field"],
        limit_page_length=0
    )
    if not files:
        frappe.throw(_("No attached files found for this record."))
    
    def get_index(f):
        try:
            if f.attached_to_field and f.attached_to_field.startswith("checklist_"):
                return int(f.attached_to_field.split("_")[1])
        except (ValueError, IndexError, AttributeError):
            pass
        return 9999
    
    files.sort(key=get_index)
    return files

@frappe.whitelist(allow_guest=False)
def download_all_ird_files_stream(docname: str) -> io.BytesIO:
    files = _get_sorted_ird_files(docname)

    zip_buffer = io.BytesIO()
    files_added = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            file_doc = frappe.get_doc("File", f.name)
            file_path = _safe_file_path(file_doc.file_url)

            if os.path.exists(file_path):
                zf.write(file_path, f.file_name)
                files_added += 1
            else:
                frappe.logger().warning(f"File not found: {f.file_name} at {file_path}")

    if files_added == 0:
        frappe.throw(_("No valid files found to include in the ZIP archive."))

    zip_buffer.seek(0)
    filename = f"IRD_All_{now_datetime().strftime('%Y%m%d_%H%M%S')}.zip"

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = zip_buffer.read()
    frappe.local.response.type = "download"
    frappe.local.response.content_type = "application/zip"

@frappe.whitelist(allow_guest=False)
def generate_combined_ird_pdf_stream(docname: str) -> Optional[bytes]:
    files = _get_sorted_ird_files(docname)

    merger = PdfMerger()
    files_merged = 0
    merged_bytes = None

    try:
        for f in files:
            fdoc = frappe.get_doc("File", f.name)
            path = _safe_file_path(fdoc.file_url)
            ext = os.path.splitext(f.file_name)[1].lower()

            try:
                if ext == ".pdf":
                    merger.append(path)
                    files_merged += 1
                elif ext in [".jpg", ".jpeg", ".png"]:
                    img = Image.open(path).convert("RGB")
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PDF")
                    img_bytes.seek(0)
                    merger.append(img_bytes)
                    files_merged += 1
            except (OSError, IOError, ValueError) as e:
                frappe.logger().error(f"Error processing {f.file_name}: {e}")
        
        if files_merged == 0:
            frappe.throw(_("No valid PDF or image files found to merge."))

        merged_bytes = io.BytesIO()
        merger.write(merged_bytes)
        merged_bytes.seek(0)

    finally:
        merger.close()
        
    filename = f"IRD_Combined_{now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"

    if not merged_bytes:
        frappe.throw(_("Failed to generate combined PDF"))

    frappe.local.response.filename = filename
    frappe.local.response.filecontent = merged_bytes.read()
    frappe.local.response.type = "download"
    frappe.local.response.content_type = "application/pdf"
