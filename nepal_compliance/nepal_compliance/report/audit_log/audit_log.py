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
            "fieldname": "modified",
            "label": _("Last Modified Date and Time"),
            "fieldtype": "Datetime",
            "width": 180
        },
        {
            "fieldname": "nepali_date",
            "label": _("Nepali Date"),
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
    conditions = "1=1"
    allowed_doctypes = ["Sales Invoice", "Purchase Invoice"]
    
    if filters.get("ref_doctype"):
        if filters["ref_doctype"] not in allowed_doctypes:
            frappe.throw(_("The selected document type is not allowed."))
        conditions += " AND v.ref_doctype = %(ref_doctype)s"
    else:
        conditions += " AND v.ref_doctype IN %(allowed_doctypes)s"
        
    if filters.get('docname'):
        conditions += " AND v.docname = %(docname)s"

    if filters.get('from_date') and filters.get('to_date'):
        conditions += " AND DATE(v.modified) >= %(from_date)s AND DATE(v.modified) <= %(to_date)s"
        
    if filters.get("doc_status"):
        conditions += " AND d.status = %(doc_status)s"
        
    return conditions, allowed_doctypes

def get_audit_log(filters, columns):
    
    conditions, allowed_doctypes = get_conditions(filters)
    filters_values = {}
    if filters:
        filters_values.update(filters)
    else:
        filters_values = {}
        
    if not filters.get("ref_doctype"):
        filters_values['allowed_doctypes'] = tuple(allowed_doctypes)
    
    ref_doctype = filters.get("ref_doctype", "Sales Invoice")
    
    if ref_doctype == "Sales Invoice":
        table_name = "Sales Invoice"
    elif ref_doctype == "Purchase Invoice":
        table_name = "Purchase Invoice"
    else:
        frappe.throw(_("Invalid ref_doctype"))

    query = '''
        SELECT v.ref_doctype,
               v.docname,
               v.data AS "audit_detail",
               v.owner,
               v.modified_by,
               v.modified,
               IFNULL (d.nepali_date, '') AS nepali_date,
               d.status AS doc_status 
        FROM tabVersion v
        LEFT JOIN `tab{table_name}` d ON v.docname = d.name
        WHERE {conditions}
        ORDER BY v.docname
    '''.format(table_name=ref_doctype, conditions=conditions)
    
    data = frappe.db.sql(query, filters_values, as_dict=1)
    dl = list(data)
    dict_submit = {}
    changed_fields = set()
    
    for row in dl:
        temp_json = json.loads(row['audit_detail'])
        changes = []
        row['submit_status'] = "No"

        if "changed" in temp_json:
            for d in temp_json['changed']:
                if d[0] == 'docstatus':
                    if d[1] == 0 and d[2] == 1:
                        row['submit_status'] = "Yes"
                        dict_submit.setdefault(row['docname'], frappe._dict()).setdefault("modified", []).append(row["modified"])
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
        
        row['doc_status'] = doc.get("status")
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
        
    return dl