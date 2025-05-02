# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils.data import (
    format_date,
    format_datetime,
    get_timespan_date_range,
    get_user_date_format,
    getdate,
)

from nepal_compliance.nepal_compliance.report.materialized_report.utils import get_purchase_sales_doctype
DOC = {
    "supplier_name": [
        "Purchase Invoice",
        "Purchase Receipt",
    ],
    "customer_name": [
        "Sales Invoice",
    ],
    "grand_total": [
        "Purchase Invoice",
        "Sales Invoice",
    ],
    "remark_field": [
        "Purchase Invoice",
        "Sales Invoice",
    ],
}

def execute(filters=None):
    _class = Materialized[filters.pop("materialized_report")](filters)
    return _class.get_columns(), _class.get_data()


class BaseAuditTrail:
    def __init__(self, filters) -> None:
        self.filters = filters

    def get_columns(self):
        pass

    def get_data(self):
        pass

    def append_rows(self, doctype):
        pass

    def get_conditions(self):
        conditions = {}
        conditions["company"] = self.filters.get("company")

        sync_with_ird = self.filters.get("sync_with_ird")
        if sync_with_ird == "Yes":
            conditions["docstatus"] = ["in", [1, 2]]
        elif sync_with_ird == "No":
            conditions["docstatus"] = 0

        if self.filters.get("party_name"):
            if self.filters.get("doctype") in DOC["supplier_name"]:
                conditions["supplier_name"] = ["like", f"%{self.filters['party_name']}%"]
            elif self.filters.get("doctype") in DOC["customer_name"]:
                conditions["customer_name"] = ["like", f"%{self.filters['party_name']}%"]

        return conditions

    def get_doctypes(self):
            doctypes = list(get_purchase_sales_doctype())
            return doctypes

class ColumnDetail(BaseAuditTrail):
    def get_columns(self):
        columns = [
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
                "label": _("VAT/PAN Number"),
                "fieldtype": "Data",
                "fieldname": "vat_number",
                "width": 150
            },
		    {
                'fieldname': 'vat',
                'label': _('VAT'),
                'fieldtype': 'Float'
		    },
		    {
                'fieldname': 'tds',
                'label': _('TDS'),
                'fieldtype': 'Float'
		    },
            {
                "label": _("Amount"),
                "fieldtype": "Int",
                "fieldname": "amount",
                "width": 80,
            },
            {
                "label": _("Status"),
                "fieldtype": "Data",
                "fieldname": "status",
                "width": 150,
            },
            {
                "label": _("Created By"),
                "fieldtype": "Link",
                "fieldname": "created_by",
                "options": "User",
                "width": 150,
            },
            {
                "label": _("Is Bill Printed"),
                "fieldtype": "Check",
                "fieldname": "is_bill_printed",
                "width": 120,
            },
            {
                "label": _("Printed By"),
                "fieldtype": "Link",
                "fieldname": "printed_by",
                "options": "User",
                "width": 150
            },
            {
                "label": _("Remarks"),
                "fieldtype": "Data",
                "fieldname": "remarks",
                "width": 180,
            },
        ]
        doctype = self.filters.get("doctype")
        if doctype != "Purchase Invoice":
            columns.append({
            "label": _("Sync with IRD"),
            "fieldtype": "Check",
            "fieldname": "sync_with_ird",
            "width": 120
        })

        return columns

    def get_data(self):
        self.data = []
        conditions = self.get_conditions()
        sync_with_ird = self.filters.get("sync_with_ird")

        if doctype := self.filters.get("doctype"):
            doctypes = [doctype]
        else:
            doctypes = self.get_doctypes()
            if sync_with_ird == "Yes":
                doctypes = [dt for dt in doctypes if dt != "Purchase Invoice"]

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
            "docstatus"
        ]

        if doctype in DOC["grand_total"]:
            fields.append("grand_total as amount")

        if doctype in DOC["supplier_name"]:
            fields.append("supplier_name as party_name")
            fields.append("vat_number")
            fields.append("")

        elif doctype in DOC["customer_name"]:
            fields.append("customer_name as party_name")
            fields.append("vat_number")


        if doctype in DOC["remark_field"]:
            fields.append("remarks")
        
        fields.append("nepali_date")
        
        fields.append("status")

        return fields

    def append_rows(self, records, doctype):
        for row in records:
            row["doctype"] = doctype
            row["creation_date"] = getdate(
                format_date(row["date_time"], get_user_date_format())
            )
            row["nepali_date"] = row.get("nepali_date", "") 
            row["status"] = row.get("status", "")
            print_count = 0
            printed_by_user = ""
            if doctype in ["Purchase Invoice", "Sales Invoice"]:
                print_count = frappe.db.count("Access Log",{
                "reference_document": row["document_name"],
                "file_type": "PDF",
                "method": "Print",
            })
            if print_count > 0:
                access_logs = frappe.db.get_all("Access Log", filters={
                "reference_document": row["document_name"],
                "file_type": "PDF",
                "method": "Print",
            }, fields=["user"], limit=1, order_by="creation desc")
            
                if access_logs:
                    printed_by_user = access_logs[0]["user"]

            row["is_bill_printed"] = 1 if print_count > 0 else 0
            row["printed_by"] = printed_by_user

            if self.filters.get("doctype") != "Purchase Invoice":
                row["sync_with_ird"] = 1 if doctype == "Sales Invoice" and row.get("docstatus") in [1, 2] else 0
                
            vat = 0.0
            tds = 0.0

            if doctype == "Purchase Invoice":
                purchase_taxes = frappe.db.get_all("Purchase Taxes and Charges", filters={"parent": row["document_name"]}, fields=['*'])
                for tax in purchase_taxes:
                    if tax.rate == 13:  
                        vat += (tax.tax_amount if tax.tax_amount else 0.0)
                    elif tax.rate in [1.5, 15]: 
                        tds += (tax.tax_amount if tax.tax_amount else 0.0)
            if doctype == "Sales Invoice":
                sales_taxes = frappe.db.get_all("Sales Taxes and Charges", filters={"parent": row["document_name"]}, fields=['*'])
                for tax in sales_taxes:
                    if tax.rate == 13: 
                        vat += (tax.tax_amount if tax.tax_amount else 0.0)
                    elif tax.rate in [1.5, 15]:
                       tds += (tax.tax_amount if tax.tax_amount else 0.0)
                       
            row["vat"] = vat
            row["tds"] = tds

            if doctype in DOC["supplier_name"]:
                row["party_type"] = "Supplier"

            elif doctype in DOC["customer_name"]:
                row["party_type"] = "Customer"

            self.data.append(row)
            
@frappe.whitelist()
def get_relavant_doctypes():
    doctypes = get_purchase_sales_doctype()
    return doctypes

Materialized = {
    "Materialized View": ColumnDetail,
}