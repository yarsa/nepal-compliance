import frappe 
from frappe import _

def create_custom_fields():
    custom_fields = {
        "Employee": [
            {"fieldname": "revised salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 0},
            {"fieldname": "life insurance", "label": "Life Insurance", "fieldtype": "Data", "insert_after": "health_insurance_no", "reqd": 0},
        ],
        "Salary Slip": [
            {"fieldname": "nepali start date", "lable": "Nepali Start Date", "fieldtype": "Data", "insert_after": "start_date", "reqd": 0},
            {"fieldname": "nepali end date", "label": "Nepali End Date", "fieldtype": "Data", "insert_after": "end_date"}
        ],
        "Fiscal Year": [
            {"fieldname": "nepali_year_start_date", "label": "Nepali Year Start Date", "fieldtype": "Date", "insert_after": "year_start_date"}
            {"fieldname": "nepali_year_end_date", "label": "Nepali Year Start Date", "fieldtype": "Date", "insert_after": "year_end_date"}
        ]
    }

    created_fields = []
    for doctype_name, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype_name, "fieldname": field["fieldname"]}):
                custom_field = frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": doctype_name,
                    **field
                })
                custom_field.insert()
                frappe.msgprint(_(f"Custom field '{field['label']}' added successfully to {doctype_name}!"))
                created_fields.append({"dt": doctype_name, "fieldname": field["fieldname"]})  
            else:
                frappe.msgprint(_(f"Field '{field['label']}' already exists in {doctype_name}."))

    return created_fields 