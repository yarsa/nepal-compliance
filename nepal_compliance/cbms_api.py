import frappe
import requests
import json
from frappe.utils.password import get_decrypted_password
from frappe.utils.background_jobs import enqueue
from frappe import _
from datetime import datetime
from typing import Optional, Any

class CBMSIntegration:
    def __init__(self, doc):
        self.doc = doc
        self.cbms_settings = None
        self.api_url = None
        self.invoice_payload = None

    def is_cbms_configured(self):
        try:
            self.cbms_settings = frappe.get_doc("CBMS Settings")
            
            if not self.cbms_settings.configure_cbms:
                return {
                    "status": "disabled",
                    "message": _("CBMS is disabled.")
                }
            
            if not all([
                self.cbms_settings.user_name,
                self.cbms_settings.get_password("password"),  
                self.cbms_settings.panvat_no,
                self.cbms_settings.sales_api_url,  
                self.cbms_settings.credit_note_api_url  
            ]):
                return {
                    "status": "configuration_error",
                    "message": _("CBMS is enabled but configuration is incomplete. Please fill all required fields in CBMS Settings.")
                }

            return {
                "status": "configured",
                "message": None
            }

        except frappe.DoesNotExistError:
            return {
                "status": "not_found",
                "message": _("CBMS Settings not found.")
            }
    
    def convert_to_nepali_fy_format(self, fy_name):
        if "/" in fy_name and len(fy_name.split("/")[0]) == 4:
            return fy_name
        try:
            start, end = [int(x) for x in fy_name.split("-")]
            nep_start = start + 57
            nep_end = end + 57
            return f"{nep_start}/{str(nep_end)[-2:]}"
        except Exception:
            return fy_name

    def get_buyer_pan(self):
        vat = getattr(self.doc, "vat_number", None)
        tax = getattr(self.doc, "tax_id", None)

        pan = vat or tax or ""
        pan = pan.strip()
    
        if pan and pan.isdigit() or pan.replace('.', '').isdigit():
            return pan
        else:
            return None

    def prepare_payload(self):
        from nepal_compliance.nepali_date_utils.nepali_date import format_bs
        try:
            if not self.cbms_settings:
                self.cbms_settings = frappe.get_doc("CBMS Settings")
            
            if not self.cbms_settings:
                frappe.log_error("CBMS Settings not found", "CBMS API Error")
                return None

            fiscal_year = frappe.db.get_value(
                "Fiscal Year",
                {"year_start_date": ["<=", self.doc.posting_date], "year_end_date": [">=", self.doc.posting_date]},
                "name"
            )
            if not fiscal_year:
                frappe.log_error(f"Fiscal Year not found for posting date: {self.doc.posting_date}", "CBMS API Error")
                return None
            
            fiscal_year = self.convert_to_nepali_fy_format(fiscal_year)

            try:
                invoice_date = format_bs(self.doc.posting_date, "YYYY.MM.DD")
            except ValueError as e:
                frappe.log_error(f"Invalid Posting date format: {self.doc.posting_date}. Error: {str(e)}", "CBMS API Error")
                return None
            except AttributeError as e:
                frappe.msgprint(_("Posting Date Missing"))
                frappe.log_error("Posting date is missing in the Sales Invoice.", "CBMS API Error")
                return None

            datetimeclient = frappe.utils.now()
            datetime_obj = datetime.strptime(datetimeclient, "%Y-%m-%d %H:%M:%S.%f")
            formatted_datetime = datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

            self.invoice_payload = {
                "username": self.cbms_settings.user_name,
                "password": self.cbms_settings.get_password("password"),
                "seller_pan": self.cbms_settings.panvat_no,
                "buyer_pan": self.get_buyer_pan(),  
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
            config = self.is_cbms_configured()
            
            if config["status"] != "configured":
                raise Exception(config["message"])

            api_url = self.cbms_settings.credit_note_api_url if self.doc.is_return else self.cbms_settings.sales_api_url
            if not api_url:
                frappe.log_error(_("API URL is not configured for CBMS.", "CBMS API Error"))
                return {"message": _("API URL is not configured for CBMS."), "status": "failed"}

            payload = self.prepare_payload()
            if not payload:
                raise Exception(_("Failed to prepare payload."))

            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)

            if response.status_code == 200:
                doc.reload()
                doc.cbms_status = "Success"
                doc.cbms_response = response.text
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
def post_sales_invoice_or_return_to_cbms(doc_name: Any, method: Optional[str] = None) -> None:
    
    try:
        doc = frappe.get_doc("Sales Invoice", doc_name)
        if not doc:
            frappe.throw(_("Sales Invoice not found"))

        cbms_integration = CBMSIntegration(doc)
        config = cbms_integration.is_cbms_configured()
        
        if config["status"] != "configured":
            return config
        
        enqueue(
            method=cbms_integration.send_to_cbms,  
            queue="short",
            timeout=60,
            is_async=True,
            doc=doc_name 
        )
        frappe.msgprint(_("Invoice/Return has been queued for sending to CBMS."))
        return {"message": _("Request processed successfully"), "status": "queued"}

    except Exception as e:
        frappe.log_error(
            message=str(e),
            title="CBMS API Error"
        )
        return {"message": _("An error occurred while processing the request: {0}").format(str(e))}

@frappe.whitelist()
def sync_failed_cbms_invoices():
    failed_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 1, "cbms_status": ["!=", "Success"]},
        pluck="name"
    )

    if not failed_invoices:
        frappe.msgprint(_("No invoices with failed status found.")) 
        return {"message": 0} 

    for inv_name in failed_invoices:
        try:
            doc = frappe.get_doc("Sales Invoice", inv_name)
            cbms = CBMSIntegration(doc)

            enqueue(
                method=cbms.send_to_cbms,
                queue="short",
                timeout=60,
                is_async=True,
                doc=doc
            )
            frappe.logger().info(f"Invoice {inv_name} queued for CBMS sync.")
        except Exception as e:
            frappe.log_error(f"Error processing invoice {inv_name} for CBMS sync: {str(e)}", "CBMS Sync Retry")

    frappe.msgprint(_("{} invoice(s) queued for CBMS sync.").format(len(failed_invoices)))