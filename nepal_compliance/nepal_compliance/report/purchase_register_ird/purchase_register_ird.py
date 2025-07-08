# Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
    """
    Generates the purchase register report columns and data based on provided filters.
    
    Parameters:
        filters (dict, optional): Criteria to filter the report data, such as company, supplier, document number, and date range.
    
    Returns:
        tuple: A pair containing the list of column definitions and the corresponding report data rows.
    """
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    """
    Return the column definitions for the purchase register report with Nepali tax-related fields.
    
    Returns:
        list: A list of dictionaries specifying each report column's label (in Nepali), field name, type, and width.
    """
    return [
        {"label": _("मिति"), "fieldname": "nepali_date", "fieldtype": "Data", "width": 120},
        # {"label": "बीजक नं.", "fieldname": "invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 100},
        {"label": _("बीजक नं."), "fieldname": "invoice", "fieldtype": "Data", "width": 200},
        {"label": _("प्रज्ञापनपत्र नं."), "fieldname": "customs_declaration_number", "fieldtype": "Data", "width": 130},
        {"label": _("आपूर्तिकर्ताको नाम"), "fieldname": "supplier_name", "fieldtype": "Data", "width": 160},
        {"label": _("आपूर्तिकर्ताको स्थायी लेखा नम्बर"), "fieldname": "pan", "fieldtype": "Data", "width": 120},
        {"label": _("जम्मा खरिद मूल्य (रु)"), "fieldname": "total", "fieldtype": "Float", "width": 120},
        {"label": _("कर छुट हुने वस्तु वा सेवाको खरिद / पैठारी मूल्य (रु)"), "fieldname": "tax_exempt", "fieldtype": "Float", "width": 100},
        {"label": _("करयोग्य खरिद (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य खरिद (पूंजीगत बाहेक) कर (रु)"), "fieldname": "tax_amount", "fieldtype": "Float", "width": 120},
        {"label": _("करयोग्य पैठारी (पूंजीगत बाहेक) मूल्य (रु)"), "fieldname": "taxable_import_non_capital_amount", "fieldtype": "Float", "width": 140},
        {"label": _("करयोग्य पैठारी (पूंजीगत बाहेक) कर (रु)"), "fieldname": "taxable_import_non_capital_tax", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य खरिद / पैठारी मूल्य (रु)"), "fieldname": "capital_taxable_amount", "fieldtype": "Float", "width": 140},
        {"label": _("पूंजीगत करयोग्य खरिद / पैठारी कर (रु)"), "fieldname": "capital_taxable_tax", "fieldtype": "Float", "width": 140},
    ]

def get_data(filters):
    """
    Fetches and categorizes purchase invoice data for the report based on provided filters.
    
    For each submitted, non-return purchase invoice matching the filters, retrieves invoice details and classifies item amounts into tax-exempt, taxable domestic non-capital, taxable import non-capital, and capital taxable categories. Calculates tax amounts for each category at a fixed 13% rate if taxable. Returns a list of dictionaries, each representing a report row with invoice and tax breakdown details.
    
    Parameters:
        filters (dict): Dictionary of filter criteria such as company, supplier, document number, and Nepali date range.
    
    Returns:
        list: List of dictionaries containing invoice details and categorized tax information for the report.
    """
    conditions = ["pi.docstatus = 1 and pi.is_return = 0"]
    values = {}

    if filters.get("company"):
        conditions.append("pi.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("supplier"):
        conditions.append("pi.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    if filters.get("document_number"):
        conditions.append("pi.name = %(document_number)s")
        values["document_number"] = filters.get("document_number")

    if filters.get("from_nepali_date") and filters.get("to_nepali_date"):
        conditions.append("pi.nepali_date BETWEEN %(from)s AND %(to)s")
        values["from"] = filters.get("from_nepali_date")
        values["to"] = filters.get("to_nepali_date")
    elif filters.get("from_nepali_date"):
        conditions.append("pi.nepali_date >= %(from)s")
        values["from"] = filters.get("from_nepali_date")
    elif filters.get("to_nepali_date"):
        conditions.append("pi.nepali_date <= %(to)s")
        values["to"] = filters.get("to_nepali_date")

    query = f"""
        SELECT
            pi.name as invoice, pi.bill_no, pi.customs_declaration_number, pi.rounded_total, pi.nepali_date, pi.supplier_name, pi.tax_id as pan,
            pi.total, pi.total_taxes_and_charges as total_tax
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabSupplier` s ON pi.supplier = s.name
        WHERE {' AND '.join(conditions)}
        ORDER BY pi.posting_date
    """

    invoices = frappe.db.sql(query, values, as_dict=True)
    data = []

    for inv in invoices:
        supplier_country = frappe.db.get_value("Supplier", inv.supplier_name, "country") or ""
        is_import = supplier_country.strip().lower() != "nepal"

        tax_exempt = taxable_domestic_nc = taxable_import_nc = capital_taxable_amount = 0.0

        item_filters = {"parent": inv.invoice}

        items = frappe.get_all("Purchase Invoice Item", filters=item_filters,
            fields=["is_nontaxable_item", "net_amount", "amount", "asset_category"])

        for item in items:
            amt = flt(item.get("net_amount") or item.get("amount"))

            if item.get("is_nontaxable_item"):
                tax_exempt += amt
                continue

            if item.get("asset_category"):
                capital_taxable_amount += amt
            else:
                if is_import:
                    taxable_import_nc += amt
                else:
                    taxable_domestic_nc += amt

        total_taxable = taxable_domestic_nc + taxable_import_nc + capital_taxable_amount
        total_tax = flt(inv.total_tax)

        # tax_domestic_nc = (taxable_domestic_nc / total_taxable) * total_tax if total_taxable else 0
        tax_domestic_nc = taxable_domestic_nc * 0.13 if total_taxable else 0  
        # tax_import_nc = (taxable_import_nc / total_taxable) * total_tax if total_taxable else 0
        tax_import_nc = taxable_import_nc * 0.13 if total_taxable else 0 
        # tax_capital = (capital_taxable_amount / total_taxable) * total_tax if total_taxable else 0
        tax_capital = capital_taxable_amount * 0.13 if total_taxable else 0 

        data.append({
            "nepali_date": inv.nepali_date or inv.posting_date,
            "invoice": inv.bill_no if inv.bill_no else inv.invoice,
            "customs_declaration_number": inv.customs_declaration_number if is_import else "",
            "supplier_name": inv.supplier_name,
            "pan": inv.pan,
            "total": inv.rounded_total,
            "tax_exempt": tax_exempt,
            "taxable_amount": taxable_domestic_nc,
            "tax_amount": tax_domestic_nc,
            "taxable_import_non_capital_amount": taxable_import_nc,
            "taxable_import_non_capital_tax": tax_import_nc,
            "capital_taxable_amount": capital_taxable_amount,
            "capital_taxable_tax": tax_capital
        })

    return data
