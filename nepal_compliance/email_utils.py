import frappe
from frappe import _

@frappe.whitelist()
def send_invoice_email(docname, doctype, auto_send=False):
    """
    Send an invoice email notification with a print format attachment for a submitted Purchase or Sales Invoice.
    
    If the invoice is a Purchase Invoice, the email is sent to the supplier; if a Sales Invoice, to the customer. The function constructs a detailed HTML message with invoice information and attaches a PDF print format. If required recipient email or default outgoing email account is missing and `auto_send` is False, a warning is shown and the email is not sent. The email is sent asynchronously via the background queue.
    
    Parameters:
        docname (str): The name of the invoice document to email.
        doctype (str): The type of the invoice document ("Purchase Invoice" or "Sales Invoice").
        auto_send (bool, optional): If True, suppresses warnings and shows a confirmation message after queuing the email. Defaults to False.
    """
    doc = frappe.get_doc(doctype, docname)
    if doc.docstatus != 1:
        frappe.throw(_("Email can only be sent after submission."))

    def get_invoice_email_details(doc, doctype):
        if doctype == "Purchase Invoice":
            recipient_email = frappe.db.get_value("Supplier", doc.supplier, "supplier_email_address")
            print_format = frappe.db.get_value("Property Setter", 
                                               {"property": "default_print_format", "doc_type": doctype}, 
                                               "value") or "Purchase Invoice Nepal Compliance"
            subject = f"Purchase Invoice {doc.name} Approved - {doc.company}"
            message = f"""
            <p>Dear Supplier,</p>
            <p>We are pleased to inform you that your purchase invoice <strong>{doc.name}</strong> has been successfully approved by {doc.company}.</p>
            <p>Details of the approved invoice are as follows:</p>
            <ul>
            <li><strong>Invoice Number:</strong> {doc.name}</li>
            <li><strong>Invoice Date:</strong> {doc.posting_date}</li>
            <li><strong>Nepali Date:</strong> {doc.nepali_date}</li>
            <li><strong>Due Date:</strong> {doc.due_date}</li>
            <li><strong>Discount Amount:</strong> {doc.discount_amount}</li>
            <li><strong>Total Tax and Charges:</strong> {doc.total_taxes_and_charges}</li>
            <li><strong>Total Amount:</strong> {doc.grand_total}</li>
            </ul>
            
            <p>Attached to this email, you will find the print format for your reference: <strong>{print_format}</strong></p>
            
            <p>Thank you for your continued business.</p>
            
            <p>Best regards,<br>
            The {doc.company} Team</p>
            """
        elif doctype == "Sales Invoice":
            recipient_email = frappe.db.get_value("Customer", doc.customer, "customer_email_address")
            print_format = frappe.db.get_value("Property Setter", 
                                               {"property": "default_print_format", "doc_type": doctype}, 
                                               "value") or "Sales Invoice Nepal Compliance"
            subject = f"Sales Invoice {doc.name} Approved - {doc.company}"
            message = f"""
            <p>Dear Customer,</p>
            <p>We are pleased to inform you that your sales invoice <strong>{doc.name}</strong> has been successfully approved by {doc.company}.</p>
            <p>Details of the approved invoice are as follows:</p>
            <ul>
            <li><strong>Invoice Number:</strong> {doc.name}</li>
            <li><strong>Invoice Date:</strong> {doc.posting_date}</li>
            <li><strong>Nepali Date:</strong> {doc.nepali_date}</li>
            <li><strong>Due Date:</strong> {doc.due_date}</li>
            <li><strong>Discount Amount:</strong> {doc.discount_amount}</li>
            <li><strong>Total Tax and Charges:</strong> {doc.total_taxes_and_charges}</li>
            <li><strong>Total Amount:</strong> {doc.grand_total}</li>
            </ul>
            
            <p>Attached to this email, you will find the print format for your reference: <strong>{print_format}</strong></p>
            
            <p>Thank you for your continued business.</p>
            
            <p>Best regards,<br>
            The {doc.company} Team</p>
            """
        else:
            recipient_email = None
            subject = None
            message = None
            print_format = None
        
        return recipient_email, subject, message, print_format

    recipient_email, subject, message, print_format = get_invoice_email_details(doc, doctype)

    if not recipient_email :
        if not auto_send:
            frappe.msgprint(
            _("No email address found for this Supplier/Customer. Configure it in Supplier/Customer Doctype."),
            indicator="orange"
        )
        return

    email_account = frappe.get_value("Email Account", {"default_outgoing": 1}, "email_id")
    if not email_account:
        if not auto_send:
            frappe.msgprint(
            _("No default email account found. Configure one in Email Account settings."),
            indicator="orange"
        )
        return

    attachments = [frappe.attach_print(doctype, doc.name, print_format=print_format, file_name=doc.name)]

    try:
        frappe.enqueue(
            queue="short",
            method=frappe.sendmail,
            recipients=recipient_email,
            sender=email_account,
            subject=subject,
            message=message,
            attachments=attachments,
            reference_doctype=doctype,
            reference_name=doc.name
            )
        if auto_send:
            frappe.msgprint(_("Email has been queued for sending."))
    except Exception as e:
        frappe.logger().error(f"Error while sending email: {str(e)}")

@frappe.whitelist()
def check_email_setup(doctype, docname):
    """
    Check if both recipient email and default outgoing email account are configured for a given invoice document.
    
    Returns:
        bool: True if both the recipient's email address and a default outgoing email account are set up; False otherwise.
    """
    doc = frappe.get_doc(doctype, docname)
    email = None
    if doctype == "Purchase Invoice":
        email = frappe.db.get_value("Supplier", doc.supplier, "supplier_email_address")
    elif doctype == "Sales Invoice":
        email = frappe.db.get_value("Customer", doc.customer, "customer_email_address")

    email_account = frappe.get_value("Email Account", {"default_outgoing": 1}, "email_id")

    if not email:
        frappe.msgprint(
            _("No email address found for this Supplier/Customer. Configure it in Supplier/Customer Doctype."),
            indicator="orange",
            alert=True
        )
        return False

    if not email_account:
        frappe.msgprint(
            _("No default email account found. Configure one in Email Account settings."),
            indicator="orange",
            alert=True
        )
        return False

    return True

def send_email_on_submit(doc, method):
    send_invoice_email(doc.name, doc.doctype, auto_send=True)