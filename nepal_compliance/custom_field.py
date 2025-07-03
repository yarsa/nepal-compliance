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
            {"fieldname": "hs_code", "label": "H.S. Code", "fieldtype": "Data", "insert_after": "stock_uom", "description": "Harmonized System Code for the item, used for customs and trade purposes."},
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
            {"fieldname": "revised_salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 1},
        ],
        "Expense Claim": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Supplier": [
            {"fieldname": "supplier_vat_number", "label": "Supplier Vat/Pan Number", "fieldtype": "Data", "insert_after": "country", "allow_on_submit": 1},
            {"fieldname": "supplier_email_address", "label": "Supplier Email Address", "fieldtype": "Data", "insert_after": "supplier_vat_number"},
        ],
        "Customer": [
            {"fieldname": "customer_vat_number", "label": "Customer Vat/Pan Number", "fieldtype": "Data", "insert_after": "customer_group", "allow_on_submit": 1},
            {"fieldname": "customer_email_address", "label": "Customer Email Address", "fieldtype": "Data", "insert_after": "customer_vat_number"}
        ],
        "Salary Slip": [
            {"fieldname": "nepali_start_date", "label": "Nepali Start Date", "fieldtype": "Data", "insert_after": "start_date", "allow_on_submit": 1},
            {"fieldname": "nepali_end_date", "label": "Nepali End Date", "fieldtype": "Data", "insert_after": "end_date", "allow_on_submit": 1},
            {"fieldname": "taxable_salary", "label": "Taxable Salary", "fieldtype": "Currency", "insert_after": "total_deduction"},
        ],
        "Attendance": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "field_type": "Data", "insert_after": "attendance_date"}
        ],
        "Fiscal Year": [
            {"fieldname": "nepali_year_start_date", "label": "Nepali Year Start Date", "fieldtype": "Data", "insert_after": "year_start_date"},
            {"fieldname": "nepali_year_end_date", "label": "Nepali Year end Date", "fieldtype": "Data", "insert_after": "year_end_date"}
        ],
        "Holiday List":[
            {"fieldname": "nepali_from_date", "label": "Nepali From Date", "fieldtype": "Data", "insert_after": "total_holidays"},
            {"fieldname": "nepali_to_date", "label": "Nepali To Date", "fieldtype": "Data", "insert_after": "nepali_from_date"}
        ],
        "Holiday": [
            {"fieldname":"nepali_date_holiday", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "holiday_date"}
        ],
        "Leave Allocation":[
            {"fieldname": "from_nepali_date_leave_allocation", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_nepali_date_leave_allocation", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Leave Application": [
            {"fieldname": "from_nepali_date_leave_application", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_nepali_date_leave_application", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Purchase Order":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Purchase Receipt":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],  
        "Purchase Invoice":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
            {"fieldname": "vat_number", "label": "Supplier VAT/PAN", "fieldtype": "Data", "insert_after": "supplier", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "customer_vat_number", "label": "Customer VAT/PAN", "fieldtype": "Data", "insert_after": "vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Attach", "insert_after": "customer_vat_number", "hidden": 1, "allow_on_submit": 1},
            {"fieldname": "reason", "label": "Reason For Return", "fieldtype": "Data", "insert_after": "customer_vat_number", "depends_on": "eval:doc.is_return == 1", "mandatory_depends_on": "eval:doc.is_return == 1"},
            {"fieldname": "customs_declaration_number", "label": "Customs Declaration Number", "fieldtype": "Data", "insert_after": "bill_no", "depends_on": "eval:doc.supplier_country != 'Nepal'"}
        ],
        "Sales Order":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Sales Invoice": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "allow_on_submit": 1},
            {"fieldname": "vat_number", "label": "Customer VAT/PAN", "fieldtype": "Data", "insert_after": "customer", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "supplier_vat_number", "label": "Supplier VAT/PAN", "fieldtype": "Data", "insert_after": "vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "qr_code", "label": "QR Code", "fieldtype": "Attach", "insert_after": "supplier_vat_number", "hidden": 1, "allow_on_submit": 1},
            {"fieldname": "reason", "label": "Reason For Return", "fieldtype": "Data", "insert_after": "supplier_vat_number", "depends_on": "eval:doc.is_return == 1", "mandatory_depends_on": "eval:doc.is_return == 1"},
            {"fieldname": "cbms_status", "label": "CBMS Status", "fieldtype": "Select", "options": "\nSuccess\nPending\nFailed", "default": "", "insert_after": "supplier_vat_number", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "cbms_response", "label": "CBMS Response", "fieldtype": "Small Text", "insert_after": "cbms_status", "in_list_view": 1, "allow_on_submit": 1},
            {"fieldname": "customs_declaration_number", "label": "Customs Export Declaration Number", "fieldtype": "Data", "insert_after": "due_date", "depends_on": "eval:doc.supplier_country != 'Nepal'"},
            {"fieldname": "customs_declaration_date", "label": "Customs Export Declaration Date", "fieldtype": "Date", "insert_after": "customs_declaration_number", "depends_on": "eval:doc.supplier_country != 'Nepal'"},
            {"fieldname": "customs_declaration_date_bs", "label": "Customs Export Declaration Date BS", "fieldtype": "Data", "insert_after": "customs_declaration_date", "depends_on": "eval:doc.supplier_country != 'Nepal'"}
        ],
        "Delivery Note":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Material Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Payment Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Payment Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "GL Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Stock Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"} 
        ],
        "Journal Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "naming_series", "allow_on_submit": 1} 
        ],
        "Request for Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"} 
        ],
        "Supplier Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "supplier"} 
        ],
        "Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"} 
        ],
        "Blanket Order":[
            {"fieldname": "from_nepali_date", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_nepali_date", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Landed Cost Voucher": [
            {"fieldname": "nepali_date", "label": "NepalI Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Asset": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "field_type": "Data", "insert_after": "posting_date"},
            {"fieldname": "posting_date", "label": "Posting Date", "field_type": "Date", "insert_after": "asset_quantity"}
        ],
        "Asset Repair": [
            {"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Datetime", "insert_after": "column_break_6"},
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"} 
        ],
        "Asset Movement":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Asset Value Adjustment":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date"}
        ],
        "Asset Capitalization":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "POS Opening Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"} 
        ],
        "POS Closing Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "period_end_date"} 
        ],
        "Loyalty Program":[
            {"fieldname": "from_nepali_date", "label": "From Date BS", "fieldtype": "Data", "insert_after": "customer_territory"},
            {"fieldname": "to_nepali_date", "label": "To Date BS", "fieldtype": "Data", "insert_after": "from_nepali_date"}
        ],
        "Promotional Scheme":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from"},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto"}
        ],
        "Pricing Rule":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from"},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto"}
        ],
        "Coupon Code":[
            {"fieldname": "valid_from_bs", "label": "Valid From BS", "fieldtype": "Data", "insert_after": "valid_from"},
            {"fieldname": "valid_to_bs", "label": "Valid To BS", "fieldtype": "Data", "insert_after": "valid_upto"}
        ],
        "Serial No":[
            {"fieldname": "warranty_expiry_date_bs", "label": "Warranty Expiry Date BS", "fieldtype": "Data", "insert_after": "warranty_expiry_date"},
            {"fieldname": "amc_expiry_date_bs", "label": "AMC Expiry Date BS", "fieldtype": "Data", "insert_after": "amc_expiry_date"}
        ],
        "Batch":[
            {"fieldname": "expiry_date_bs", "label": "Expiry Date BS", "fieldtype": "Data", "insert_after": "expiry_date"},
            {"fieldname": "manufacturing_date_bs", "label": "Manufacturing Date BS", "fieldtype": "Data", "insert_after": "manufacturing_date"}
        ],
        "Installation Note":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "inst_date"} 
        ],
        "Stock Reconciliation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Quality Inspection":[
            {"fieldname": "report_date_bs_quality_inspection", "label": "Report Date BS", "fieldtype": "Data", "insert_after": "report_date"}
        ],
        "Quick Stock Balance":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date"}
        ],
        "Payroll Entry": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date"},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date"}
        ],
        "Income Tax Slab":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "effective_from"}
        ],
        "Payroll Period": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date"},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date"}
        ],
        "Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "from_date", "allow_on_submit": 1}          
        ],
        "Bulk Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_payable_account"}           
        ],
        "Salary Withholding":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Additional Salary":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date"}
        ],
        "Employee Incentive":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date"}
        ],
        "Retention Bonus":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "bonus_payment_date"}
        ],
        "Employee Tax Exemption Declaration":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period"}
        ],
        "Employee Tax Exemption Proof Submission":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period"}
        ],
        "Employee Benefit Application":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period"}
        ],
        "Employee Benefit Claim":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period"}
        ],
        "Compensatory Leave Request": [
            {"fieldname": "work_from_date_bs", "label": "Work From Date BS", "fieldtype": "Data", "insert_after": "work_from_date"},
            {"fieldname": "work_end_date_bs", "label": "Work End Date BS", "fieldtype": "Data", "insert_after": "work_end_date"}
        ],
        "Attendance Request": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Employee Advance": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Job Offer": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "offer_date"}
        ],
        "Employee Referral": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date"}
        ],
        "Shift Assignment": [
            {"fieldname": "start_date_bs", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date"},
            {"fieldname": "end_date_bs", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date"}
        ],
        "Shift Request": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Shift Assignment Tool": [
            {"fieldname": "start_date_bs", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date"},
            {"fieldname": "end_date_bs", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date"}
        ],
        "Employee Attendance Tool":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date"}
        ],
        "Upload Attendance":[
            {"fieldname": "att_fr_date_bs", "label": "Attendance From Date BS", "fieldtype": "Data", "insert_after": "att_fr_date"},
            {"fieldname": "column_break", "label": "", "fieldtype": "Column Break", "insert_after": "att_fr_date_bs"},
            {"fieldname": "att_to_date_bs", "label": "Attendance To Date BS", "fieldtype": "Data", "insert_after": "att_to_date"}
        ],
        "Leave Period": [
            {"fieldname": "from_date_bs", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_date_bs", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Leave Policy Assignment":[
            {"fieldname": "effective_from_bs", "label": "Effective From BS", "fieldtype": "Data", "insert_after": "effective_from"},
            {"fieldname": "effective_to_bs", "label": "Effective To BS", "fieldtype": "Data", "insert_after": "effective_to"}
        ],
        "Leave Control Panel":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "leave_policy"}
        ],
        "Leave Encashment":[
            {"fieldname": "encashment_date_bs", "label": "Encashment Date BS", "fieldtype": "Data", "insert_after": "encashment_date"}
        ],
        "Period Closing Voucher": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date"}
        ],
        "Invoice Discounting":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Dunning":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "Process Deferred Accounting": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
        ],
        "POS Invoice": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"}
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