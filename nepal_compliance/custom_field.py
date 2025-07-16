import frappe
from dataclasses import fields
from frappe import _


def create_custom_fields():
    custom_fields = {
        "Company": [
            {"fieldname": "logo_for_printing", "label": "Logo For Printing", "fieldtype": "Attach", "insert_after": "parent_company"},
            {"fieldname": "company_vat_number", "label": "Vat/Pan Number", "fieldtype": "Data", "insert_after": "default_holiday_list", "allow_on_submit": 1}
        ],
        "Item": [
            {"fieldname": "is_nontaxable_item", "label": "Is Non-Taxable Item", "fieldtype": "Check", "insert_after": "is_stock_item"},
            {"fieldname": "hs_code", "label": "H.S. Code", "fieldtype": "Data", "insert_after": "stock_uom", "description": "Harmonized System Code for the item, used for customs and trade purposes."}
        ],
        "Sales Invoice Item": [
            {"fieldname": "is_nontaxable_item", "label": "Is Non-Taxable Item", "fieldtype": "Check", "insert_after": "is_free_item", "fetch_from": "item_code.is_nontaxable_item", "read_only": 1},
            {"fieldname": "hs_code", "label": "H.S. Code", "fieldtype": "Data", "insert_after": "uom", "fetch_from": "item_code.hs_code"}
        ],
        "Purchase Invoice Item": [
            {"fieldname": "is_nontaxable_item", "label": "Is Non-Taxable Item", "fieldtype": "Check", "insert_after": "is_free_item", "fetch_from": "item_code.is_nontaxable_item", "read_only": 1},
            {"fieldname": "hs_code", "label": "H.S. Code", "fieldtype": "Data", "insert_after": "uom", "fetch_from": "item_code.hs_code"}
        ],
        "User": [
            {"fieldname": "use_ad_date", "label": "Use Ad Date", "fieldtype": "Check", "insert_after": "username",
            "description": "<b>Disclaimer:</b> Checking this means you prefer using the default date picker (AD format) as your preferred format."},
        ],
        "Employee": [
            {"fieldname": "revised_salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 1, "allow_on_submit": 1},
        ],
        "Expense Claim": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", 'allow_on_submit': 1},
        ],
        "Supplier": [
            {"fieldname": "supplier_vat_number", "label": "Supplier Vat/Pan Number", "fieldtype": "Data", "insert_after": "country", "allow_on_submit": 1},
            {"fieldname": "supplier_email_address", "label": "Supplier Email Address", "fieldtype": "Data", "insert_after": "supplier_vat_number"}
        ],
        "Customer": [
            {"fieldname": "customer_vat_number", "label": "Customer Vat/Pan Number", "fieldtype": "Data", "insert_after": "customer_group", "allow_on_submit": 1},
            {"fieldname": "customer_email_address", "label": "Customer Email Address", "fieldtype": "Data", "insert_after": "customer_vat_number"}
        ],
        "Salary Slip": [
            {"fieldname": "nepali_start_date", "label": "Nepali Start Date", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "nepali_end_date", "label": "Nepali End Date", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1},
            {"fieldname": "taxable_salary", "label": "Taxable Salary", "fieldtype": "Currency", "insert_after": "total_deduction", "allow_on_submit": 1},
        ],
        "Attendance": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "attendance_date", "allow_on_submit": 1},
        ],
        "Fiscal Year": [
            {"fieldname": "nepali_year_start_date", "label": "Nepali Year Start Date", "fieldtype": "Data", "insert_after": "year_start_date", "allow_on_submit": 1},
            {"fieldname": "nepali_year_end_date", "label": "Nepali Year end Date", "fieldtype": "Data", "insert_after": "year_end_date", "allow_on_submit": 1}
        ],
        "Holiday List":[
            {"fieldname": "nepali_from_date", "label": "Nepali From Date", "fieldtype": "Data", "insert_after": "total_holidays", "allow_on_submit": 1},
            {"fieldname": "nepali_to_date", "label": "Nepali To Date", "fieldtype": "Data", "insert_after": "nepali_from_date", "allow_on_submit": 1}
        ],
        "Holiday": [
            {"fieldname":"nepali_date_holiday", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "holiday_date", "allow_on_submit": 1}
        ],
        "Leave Allocation":[
            {"fieldname": "from_nepali_date_leave_allocation", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_nepali_date_leave_allocation", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1}
        ],
        "Leave Application": [
            {"fieldname": "from_nepali_date_leave_application", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_nepali_date_leave_application", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1},
        ],
        "Purchase Order":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Purchase Receipt":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],  
        "Purchase Invoice":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
            {"fieldname": "vat_number", "label": "Supplier VAT/PAN", "fieldtype": "Data", "insert_after": "supplier", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "customer_vat_number", "label": "Customer VAT/PAN", "fieldtype": "Data", "insert_after": "vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Attach", "insert_after": "customer_vat_number", "hidden": 1, "allow_on_submit": 1},
            {"fieldname": "reason", "label": "Reason For Return", "fieldtype": "Data", "insert_after": "customer_vat_number", "depends_on": "eval:doc.is_return == 1", "mandatory_depends_on": "eval:doc.is_return == 1"},
            {"fieldname": "customs_declaration_number", "label": "Customs Declaration Number", "fieldtype": "Data", "insert_after": "bill_no"}
        ],
        "Sales Order":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Sales Invoice": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
            {"fieldname": "vat_number", "label": "Customer VAT/PAN", "fieldtype": "Data", "insert_after": "customer", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "supplier_vat_number", "label": "Supplier VAT/PAN", "fieldtype": "Data", "insert_after": "vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Attach", "insert_after": "supplier_vat_number", "hidden": 1, "allow_on_submit": 1},
            {"fieldname": "reason", "label": "Reason For Return", "fieldtype": "Data", "insert_after": "supplier_vat_number", "depends_on": "eval:doc.is_return == 1", "mandatory_depends_on": "eval:doc.is_return == 1"},
            {"fieldname": "cbms_status", "label": "CBMS Status", "fieldtype": "Select", "options": "\nSuccess\nPending\nFailed", "default": "", "insert_after": "supplier_vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "cbms_response", "label": "CBMS Response", "fieldtype": "Small Text", "insert_after": "cbms_status", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "customs_declaration_number", "label": "Customs Export Declaration Number", "fieldtype": "Data", "insert_after": "cost_center", "allow_on_submit": 1},
            {"fieldname": "customs_declaration_date", "label": "Customs Export Declaration Date", "fieldtype": "Date", "insert_after": "project", "allow_on_submit": 1},
            {"fieldname": "customs_declaration_date_bs", "label": "Customs Export Declaration Date BS", "fieldtype": "Data", "insert_after": "customs_declaration_date", "allow_on_submit": 1}
        ],
        "Delivery Note":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Material Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Payment Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Payment Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
        ],
        "GL Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Stock Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1} 
        ],
        "Journal Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "naming_series", "allow_on_submit": 1} 
        ],
        "Request for Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1} 
        ],
        "Supplier Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "supplier", "allow_on_submit": 1} 
        ],
        "Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1} 
        ],
        "Blanket Order":[
            {"fieldname": "from_nepali_date", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_nepali_date", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1}
        ],
        "Landed Cost Voucher": [
            {"fieldname": "nepali_date", "label": "NepalI Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Asset": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
            {"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Date", "insert_after": "asset_quantity"}
        ],
        "Asset Repair": [
            {"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Datetime", "insert_after": "column_break_6"},
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1} 
        ],
        "Asset Movement":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Asset Value Adjustment":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "allow_on_submit": 1},
        ],
        "Asset Capitalization":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "POS Opening Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1} 
        ],
        "POS Closing Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "period_end_date", "allow_on_submit": 1} 
        ],
        "Loyalty Program":[
            {"fieldname": "from_nepali_date", "label": "From Date BS", "fieldtype": "Data", "insert_after": "customer_territory", "allow_on_submit": 1},
            {"fieldname": "to_nepali_date", "label": "To Date BS", "fieldtype": "Data", "insert_after": "from_nepali_date", "allow_on_submit": 1}
        ],
        "Promotional Scheme":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from", "allow_on_submit": 1},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto", "allow_on_submit": 1}
        ],
        "Pricing Rule":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from", "allow_on_submit": 1},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto", "allow_on_submit": 1}
        ],
        "Coupon Code":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from", "allow_on_submit": 1},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto", "allow_on_submit": 1}
        ],
        "Serial No":[
            {"fieldname": "warranty_expiry_date_bs", "label": "Warranty Expiry Date BS", "fieldtype": "Data", "insert_after": "warranty_expiry_date", "allow_on_submit": 1},
            {"fieldname": "amc_expiry_date_bs", "label": "AMC Expiry Date BS", "fieldtype": "Data", "insert_after": "amc_expiry_date", "allow_on_submit": 1}
        ],
        "Batch":[
            {"fieldname": "expiry_date_bs", "label": "Expiry Date BS", "fieldtype": "Data", "insert_after": "expiry_date", "allow_on_submit": 1},
            {"fieldname": "manufacturing_date_bs", "label": "Manufacturing Date BS", "fieldtype": "Data", "insert_after": "manufacturing_date", "allow_on_submit": 1}
        ],
        "Installation Note":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "inst_date", "allow_on_submit": 1} 
        ],
        "Stock Reconciliation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Quality Inspection":[
            {"fieldname": "report_date_bs_quality_inspection", "label": "Report Date BS", "fieldtype": "Data", "insert_after": "report_date", "allow_on_submit": 1}
        ],
        "Quick Stock Balance":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "allow_on_submit": 1}
        ],
        "Payroll Entry": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1}
        ],
        "Income Tax Slab":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "effective_from", "allow_on_submit": 1},
        ],
        "Payroll Period": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1}
        ],
        "Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
        ],
        "Bulk Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_payable_account", "allow_on_submit": 1}           
        ],
        "Salary Withholding":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Additional Salary":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date", "allow_on_submit": 1}
        ],
        "Employee Incentive":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date", "allow_on_submit": 1}
        ],
        "Retention Bonus":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "bonus_payment_date", "allow_on_submit": 1}
        ],
        "Employee Tax Exemption Declaration":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "allow_on_submit": 1}
        ],
        "Employee Tax Exemption Proof Submission":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "allow_on_submit": 1}
        ],
        "Employee Benefit Application":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "allow_on_submit": 1}
        ],
        "Employee Benefit Claim":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "allow_on_submit": 1}
        ],
        "Compensatory Leave Request": [
            {"fieldname": "work_from_date_bs", "label": "Work From Date BS", "fieldtype": "Data", "insert_after": "work_from_date", "allow_on_submit": 1},
            {"fieldname": "work_end_date_bs", "label": "Work End Date BS", "fieldtype": "Data", "insert_after": "work_end_date", "allow_on_submit": 1}
        ],
        "Attendance Request": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1}
        ],
        "Employee Advance": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Job Offer": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "offer_date", "allow_on_submit": 1}
        ],
        "Employee Referral": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "allow_on_submit": 1}
        ],
        "Shift Assignment": [
            {"fieldname": "start_date_bs", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "end_date_bs", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1}
        ],
        "Shift Request": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1}
        ],
        "Shift Assignment Tool": [
            {"fieldname": "start_date_bs", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "end_date_bs", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1}
        ],
        "Employee Attendance Tool":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "allow_on_submit": 1},
        ],
        "Upload Attendance":[
            {"fieldname": "att_fr_date_bs", "label": "Attendance From Date BS", "fieldtype": "Data", "insert_after": "att_fr_date", "allow_on_submit": 1},
            {"fieldname": "column_break", "label": "", "fieldtype": "Column Break", "insert_after": "att_fr_date_bs"},
            {"fieldname": "att_to_date_bs", "label": "Attendance To Date BS", "fieldtype": "Data", "insert_after": "att_to_date", "allow_on_submit": 1},
        ],
        "Leave Period": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date", "allow_on_submit": 1}
        ],
        "Leave Policy Assignment":[
            {"fieldname": "effective_from_bs", "label": "Effective From BS", "fieldtype": "Data", "insert_after": "effective_from", "allow_on_submit": 1},
            {"fieldname": "effective_to_bs", "label": "Effective To BS", "fieldtype": "Data", "insert_after": "effective_to", "allow_on_submit": 1}
        ],
        "Leave Control Panel":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "leave_policy", "allow_on_submit": 1}
        ],
        "Leave Encashment":[
            {"fieldname": "encashment_date_bs", "label": "Encashment Date BS", "fieldtype": "Data", "insert_after": "encashment_date", "allow_on_submit": 1},
        ],
        "Period Closing Voucher": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "allow_on_submit": 1}
        ],
        "Invoice Discounting":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Dunning":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "Process Deferred Accounting": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1}
        ],
        "POS Invoice": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
        ]
    }

    created_fields = [] 

    for doctype_name, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype_name, "fieldname": field["fieldname"]}):
                custom_field = frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": doctype_name,
                    "module": "Nepal Compliance",
                    **field
                })
                custom_field.save()
                frappe.msgprint(_(f"Custom field '{field['label']}' added successfully to {doctype_name}!"))
                created_fields.append({"dt": doctype_name, "fieldname": field["fieldname"]})
            else:
                frappe.msgprint(_(f"Field '{field['label']}' already exists in {doctype_name}."))

    return created_fields  

create_custom_fields()