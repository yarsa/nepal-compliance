import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    columns, data = [], []
    columns = [
        _("Invoice Date") + ":Date:150",
        _("Nepali Date") + ":Data:150",
        _("Supplier") + ":Link/Supplier:150",
        _("Invoice Number") + ":Link/Purchase Invoice:120",
        _("Item Code") + ":Link/Item:120",
        _("Item Name") + ":Data:150",
        _("Qty") + ":Float:60",
        _("Rate") + ":Currency:80",
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

    query = """
        SELECT
            pi.posting_date,
            pi.nepali_date,
            pi.supplier,
            pi.name AS invoice_number,
            item.item_code,
            item.item_name,
            item.qty,
            item.rate,
            (item.qty * item.rate) AS amount,
            pi.taxes_and_charges_added,
            pi.discount_amount,
            pi.total,
            pi.net_total,
            pi.grand_total,
            pi.total_advance,
            pi.outstanding_amount,
            pi.status
        FROM
            `tabPurchase Invoice` pi
        JOIN
            `tabPurchase Invoice Item` item ON item.parent = pi.name
        {0}
        ORDER BY pi.posting_date DESC
    """.format(conditions)
    
    result = frappe.db.sql(query, as_dict=True)

    invoice_totals = {}
    current_invoice = None

    overall_totals = {
        "qty": 0,
        "rate": 0,
        "amount": 0,
    }