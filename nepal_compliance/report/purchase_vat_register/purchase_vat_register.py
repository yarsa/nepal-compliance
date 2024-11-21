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
            'fieldtype': 'supplier_invoice_date',
		    'label': _('Supplier Invoice Date'),
		    'fieldtype': 'Date'
	    },
        {
            'fieldname': 'vat_no',
            'label': _('Vat No'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'item_code',
            'label': _('Item Code'),
            'fieldtype': 'Link',
            'options': 'Item'
        },
        {
            'fieldname': 'item_name',
            'label': _('Item Name'),
            'fiedltype': 'Link',
            'options': 'Item'
        },
        {
            'fieldname': 'item_description',
            'label': _('Item Description'),
            'fieldtype': 'Text'
        },
        {
            'fieldname': 'unit',
            'label': _('Unit'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'total',
            'label': _(''),
            'fieldtype': 'Data',
            'width': 150
        },
        {
            'fieldname': 'qty',
            'label': _('Quantity'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'rate',
            'label': _('Rate'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'amount',
            'label': _('Amount'),
            'fieltype': 'Data'
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
            'fiedlname': 'expense_account',
            'label': _('Expense Account'),
            'fieldtype': 'Data'
        },
        {
            'fiedlname': 'warehouse',
            'label': _('Warehouse'),
            'fiedltype': 'Link',
            'options': 'warehouse'
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
        },
        {
            'fieldname': 'outstanding_amount',
            'label': _('Outstanding Amount'),
            'fieldtype': 'Data'
        },
        {
            'fieldname': 'total_tax_and_charges',
            'label': _('Total Tax and Charges'),
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
        bill_no_filter = f"%{filters['bill_no']}%"
        conditions["bill_no"] = ["like", bill_no_filter]
    if filters.get("bill_date"):
        conditions["bill_date"] = filters["bill_date"]
    if filter.get("due_date"):
        conditions["due_date"] = filters["due_date"]
    if filter.get("nepali_date"):
        nepali_date_filter = f"%{filter['nepali_date']}%"
        conditions["nepali_date"] = ["like", nepali_date_filter]
	if filters.get("expense_account"):
		account_filter = f"%{filters['expense_account']}%"
		conditions["expense_account"] = ["like", account_filter]
	if filters.get("warehouse"):
		conditions["warehouse"] = filters["warehouse"]
    if filters.get("name"):
        conditions["name"] = filters["name"]   
         
    purchase_invoice = frappe.db.get_list("Purchase Invoice", filters = conditions, fields=['*'])
    for purchase in purchase_invoice:
        items = frappe.db.get_all("Purchase Invoice Item", filters={"parent":purchase.name}, fields=['*'])
        total = 0
        total_qty = 0
        total_rate = 0
        gross_amount = 0
        sum_gross_amount = 0
        vat = 0
        sum_vat = 0
        for item in items:
            total += item.amount
            gross_amount += item.amount
            sum_gross_amount += gross_amount
            vat = gross_amount * 13/100
            sum_vat += vat
            total_qty += item.qty
            total_rate += item.rate
            data.append([purchase.posting_date, purchase.nepali_date, purchase.name, purchase.supplier, purchase.bill_no, purchase.bill_date, '', item.item_code, item.item_name, item.description, item.uom, '', item.qty, item.rat, item.amount, gross_amount, '', item.expense_account, item.warehouse, vat, '', '', ''])
        data.append(['', '', '', '', '', '', '', '', '', '', '', 'Total', total_qty, total_rat, total, sum_gross_amount, purchase.grand_total, '', '', sum_vat, purchase.total, purchae.outstanding_amount, purchase.taxes_and_charges_added])  
    return columns, data 
