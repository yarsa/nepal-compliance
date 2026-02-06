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
            "label": _("Date"),
            "fieldtype": "Date",
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
            "fieldname": "discount",
            "label": _("Discount Amount"),
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
            "fieldname": "taxable_amount",
            "label": _("Taxable Amount"),
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
    
    data = """
        SELECT
            si.posting_date as posting_date,
            si.name as invoice_number,
            si.customer_name as customer,
            COALESCE(si.vat_number, si.tax_id) as pan_number,
            si.grand_total as total_amount,
            si.discount_amount as discount,
            si.total_taxes_and_charges as vat_amount,
            si.net_total as taxable_amount,
            si.modified_by as cancelled_by
        FROM 
            `tabSales Invoice` si
        WHERE 
            si.docstatus = 2
            AND (si.is_return = 0 OR si.is_return = 1)
            AND {conditions}
        ORDER BY 
            si.creation DESC
    """.format(conditions=conditions)
    
    return frappe.db.sql(data, filters, as_dict=1)

def get_conditions(filters):
    conditions = []

    if filters.get("from_nepali_date"):
        conditions.append("si.posting_date >= %(from_nepali_date)s")
    if filters.get("to_nepali_date"):
        conditions.append("si.posting_date <= %(to_nepali_date)s")
    if filters.get("company"):
        conditions.append("si.company = %(company)s")
    if filters.get("cancelled_by"):
        conditions.append("si.modified_by = %(cancelled_by)s")
    if filters.get("customer_name"):
        conditions.append("customer_name = %(customer_name)s")
        
    return " AND ".join(conditions)
