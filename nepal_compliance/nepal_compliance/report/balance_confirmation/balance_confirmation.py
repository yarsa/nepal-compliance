# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {
            "fieldname": "party_type",
            "label": _("Party Type"),
            "fieldtype": "Link",
            "options": "Party Type",
            "width": 120
        },
        {
            "fieldname": "party",
            "label": _("Party"),
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 180
        },
        {
            "fieldname": "opening_debit",
            "label": _("Opening (Dr)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "opening_credit",
            "label": _("Opening (Cr)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "debit",
            "label": _("Debit"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "credit",
            "label": _("Credit"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "closing_debit",
            "label": _("Closing (Dr)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "closing_credit",
            "label": _("Closing (Cr)"),
            "fieldtype": "Currency",
            "width": 120
        },
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    gl_entries = get_gl_entries(conditions, filters)
    data = []
    
    for gle in gl_entries:
        row = {
            "party_type": gle.party_type,
            "party": gle.party,
            "opening_debit": gle.opening_debit,
            "opening_credit": gle.opening_credit,
            "debit": gle.debit,
            "credit": gle.credit,
            "closing_debit": gle.closing_debit,
            "closing_credit": gle.closing_credit,
        }
        data.append(row)
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("company"):
        conditions.append("company = %(company)s")
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
    elif filters.get("from_date") and filters.get("to_date"):
        conditions.append("posting_date BETWEEN %(from_date)s AND %(to_date)s")
    if filters.get("party_type"):
        conditions.append("party_type = %(party_type)s")
    if filters.get("party"):
        conditions.append("party = %(party)s")

    return " AND ".join(conditions)

def get_gl_entries(conditions, filters):
    date_field = "posting_date"
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    return frappe.db.sql("""
        WITH OpeningBalance AS (
            SELECT 
                party_type,
                party,
                SUM(IF({date_field} < %(from_date)s AND is_cancelled = 0, debit, 0)) as opening_debit,
                SUM(IF({date_field} < %(from_date)s AND is_cancelled = 0, credit, 0)) as opening_credit
            FROM `tabGL Entry`
            WHERE {conditions}
            GROUP BY party_type, party
        ),
        CurrentTransactions AS (
            SELECT 
                party_type,
                party,
                SUM(IF(is_cancelled = 0, debit, 0)) as debit,
                SUM(IF(is_cancelled = 0, credit, 0)) as credit
            FROM `tabGL Entry`
            WHERE {date_field} BETWEEN %(from_date)s AND %(to_date)s
            AND {conditions}
            GROUP BY party_type, party
        )
        SELECT 
            ob.party_type,
            ob.party,
            ob.opening_debit,
            ob.opening_credit,
            COALESCE(ct.debit, 0) as debit,
            COALESCE(ct.credit, 0) as credit,
            (ob.opening_debit + COALESCE(ct.debit, 0) - COALESCE(ct.credit, 0)) as closing_debit,
            (ob.opening_credit + COALESCE(ct.credit, 0) - COALESCE(ct.debit, 0)) as closing_credit
        FROM OpeningBalance ob
        LEFT JOIN CurrentTransactions ct
        ON ob.party_type = ct.party_type AND ob.party = ct.party
        ORDER BY ob.party_type, ob.party
    """.format(
        conditions=conditions,
        date_field=date_field
    ), {
        "from_date": from_date,
        "to_date": to_date,
        **filters
    }, as_dict=1)

def get_pan_number(party_type, party):
    if party_type == "Supplier":
        return frappe.db.get_value("Supplier", party, "tax_id")
    elif party_type == "Customer":
        return frappe.db.get_value("Customer", party, "tax_id")
    return ""

def get_party_address(party_type, party):
    address = frappe.db.sql("""
        SELECT 
            addr.address_line1,
            addr.city,
            addr.country
        FROM `tabAddress` addr
        INNER JOIN `tabDynamic Link` dl
        ON dl.parent = addr.name
        WHERE 
            dl.link_doctype = %s
            AND dl.link_name = %s
            AND addr.is_primary_address = 1
        LIMIT 1
    """, (party_type, party), as_dict=1)
    
    if address:
        return f"{address[0].address_line1}, {address[0].city}, {address[0].country}"
    return ""