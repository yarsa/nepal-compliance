import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "cancel_date",
            "label": _("Cancelled Date"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "nepali_date",
            "label": _("Nepali Date"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "invoice_number",
            "label": _("Invoice Number"),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 200
        },
        {
            "fieldname": "customer",
            "label": _("Customer Name"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "pan_number",
            "label": _("PAN/VAT Number"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_amount",
            "label": _("Total Amount"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "taxable_amount",
            "label": _("Taxable Amount"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "vat_amount",
            "label": _("VAT Amount"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "cancelled_by",
            "label": _("Cancelled By"),
            "fieldtype": "Link",
            "options": "User",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT
            si.posting_date, 
            si.modified as cancel_date,
            si.nepali_date as nepali_date,
            si.name as invoice_number,
            si.customer_name as customer,
            si.vat_number as pan_number,
            si.grand_total as total_amount,
            si.net_total as taxable_amount,
            si.total_taxes_and_charges as vat_amount,
            si.modified_by as cancelled_by
        FROM 
            `tabSales Invoice` si
        WHERE 
            si.docstatus = 2
            AND (si.is_return = 0 OR si.is_return = 1)
            AND {conditions}
        ORDER BY 
            si.creation DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date"):
        conditions.append("si.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("si.posting_date <= %(to_date)s")
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
    if filters.get("from_nepali_date"):
        conditions.append("si.nepali_date >= %(from_nepali_date)s")
    if filters.get("to_nepali_date"):
        conditions.append("si.nepali_date <= %(to_nepali_date)s")
    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        
    return " AND ".join(conditions)
