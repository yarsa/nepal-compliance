import frappe
from frappe import _

def execute(filters=None):
    columns, data = [], []
    
    columns = [
        _("Invoice Date") + ":Date:150",
        _("Nepali Date") + ":Data:150",
        _("Customer") + ":Link/Customer:150",
        _("Invoice Number") + ":Link/Sales Invoice:120",
        _("Qty") + ":Float:60",
        _("Amount") + ":Currency:100",
        _("Tax and Charges Added") + ":Currency:120",
        _("Discount") + ":Currency:120",
        _("Total") + ":Currency:120",
        _("Net Total") + ":Currency:120",
        _("Grand Total") + ":Currency:120",
        _("Total Advance") + ":Currency:120",
        _("Outstanding Amount") + ":Currency:120",
        _("Status") + ":Data:80",
    ]
    conditions = "si.docstatus = 1"
    from_date, to_date, from_nepali_date, to_nepali_date, nepali_date = None, None, None, None, None
    
    if filters.get("from_date") and filters.get("to_date"):
        from_date = filters["from_date"]
        to_date = filters["to_date"]
        conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        from_nepali_date = filters["from_nepali_date"]
        to_nepali_date = filters["to_nepali_date"]
        conditions += " AND si.nepali_date BETWEEN %(from_nepali_date)s AND %(to_nepali_date)s"
    
    query = """
        SELECT
            si.posting_date,
            si.nepali_date,
            si.customer,
            si.name AS invoice_number,
            SUM(item.qty) AS total_qty,
            SUM(item.qty * item.rate) AS total_amount,
            si.total_taxes_and_charges AS total_taxes_and_charges,
            si.discount_amount AS discount_amount,
            si.total AS total,
            si.net_total AS net_total,
            si.grand_total AS grand_total,
            si.total_advance AS total_advance,
            si.outstanding_amount AS outstanding_amount,
            si.status
        FROM
            `tabSales Invoice` si
        JOIN
            `tabSales Invoice Item` item ON item.parent = si.name
        WHERE
			{0}
        GROUP BY
            si.name
        ORDER BY
            si.posting_date DESC
    """.format(conditions)

    result = frappe.db.sql(query, values={'from_date': from_date, 'to_date': to_date,'from_nepali_date': from_nepali_date, 'to_nepali_date': to_nepali_date}, as_dict=True)

    for row in result:
        data.append([
            row.posting_date,                         
            row.nepali_date,                          
            row.supplier,                             
            row.invoice_number,                       
            row.total_qty,                           
            row.total_amount,                         
            row.total_taxes_and_charges,              
            row.discount_amount,                      
            row.total,                                
            row.net_total,                            
            row.grand_total,                          
            row.total_advance,                        
            row.outstanding_amount,                   
            row.status                               
        ])
    return columns, data