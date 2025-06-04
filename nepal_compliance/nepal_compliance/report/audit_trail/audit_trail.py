# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

def execute(filters=None):
	columns, data = [], []
	return columns, data

import frappe
from frappe import _
from frappe.utils.data import (
    format_date,
    format_datetime,
    get_timespan_date_range,
    get_user_date_format,
    getdate,
)

from nepal_compliance.nepal_compliance.report.audit_trail.utils import get_audit_trail_doctypes

DoctypeFields = {
    "customer_name": [
        "Delivery Note",
        "Dunning",
        "POS Invoice",
        "Sales Invoice",
    ],
    "grand_total": [
        "Dunning",
        "Delivery Note",
        "Expense Claim"
        "Purchase Invoice",
        "Purchase Receipt",
        "POS Invoice",
        "Sales Invoice",
    ],
    "no_name": [
        "Account Settings",
        "Asset",
        "Asset Repair",
        "Landed Cost Voucher",
        "Period Closing Voucher",
        "Process Deferred Accounting",
    ],
    "remarks_field": [
        "Purchase Invoice",
        "Purchase Receipt",
        "Payment Entry",
        "POS Invoice",
        "Stock Entry",
        "Subcontracting Receipt",
        "Sales Invoice",
        "Period Closing Voucher",
    ],
    "supplier_name": [
        "Purchase Invoice",
        "Purchase Receipt",
        "Stock Entry",
        "Subcontracting Receipt",
    ],
    "total_amount": [
        "Invoice Discounting",
        "Journal Entry",
        "Stock Entry",
    ]
}

def execute(filters=None):
    _class = REPORT_CLASSES_BY_TYPE[filters.pop("report")](filters)
    return _class.get_columns(), _class.get_data()

class BaseAuditTrail:
    def __init__(self, filters) -> None:
        self.filters = filters

    def get_columns(self):
        pass

    def get_data(self):
        pass

    def append_rows(self, new_count, modified_count, doctype):
        pass
    
    def get_conditions(self):
        conditions = []
        date_option = self.filters.get("date_option")
        doctype = self.filters.get("doctype")
    
        if date_option == "Nepali Date Filter":
            from_np = self.filters.get("from_nepali_date")
            to_np = self.filters.get("to_nepali_date")

            if from_np and to_np:
                conditions.append(["nepali_date", ">=", from_np])
                conditions.append(["nepali_date", "<=", to_np])
            elif from_np:
                conditions.append(["nepali_date", ">=", from_np])
            elif to_np:
                conditions.append(["nepali_date", "<=", to_np])

        else:
            date_condition = self.get_date()
            if date_condition:
                conditions.append(["modified", date_condition[0], date_condition[1]])
            
        owner = self.get_user()
        if owner:
            if isinstance(owner, list) and len(owner) == 3:
                conditions.append(owner)
            elif isinstance(owner, list) and len(owner) == 2:
                conditions.append(["owner"] + owner)
            else:
                conditions.append(["owner", "=", owner])

        company = self.filters.get("company")
        if company:
            conditions.append(["company", "=", company])

        return conditions

    def get_date(self):
        date_option = self.filters.pop("date_option", None)
        date_range = self.filters.pop("date_range", None)
        if date_option == "Custom":
            return ["between", date_range]
        else:
            date_range = [get_timespan_date_range(date_option.lower())][0]
            return ("between", date_range)
        
    def get_date_field(self, doctype):
        if doctype:
            if self.field_exists(doctype, "posting_date"):
                return "posting_date"
            elif self.field_exists(doctype, "transaction_date"):
                return "transaction_date"
        return "modified"

    def get_user(self):
        if self.filters.get("user"):
            return self.filters["user"]
        else:
            users = frappe.get_all("User", pluck="name")
            return ["in", users]

    def get_doctypes(self):
        doctypes = list(get_relevant_doctypes())
        return doctypes

    def update_count(self):
        fields = ["owner as user_name", "count(name) as count"]
        self.filters["creation"] = self.get_date()

        if doctype := self.filters.pop("doctype", None):
            doctypes = [doctype]
        else:
            doctypes = self.get_doctypes()

        if user := self.filters.pop("user", None):
            self.filters["owner"] = user

        filters = self.filters.copy()
        del filters["company"]

        for doctype in doctypes:
            new_count = frappe.get_all(
                doctype,
                filters=self.filters,
                fields=fields,
                group_by=self.group_by,
            )

            modified_count = frappe.get_all(
                "Version",
                filters={**filters, "ref_doctype": doctype},
                fields=fields,
                group_by=self.group_by,
            )

            self.append_rows(new_count, modified_count, doctype)

    def field_exists(self, doctype, fieldname):
        meta = frappe.get_meta(doctype)
        return fieldname in [field.fieldname for field in meta.fields]

class ReportSummary(BaseAuditTrail):
    def get_columns(self):
        columns = [
            {
                "label": _("Date and Time"),
                "fieldtype": "DateTime",
                "fieldname": "date_time",
                "width": 160,
            },
            {
                "label": _("DocType"),
                "fieldtype": "Data",
                "fieldname": "doctype",
                "width": 120,
            },
            {
                "label": _("Document Name"),
                "fieldtype": "Dynamic Link",
                "fieldname": "document_name",
                "width": 200,
                "options": "doctype",
            },
            {
                "label": _("Creation Date"),
                "fieldtype": "Date",
                "fieldname": "creation_date",
                "width": 120,
            },
            {
                "label": _("Posting Date"),
                "fieldtype": "Date",
                "fieldname": "posting_date",
                "width": 120,
            },
            {
                "label": _("Nepali Date"),
                "fieldtype": "Data", 
                "fieldname": "nepali_date",
                 "width": 120,
            },
            {
                "label": _("Party Type"),
                "fieldtype": "Data",
                "fieldname": "party_type",
                "width": 100,
            },
            {
                "label": _("Party Name"),
                "fieldtype": "Dynamic Link",
                "fieldname": "party_name",
                "width": 150,
                "options": "party_type",
            },
            {
                "label": _("Amount"),
                "fieldtype": "Int",
                "fieldname": "amount",
                "width": 80,
            },
            {
                "label": _("Created By"),
                "fieldtype": "Link",
                "fieldname": "created_by",
                "options": "User",
                "width": 150,
            },
            {
                "label": _("Modified By"),
                "fieldtype": "Link",
                "fieldname": "modified_by",
                "options": "User",
                "width": 150,
            },
            {
                "label": _("Remarks"),
                "fieldtype": "Data",
                "fieldname": "remarks",
                "width": 180,
            },
        ]

        return columns

    def get_data(self):
        self.data = []
        conditions = self.get_conditions()

        if doctype := self.filters.get("doctype"):
            doctypes = [doctype]
        else:
            doctypes = self.get_doctypes()

        for doctype in doctypes:
            fields = self.get_fields(doctype)
            records = frappe.get_all(doctype, fields=fields, filters=conditions)
            self.append_rows(records, doctype)

        return self.data

    def get_fields(self, doctype):
        fields = [
            "modified as date_time",
            "company",
            "name as document_name",
            "owner as created_by",
            "modified_by as modified_by",
        ]
        if self.field_exists(doctype, 'nepali_date'):
            fields.append("nepali_date") 

        date_field = self.get_date_field(doctype)
        if self.field_exists(doctype, date_field):
            fields.append(date_field)
            
        if doctype == "Purchase Invoice":
            fields.append("grand_total as amount")
            
        if doctype == "Payment Entry":
            fields.extend(
                ["party_type", "party_name", "total_allocated_amount as amount"]
            )

        if doctype == "Subcontracting Receipt":
            fields.append("total as amount")

        elif doctype in DoctypeFields["grand_total"]:
            fields.append("grand_total as amount")

        elif doctype in DoctypeFields["total_amount"]:
            fields.append("total_amount as amount")

        if doctype in DoctypeFields["supplier_name"]:
            fields.append("supplier_name as party_name")

        elif doctype in DoctypeFields["customer_name"]:
            fields.append("customer_name as party_name")

        if doctype == "Journal Entry":
            fields.append("user_remark as remarks")
            fields.append("total_debit as amount")

        elif doctype in DoctypeFields["remarks_field"]:
            fields.append("remarks")

        return fields

    def append_rows(self, records, doctype):
        for row in records:
            row["date_time"] = format_datetime(row["date_time"])
            row["doctype"] = doctype
            row["creation_date"] = getdate(
                format_date(row["date_time"], get_user_date_format())
            )
            row["posting_date"] = row.get("posting_date") or row.get("transaction_date", "")
            row["nepali_date"] = row.get("nepali_date", "")  
            
            if doctype in DoctypeFields["no_name"]:
                row["party_name"] = ""
                row["amount"] = ""

            elif doctype in DoctypeFields["supplier_name"]:
                row["party_type"] = "Supplier"

            elif doctype in DoctypeFields["customer_name"]:
                row["party_type"] = "Customer"

            self.data.append(row)

class DocTypeReport(BaseAuditTrail):
    def get_columns(self):
        columns = [
            {
                "label": _("DocType"),
                "fieldtype": "Data",
                "fieldname": "doctype",
                "width": 150,
            },
            {
                "label": _("New Records"),
                "fieldtype": "Data",
                "fieldname": "new_count",
                "width": 150,
            },
            {
                "label": _("Modified Records"),
                "fieldtype": "Data",
                "fieldname": "modify_count",
                "width": 150,
            },
        ]

        return columns

    def get_data(self):
        self.data = {}
        self.group_by = ""
        self.update_count()
        return list(self.data.values())

    def append_rows(self, new_records, modified_records, doctype):
        new_count = modify_count = 0
        for row in new_records:
            new_count += row["count"]

        for row in modified_records:
            modify_count += row["count"]

        if not (new_count or modify_count):
            return

        row = {"doctype": doctype, "new_count": new_count, "modify_count": modify_count}
        self.data.setdefault(doctype, row)
    
class UserReport(BaseAuditTrail):
    def get_columns(self):
        columns = [
            {
                "label": _("User"),
                "fieldtype": "Link",
                "fieldname": "user_name",
                "options": "User",
                "width": 200,
            },
            {
                "label": _("New Records"),
                "fieldtype": "Data",
                "fieldname": "new_count",
                "width": 150,
            },
            {
                "label": _("Modified Records"),
                "fieldtype": "Data",
                "fieldname": "modify_count",
                "width": 150,
            },
        ]

        return columns

    def get_data(self):
        self.data = {}
        self.group_by = "owner"
        self.update_count()

        return list(self.data.values())

    def append_rows(self, new_records, modified_records, doctype):
        for row in new_records:
            user_name = row["user_name"]
            user_count = self.data.setdefault(
                user_name,
                {
                    "user_name": user_name,
                    "new_count": 0,
                    "modify_count": 0,
                },
            )

            user_count["new_count"] += row["count"]

        for row in modified_records:
            user_name = row["user_name"]
            user_count = self.data.setdefault(
                user_name,
                {
                    "user_name": user_name,
                    "new_count": 0,
                    "modify_count": 0,
                },
            )

            user_count["modify_count"] += row["count"]


@frappe.whitelist()
def get_relevant_doctypes():
    doctypes = get_audit_trail_doctypes()
    return doctypes


REPORT_CLASSES_BY_TYPE = {
    "Detail Report": ReportSummary,
    "DocType Summary": DocTypeReport,
    "User Summary": UserReport,
}