import frappe
from dataclasses import fields
from frappe import _


def create_custom_fields():
    custom_fields = {
        "Company": [
            {"fieldname": "logo_for_printing", "label": "Logo For Printing", "fieldtype": "Attach", "insert_after": "parent_company"}
        ],
        "Employee": [
            {"fieldname": "date_picker", "label": "Date Picker", "fieldtype": "Date", "insert_after": "gender", "reqd": 0},
            {"fieldname": "revised_salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 1},
        ],
        "Expense Claim": [
            {"fieldname": "nepali_date", "label": "Neplai Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Customer": [
            {"fieldname": "customer_code", "label": "Customer Code", "fieldtype": "Data", "insert_after": "customer_name", "reqd": 0},
        ],
        "Salary Slip": [
            {"fieldname": "nepali_start_date", "label": "Nepali Start Date", "fieldtype": "Data", "insert_after": "start_date"},
            {"fieldname": "nepali_end_date", "label": "Nepali End Date", "fieldtype": "Data", "insert_after": "end_date"},
            {"fieldname": "taxable_salary", "label": "Taxable Salary", "fieldtype": "Currency", "insert_after": "total_deduction"},
        ],
        "Attendance": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "field_type": "Data", "insert_after": "attendance_date", "in_list_view": 1, "in_standard_filter": 1}
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
            {"fieldname":"nepali_date_holiday", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "holiday_date", "in_list_view": 1}
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
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Purchase Receipt":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],  
        "Purchase Invoice":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Sales Order":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Sales Invoice": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_standard_filter": 1},
            {"fieldname": "print_count", "label": "Print Count", "fieldtype": "Int", "insert_after": "amended_form", "read_only": 1}
        ],
        "Delivery Note":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Material Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Payment Request":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Payment Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "GL Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_standard_filter": 1, "in_list_view": 1}
        ],
        "Stock Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_standard_filter": 1, "in_list_view": 1} 
        ],
        "Journal Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "naming_series", "in_standard_filter": 1, "in_list_view": 1} 
        ],
        "Request for Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1} 
        ],
        "Supplier Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "supplier", "in_list_view": 1} 
        ],
        "Quotation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1} 
        ],
        "Blanket Order":[
            {"fieldname": "from_nepali_date", "label": "From Date BS", "fieldtype": "Data", "insert_after": "from_date"},
            {"fieldname": "to_nepali_date", "label": "To Date BS", "fieldtype": "Data", "insert_after": "to_date"}
        ],
        "Landed Cost Voucher": [
            {"fieldname": "nepali_date", "label": "NepalI Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1}
        ],
        "Asset": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "field_type": "Data", "insert_after": "posting_date", "in_list_view": 1},
            {"fieldname": "posting_date", "label": "Posting Date", "field_type": "Date", "insert_after": "asset_quantity", "in_list_view": 1}
        ],
        "Asset Repair": [
            {"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Datetime", "insert_after": "column_break_6"},
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date"} 
        ],
        "Asset Movement":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "transaction_date", "in_list_view": 1}
        ],
        "Asset Value Adjustment":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "in_list_view": 1,}
        ],
        "Asset Capitalization":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1}
        ],
        "POS Opening Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1} 
        ],
        "POS Closing Entry":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "period_end_date", "in_list_view": 1} 
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
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "inst_date", "in_list_view": 1} 
        ],
        "Stock Reconciliation":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1,}
        ],
        "Quality Inspection":[
            {"fieldname": "report_date_bs_quality_inspection", "label": "Report Date BS", "fieldtype": "Data", "insert_after": "report_date", "in_list_view": 1,}
        ],
        "Quick Stock Balance":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "date", "in_list_view": 1,}
        ],
        "Payroll Entry": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "in_list_view": 1,},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "in_list_view": 1,}
        ],
        "Income Tax Slab":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "effective_from", "in_list_view": 1,}
        ],
        "Payroll Period": [
            {"fieldname": "nepali_start_date", "label": "Start Date BS", "fieldtype": "Data", "insert_after": "start_date", "in_list_view": 1,},
            {"fieldname": "nepali_end_date", "label": "End Date BS", "fieldtype": "Data", "insert_after": "end_date", "in_list_view": 1,}
        ],
        "Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "from_date", "in_list_view": 1},            
        ],
        "Bulk Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_payable_account", "in_list_view": 1},            
        ],
        "Salary Withholding":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1}
        ],
        "Additional Salary":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date", "in_list_view": 1}
        ],
        "Employee Incentive":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_date", "in_list_view": 1}
        ],
        "Retention Bonus":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "bonus_payment_date", "in_list_view": 1}
        ],
        "Employee Tax Exemption Declaration":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "in_list_view": 1}
        ],
        "Employee Tax Exemption Proof Submission":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "in_list_view": 1}
        ],
        "Employee Benefit Application":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "in_list_view": 1}
        ],
        "Employee Benefit Claim":[
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "payroll_period", "in_list_view": 1}
        ],
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
                created_fields.append({"dt": doctype_name, "fieldname": field["fieldname"]})  # Store created field info
            else:
                frappe.msgprint(_(f"Field '{field['label']}' already exists in {doctype_name}."))

    return created_fields  

create_custom_fields()