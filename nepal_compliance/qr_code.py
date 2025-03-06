import qrcode
import frappe
from io import BytesIO
import base64

def create_qr_code(doc, method=None):
    if getattr(frappe.local, 'is_qr_code_updated', False):
        return

    if doc.doctype == 'Sales Invoice':
        contact_field = 'customer'  
    elif doc.doctype == 'Purchase Invoice':
        contact_field = 'supplier'  
    else:
        return
    
    contact = getattr(doc, contact_field)
    posting_date = doc.posting_date
    nepali_date = doc.nepali_date
    payment_due_date = doc.due_date
    tax_and_charges = doc.total_taxes_and_charges
    discount = doc.discount_amount
    grand_total = doc.grand_total

    qr_data = f""" 
    {contact_field.capitalize()}: {contact}
    Posting Date: {posting_date}
    Nepali Date: {nepali_date}
    Payment Due Date: {payment_due_date}
    Total Tax and Charges: {tax_and_charges}
    Discount Amount: {discount}
    Grand Total: {grand_total}
    """

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    if doc.qr_code and doc.qr_code.split(',')[1] == img_str:
        return doc.qr_code
    
    doc.qr_code = f"data:image/png;base64,{img_str}"
    frappe.local.is_qr_code_updated = True
    doc.save()

    frappe.msgprint(frappe._("QR code generated successfully for the invoice."))
    return doc.qr_code