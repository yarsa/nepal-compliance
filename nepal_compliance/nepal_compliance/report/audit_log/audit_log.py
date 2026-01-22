# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import getdate
import json

DOCTYPE_DATE_FIELD_MAP = {
    "Sales Invoice": "posting_date",
    "Purchase Invoice": "posting_date",
    "Journal Entry": "posting_date",
    "Payment Entry": "posting_date",
    "Delivery Note": "posting_date",
    "Purchase Receipt": "posting_date",
    "POS Invoice": "posting_date",
    "Stock Entry": "posting_date",
    "Stock Reconciliation": "posting_date",
    "Sales Order": "transaction_date",
    "Purchase Order": "transaction_date",
    "Asset": "purchase_date",
    "Expense Claim": "posting_date",
}

ALLOWED_DOCTYPES = list(DOCTYPE_DATE_FIELD_MAP.keys())

def execute(filters=None):
	columns, data = [], []
	filters = filters or {}
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
            "fieldname": "posting_date",
            "label": _("Date"),
            "fieldtype": "Date",
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

def get_audit_log(filters, columns):

    queries = []
    common_conditions = []

    if filters.get("docname"):
        common_conditions.append(f"v.docname = {frappe.db.escape(filters['docname'])}")

    if filters.get("modified_by"):
        common_conditions.append(f"v.modified_by = {frappe.db.escape(filters['modified_by'])}")

    common_condition_sql = " AND ".join(common_conditions) if common_conditions else "1=1"

    if filters.get("ref_doctype"):
        doctypes = [filters["ref_doctype"]]
        if doctypes[0] not in ALLOWED_DOCTYPES:
            frappe.throw(_("Invalid Document Type"))
    else:
        doctypes = ALLOWED_DOCTYPES

    for doctype in doctypes:
        meta = frappe.get_meta(doctype)
        date_field = DOCTYPE_DATE_FIELD_MAP.get(doctype)
        has_status = "status" in [df.fieldname for df in meta.fields]

        conditions = [
            f"v.ref_doctype = {frappe.db.escape(doctype)}",
            common_condition_sql
        ]

        if date_field and filters.get("from_nepali_date"):
            conditions.append(f"d.{date_field} >= {frappe.db.escape(filters['from_nepali_date'])}")

        if date_field and filters.get("to_nepali_date"):
            conditions.append(f"d.{date_field} <= {frappe.db.escape(filters['to_nepali_date'])}")

        if filters.get("doc_status") and has_status:
            conditions.append(f"d.status = {frappe.db.escape(filters['doc_status'])}")

        where_clause = " AND ".join(conditions)

        queries.append(f"""
            SELECT
                v.ref_doctype,
                v.docname,
                v.data AS audit_detail,
                v.owner,
                v.modified_by,
                v.modified,
                {f"d.{date_field}" if date_field else "NULL"} AS posting_date,
                {"d.status" if has_status else "''"} AS doc_status
            FROM tabVersion v
            LEFT JOIN `tab{doctype}` d ON v.docname = d.name
            WHERE {where_clause}
        """)

    final_query = " UNION ALL ".join(queries) + " ORDER BY modified DESC"

    data = frappe.db.sql(final_query, as_dict=True)

    return post_process_rows(data, columns, filters)

def post_process_rows(data, columns, filters):

    changed_fields = set()
    submit_map = {}

    for row in data:
        try:
            payload = json.loads(row["audit_detail"])
        except (json.JSONDecodeError, TypeError):
            row.uopdate({
                "submit_status": "No",
                "operation": "Unknown",
                "audit_detail_summary": "Error parsing audit detail"
            })
            continue
        summary_lines = []
        row["submit_status"] = "No"
        row["operation"] = payload.get("operation", "Update").capitalize()

        for changes in payload.get("changed", []):
            if not isinstance(changes, list) or len(changes) < 3:
                continue
            field, old, new = changes[0], changes[1], changes[2]
            if field == "docstatus":
                if old == 0 and new == 1:
                    row["submit_status"] = "Yes"
                    row["operation"] = "Submit"
                    submit_map.setdefault(row["docname"], []).append(row["modified"])
                elif old == 1 and new == 2:
                    row["operation"] = "Cancel"
            else:
                changed_fields.add(field)
                row[field] = f"{old} → {new}"
                summary_lines.append(f"- **{field.replace('_',' ').title()}**: {old} → {new}")

        for d in payload.get("data", []):
            if not isinstance(d, list) or len(d) < 2:
                continue
            field, value = d[0], d[1]
            changed_fields.add(field)
            row[field] = value
            summary_lines.append(f"- **{field.replace('_',' ').title()}**: {value}")

        row["audit_detail_summary"] = "\n".join(map(str, summary_lines))

    for row in data:
        if row["docname"] in submit_map and row["submit_status"] == "No":
            if row["modified"] > submit_map[row["docname"]][0]:
                row["submit_status"] = "After Submit"

    for field in changed_fields:
        if field != "posting_date":
            columns.append({
                "label": _(field.replace("_", " ").title()),
                "fieldname": field,
                "fieldtype": "Data",
                "width": 200,
            })

    columns.append({
        "label": _("Audit Detail Summary"),
        "fieldname": "audit_detail_summary",
        "fieldtype": "Text",
        "width": 500,
    })

    if filters.get("operation"):
        data = [d for d in data if d.get("operation") == filters["operation"]]

    if filters.get("status"):
        data = [d for d in data if d.get("submit_status") == filters["status"]]

    if filters.get("doc_status"):
        data = [d for d in data if d.get("doc_status") == filters["doc_status"]]

    return data