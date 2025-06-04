# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import getdate
import json


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_audit_log(filters, columns)
	return columns, data

def get_columns():
    columns = [
        { 
            "label": _("Document Type"), 
            "fieldtype": "Link", 
            "options": "DocType", 
            "fieldname": "ref_doctype", 
            "width": 150
        },
        { 
            "label": _("Document Reference"), 
            "fieldtype": "Dynamic Link", 
            "options": "ref_doctype", 
            "fieldname": "docname", 
            "width": 220
        },
        {
            "fieldname": "modified_by",
            "label": _("Last Modified By User"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "operation",
            "label": _("Operation"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "modified",
            "label": _("Last Modified Date and Time"),
            "fieldtype": "Datetime",
            "width": 180
        },
        {
            "fieldname": "nepali_date",
            "label": _("Date"),
            "fieldtype": "Data",
            "width": 150
        },
		{
			"fieldname": "doc_status",
			"label": _("Doc Status"),
			"fieldtype": "Data",
			"width": 100
		},
        {
            "fieldname": "submit_status",
            "label": _("Submit Status"),
            "fieldtype": "Data",
            "width": 100
        }
    ]
    return columns

def get_conditions(filters):
    allowed_doctypes = [
    "Sales Invoice", "Purchase Invoice", "Journal Entry", "Payment Entry",
    "Sales Order", "Purchase Order", "Delivery Note", "Purchase Receipt",
    "Stock Entry", "Stock Reconciliation", "POS Invoice", "Asset", "Expense Claim"]

    conditions = []

    if filters.get("ref_doctype"):
        if filters["ref_doctype"] not in allowed_doctypes:
            frappe.throw(_("The selected document type is not allowed."))
        conditions.append("v.ref_doctype = %(ref_doctype)s")
    else:
        conditions.append("v.ref_doctype IN %(allowed_doctypes)s")

    if filters.get('docname'):
        conditions.append("v.docname = %(docname)s")

    if filters.get("from_nepali_date"):
        conditions.append("IFNULL(d.nepali_date, '') >= %(from_nepali_date)s")
    if filters.get("to_nepali_date"):
        conditions.append("IFNULL(d.nepali_date, '') <= %(to_nepali_date)s")

    if filters.get("doc_status"):
        conditions.append("IFNULL(d.status, '') = %(doc_status)s")
    
    if filters.get("modified_by"):
        conditions.append("v.modified_by = %(modified_by)s")

    condition_str = " AND ".join(conditions) if conditions else "1=1"
    return condition_str, allowed_doctypes

def get_audit_log(filters, columns):
    
    conditions, allowed_doctypes = get_conditions(filters)
    filters_values = filters.copy() if filters else {}
        
    if not filters.get("ref_doctype"):
        filters_values['allowed_doctypes'] = tuple(allowed_doctypes)
    
    ref_doctype = filters.get("ref_doctype", "Sales Invoice")

    if ref_doctype not in allowed_doctypes:
        frappe.throw(_("Invalid ref_doctype"))

    meta = frappe.get_meta(ref_doctype)
    has_nepali_date = "nepali_date" in [df.fieldname for df in meta.fields]
    has_status = "status" in [df.fieldname for df in meta.fields]

    select_fields = [
        "v.ref_doctype",
        "v.docname",
        "v.data AS audit_detail",
        "v.owner",
        "v.modified_by",
        "v.modified"
    ]

    if has_nepali_date:
        select_fields.append("IFNULL(d.nepali_date, '') AS nepali_date")
    else:
        select_fields.append("'' AS nepali_date")

    if has_status:
        select_fields.append("d.status AS doc_status")
    else:
        select_fields.append("'' AS doc_status")

    select_clause = ",\n       ".join(select_fields)

    query = f"""
        SELECT {select_clause}
        FROM tabVersion v
        LEFT JOIN `tab{ref_doctype}` d ON v.docname = d.name
        WHERE {conditions}
        ORDER BY v.docname
    """
    data = frappe.db.sql(query, filters_values, as_dict=1)
    dl = list(data)
    dict_submit = {}
    changed_fields = set()
    
    for row in dl:
        temp_json = json.loads(row['audit_detail'])
        changes = []
        row['submit_status'] = "No"
        row["operation"] = "Update"

        if "operation" in temp_json:
            row["operation"] = temp_json["operation"].capitalize()

        if "changed" in temp_json:
            for d in temp_json['changed']:
                if d[0] == 'docstatus':
                    if d[1] == 0 and d[2] == 1:
                        row['submit_status'] = "Yes"
                        row["operation"] = "Submit"
                        dict_submit.setdefault(row['docname'], frappe._dict()).setdefault("modified", []).append(row["modified"])
                    elif d[1] == 1 and d[2] == 2:
                        row["operation"] = "Cancel"
                        row["submit_status"] = "No"
                    else:
                        row['submit_status'] = "No"
                else:
                    changed_fields.add(d[0])
                    row[d[0]] = f"{d[1]} -> {d[2]}"
                    changes.append(f"- **{d[0]}**: {d[1]} -> {d[2]}")
        if 'nepali_date' not in row:
            row['nepali_date'] = ""

        if "data" in temp_json:
            for d in temp_json['data']:
                if d[0] == 'sql_query':
                    row['sql_query'] = d[1]
                    changed_fields.add('sql_query')
                    changes.append(f"- **SQL Query**: {d[1]}")
                elif d[0] == 'data_import':
                    row['data_import'] = d[1]
                    changed_fields.add('data_import')
                    changes.append(f"- **Data Import**: {d[1]}")
                elif d[0] == 'user_activity':
                    row['user_activity'] = d[1]
                    changed_fields.add('user_activity')
                    changes.append(f"- **User Activity**: {d[1]}")
        doc = frappe.get_doc(row['ref_doctype'], row['docname'])
        
        row['doc_status'] = doc.get("status") or ""
        if not row.get('nepali_date'):
            row['nepali_date'] = doc.get("nepali_date") or ""

        row['audit_detail_summary'] = "\n".join(changes)
        
    for field in changed_fields:
        if field != "nepali_date":
            columns.append({
                "label": _(field.replace("_", " ").title()),
                "fieldtype": "Data",
                "fieldname": field,
                "width": 200
            })
    columns.append({
        "label": _("Audit Detail Summary"),
        "fieldtype": "Text",
        "fieldname": "audit_detail_summary",
        "width": 500
    })
    
    for row in dl:
        modified = ''
        if row['docname'] in dict_submit:
            modified = dict_submit.get(row['docname'], {}).get("modified", [])[0]
        if modified:
            if (row['modified'] - modified).days > 0 and row['submit_status'] == 'No':
                row['submit_status'] = "After Submit"
            elif (row['modified'] - modified).days == 0 and row['submit_status'] == 'No' and (row['modified'] - modified).seconds > 0:
                row['submit_status'] = "After Submit"
    
    if filters.get("status"):
        dl = [row for row in dl if row['submit_status'] == filters["status"]]

    if filters.get("doc_status"):
        dl = [row for row in dl if row['doc_status'] == filters["doc_status"]]
    
    if filters.get("operation"):
        dl = [row for row in dl if row.get("operation") == filters["operation"]]
 
    return dl