import frappe
import requests
import json
from frappe.utils.password import get_decrypted_password
from frappe.utils.background_jobs import enqueue
from frappe import _
from datetime import datetime

class CBMSIntegration:
    def __init__(self, doc):
        self.doc = doc
        self.cbms_settings = None
        self.api_url = None
        self.invoice_payload = None

    def is_cbms_configured(self):

        try:
            self.cbms_settings = frappe.get_doc("CBMS Settings")
            return all([
                self.cbms_settings.user_name,
                self.cbms_settings.get_password("password"),  
                self.cbms_settings.panvat_no,
                self.cbms_settings.sales_api_url,  
                self.cbms_settings.credit_note_api_url  
            ])
        except frappe.DoesNotExistError:
            return False

    def prepare_payload(self):

        try:
            if not self.doc.nepali_date:
                frappe.throw(_("Nepali date is missing in the Sales Invoice."))

            fiscal_year = frappe.db.get_value(
                "Fiscal Year",
                {"year_start_date": ["<=", self.doc.posting_date], "year_end_date": [">=", self.doc.posting_date]},
                "name"
            )
            if not fiscal_year:
                frappe.log_error(f"Fiscal Year not found for posting date: {self.doc.posting_date}", "CBMS API Error")
                return None

            try:
                date_obj = datetime.strptime(self.doc.nepali_date, "%Y-%m-%d")
                invoice_date = date_obj.strftime("%Y.%m.%d")
            except ValueError as e:
                frappe.log_error(f"Invalid Nepali date format: {self.doc.nepali_date}. Error: {str(e)}", "CBMS API Error")
                return None
            except AttributeError as e:
                frappe.msgprint(_("Nepali Date Missing"))
                frappe.log_error("Nepali date is missing in the Sales Invoice.", "CBMS API Error")
                return None

            datetimeclient = frappe.utils.now()
            datetime_obj = datetime.strptime(datetimeclient, "%Y-%m-%d %H:%M:%S.%f")
            formatted_datetime = datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

            self.invoice_payload = {
                "username": self.cbms_settings.user_name,
                "password": self.cbms_settings.get_password("password"),
                "seller_pan": self.cbms_settings.panvat_no,
                "buyer_pan": self.doc.vat_number,  
                "fiscal_year": fiscal_year,
                "total_sales": self.doc.grand_total if not self.doc.is_return else abs(self.doc.grand_total), 
                "taxable_sales_vat": abs(self.doc.net_total) if self.doc.is_return else (self.doc.net_total if self.doc.discount_amount else abs(self.doc.total)),
                "vat": self.doc.total_taxes_and_charges if not self.doc.is_return else abs(self.doc.total_taxes_and_charges),  
                "excisable_amount" : 0.0, 
                "excise" : 0.0,
                "taxable_sales_hst" : 0.0,
                "hst" : 0.0, 
                "amount_for_esf" : 0.0, 
                "esf" : 0.0, 
                "export_sales" : 0.0,
                "tax_exempted_sales" : 0.0,
                "isrealtime" : True, 
                "datetimeclient": formatted_datetime
            }

            if self.doc.is_return:
                self.invoice_payload.update({
                    "ref_invoice_number": self.doc.return_against,
                    "credit_note_date": invoice_date,
                    "credit_note_number": self.doc.name,
                    "reason_for_return": self.doc.reason
                })
            else:
                self.invoice_payload.update({
                    "invoice_number": self.doc.name,
                    "invoice_date": invoice_date
                })
            
            return self.invoice_payload
        except Exception as e:
            frappe.log_error(f"Error preparing payload: {str(e)}", "CBMS API Error")
            return None

    def send_to_cbms(self, doc):
        self.doc = doc
        
        try:
            if not self.is_cbms_configured():
                raise Exception(_("CBMS settings are not properly configured."))

            api_url = self.cbms_settings.credit_note_api_url if self.doc.is_return else self.cbms_settings.sales_api_url
            if not api_url:
                frappe.log_error(_("API URL is not configured for CBMS.", "CBMS API Error"))
                return {"message": _("API URL is not configured for CBMS."), "status": "failed"}

            payload = self.prepare_payload()
            if not payload:
                raise Exception(_("Failed to prepare payload."))

            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)

            if response.status_code == 200:
                doc.reload()
                doc.cbms_status = "Success"
                doc.cbms_response = json.dumps(response.status_code)
                doc.save(ignore_permissions=True)
                frappe.db.commit()
                return {"message": _("Invoice/Return successfully posted to CBMS"), "status": "success"}

            else:
                doc.reload()
                doc.cbms_status = "Failed"
                doc.cbms_response = response.text
                doc.save(ignore_permissions=True)
                frappe.db.commit()
                error_msg = f"CBMS API Error: {response.text}"
                frappe.log_error(error_msg, "CBMS API")
                return {"message": _("Error occurred"), "status": "failed", "error": error_msg}
        except requests.exceptions.RequestException as e:
            doc.reload()
            doc.cbms_status = "Failed"
            doc.cbms_response = str(e)
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.log_error(f"Failed to connect to CBMS API: {str(e)}", "CBMS API")
            return {"message": _("Failed to connect to CBMS API"), "status": "failed", "error": str(e)}
        except Exception as e:
            doc.reload()
            doc.cbms_status = "Failed"
            doc.cbms_response = str(e)
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.log_error(f"Unexpected error while sending data to CBMS: {str(e)}", "CBMS API")
            return {"message": _("Unexpected error occurred"), "status": "failed", "error": str(e)}

@frappe.whitelist()
def post_sales_invoice_or_return_to_cbms(doc_name, method=None):
    
    try:
        doc = frappe.get_doc("Sales Invoice", doc_name)
        if not doc:
            frappe.throw(_("Sales Invoice not found"))

        cbms_integration = CBMSIntegration(doc)
        if not cbms_integration.is_cbms_configured():
            frappe.throw(_("CBMS settings are not configured properly."))
            return {"message": _("CBMS settings not configured")}
        
        enqueue(
            method=cbms_integration.send_to_cbms,  
            queue="short",
            timeout=60,
            is_async=True,
            doc=doc_name 
        )
        frappe.msgprint(_("Invoice/Return has been queued for sending to CBMS"))
        return {"message": _("Request processed successfully"), "status": "success"}

    except Exception as e:
        frappe.log_error(f"Error in post_sales_invoice_or_return_to_cbms: {str(e)}", "CBMS API Error")
        return {"message": _("An error occurred while processing the request: {0}").format(str(e))}

@frappe.whitelist()
def sync_failed_cbms_invoices():
    failed_invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "cbms_status": ["in", ["Failed"]]}, pluck="name")
    
    if not failed_invoices:
        frappe.msgprint(_("No failed invoices found.")) 
        return {"message": 0} 

    for inv_name in failed_invoices:
        doc = frappe.get_doc("Sales Invoice", inv_name)
        cbms = CBMSIntegration(doc)
        enqueue(
            method=cbms.send_to_cbms,
            queue="short",
            timeout=60,
            is_async=True,
            doc=doc
        )
    frappe.msgprint(_("{} failed invoice(s) queued for sync.").format(len(failed_invoices)))