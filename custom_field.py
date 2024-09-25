import frappe 

def create_custom_fields():
    custom_fields = {
        "Employee": [
            {"fieldname": "revised salary", "label": "Revised Salary", "fieldtype": "Currency", "insert_after": "payroll_cost_center", "reqd": 0},
            {"fieldname": "life insurance", "label": "Life Insurance", "fieldtype": "Data", "insert_after": "health_insurance_no", "reqd": 0},
        ],
        # "Customer": [
        #     {"fieldname": "customer_code", "label": "Customer Code", "fieldtype": "Data", "insert_after": "health_insurance_no", "reqd": 0},
        # ], ............
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