import frappe
from dataclasses import fields
from frappe import _


def create_custom_fields():
    custom_fields = {
        "Employee": [
            {"fieldname": "date_picker", "label": "Date Picker", "fieldtype": "Date", "insert_after": "gender", "reqd": 0},
            {"fieldname": "revised_salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 1},
        ],
        "Expense Claim": [
            {"fieldname": "nepali_date", "label": "Neplai Date", "fieldtype": "Data", "insert_after": "posting_date", "in_list_view": 1, "in_standard_filter": 1}
        ],
        "Salary Structure Assignment": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "fieldtype": "Data", "insert_after": "from_date", "in_list_view": 1},            
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
        "Landed Cost Voucher": [
            {"fieldname": "nepali_date", "label": "NepalI Date", "fieldtype": "Data", "insert_after": "posting_date", "in_standard_filter": 1}
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
        "Asset": [
            {"fieldname": "nepali_date", "label": "Nepali Date", "field_type": "Data", "insert_after": "posting_date"},
            {"fieldname": "posting_date", "label": "Posting Date", "field_type": "Date", "insert_after": "asset_quantity"}
        ],
        "Asset Repair": [
            {"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Datetime", "insert_after": "column_break_6"},
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
                created_fields.append({"dt": doctype_name, "fieldname": field["fieldname"]})  # Store created field info
            else:
                frappe.msgprint(_(f"Field '{field['label']}' already exists in {doctype_name}."))

    return created_fields  

create_custom_fields()