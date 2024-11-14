from __future__ import unicode_literals
import frappe

def execute(filters=None):
    columns = [
        {
            'fieldname': 'date',
            'label': _('Date'),
            'fieldtype': 'Date'
        },
        {
            'fieldname': 'nepali_date',
            'label': _('Nepali Date'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'invoice_no',
            'label': _('Invoice No'),
            'fieldtype': 'Link',
            'options': 'Purchase Invoice'
        },
        {
            'fieldname': 'supplier',
            'label': _('Supplier Name'),
            'fieldtype': 'Link',
            'options': 'Supplier'
        },
        {
            'fieldname': 'bill_no',
            'label': _('Supplier Invoice No'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'vat_no',
            'label': _('Vat No'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'item_descriotion',
            'label': _('Item Description'),
            'fieldtype': 'Text'
        },
        {
            'fieldname': 'unit',
            'label': _('Unit'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'qty',
            'label': _('Quantity'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'rate',
            'label': _('Rate/Unit'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'gross_amount',
            'label': _('Gross Amount'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'net_amount',
            'label': _('Net Amount'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'vat',
            'label': _('13% VAT'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'invoice_total',
            'label': _('Invoice Total'),
            'fieldtype': 'Data'
        }

    ]
    data = []
    conditions = {"docstatus": 1, "is_return": 0}
    if filters.get("company"):
        conditons["company"] = filters["company"]
    if filters.get("supplier"):
        conditions["supplier"] = filters["supplier"]
    if filter.get("bill_no"):
        bill_no_filter = f"%{filters["bill_no"]}%"
        conditions["bill_no"] = ["like", bill_no_filter]
    if filters.get("bill_date"):
        conditions["bill_date"] = filters["bill_date"]
    if filter.get("due_date"):
        conditions["due_date"] = filters["due_date"]
    if filter.get("nepali_date"):
        nepali_date_filter = f"%{filter['nepali_date']}%"
        conditions["nepali_date"] = ["like", nepali_date_filter]
        
    
    purchase_invoice = frappe.db.get_list("Purchase Invoice", filters = conditions, fields)
    return columns, data 
