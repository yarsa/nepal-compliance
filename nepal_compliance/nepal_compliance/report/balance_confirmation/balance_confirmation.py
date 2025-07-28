# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime


def execute(filters=None):
    filters = filters or {}

    filters["from_date"], filters["to_date"] = get_dynamic_date_range()

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
        data.append({
            "party_type": gle.party_type,
            "party": gle.party,
            "opening_debit": gle.opening_debit,
            "opening_credit": gle.opening_credit,
            "debit": gle.debit,
            "credit": gle.credit,
            "closing_debit": gle.closing_debit,
            "closing_credit": gle.closing_credit,
        })

    return data


def get_conditions(filters):
    conditions = []

    if filters.get("company"):
        conditions.append("company = %(company)s")
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
    if filters.get("party_type"):
        conditions.append("party_type = %(party_type)s")
    if filters.get("party"):
        conditions.append("party = %(party)s")

    return " AND ".join(conditions)


def get_gl_entries(conditions, filters):
    return frappe.db.sql(f"""
        WITH OpeningBalance AS (
            SELECT 
                party_type,
                party,
                SUM(IF(posting_date < %(from_date)s AND is_cancelled = 0, debit, 0)) as opening_debit,
                SUM(IF(posting_date < %(from_date)s AND is_cancelled = 0, credit, 0)) as opening_credit
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
            WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND {conditions}
            GROUP BY party_type, party
        )
        SELECT 
            ob.party_type,
            ob.party,
            COALESCE(ob.opening_debit, 0) as opening_debit,
            COALESCE(ob.opening_credit, 0) as opening_credit,
            COALESCE(ct.debit, 0) as debit,
            COALESCE(ct.credit, 0) as credit,
            (COALESCE(ob.opening_debit, 0) + COALESCE(ct.debit, 0) - COALESCE(ct.credit, 0)) as closing_debit,
            (COALESCE(ob.opening_credit, 0) + COALESCE(ct.credit, 0) - COALESCE(ct.debit, 0)) as closing_credit
        FROM OpeningBalance ob
        LEFT JOIN CurrentTransactions ct
            ON ob.party_type = ct.party_type AND ob.party = ct.party
        ORDER BY ob.party_type, ob.party
    """, filters, as_dict=1)


def get_dynamic_date_range():
    try:
        result = frappe.db.sql("""
            SELECT MIN(posting_date) as min_date, MAX(posting_date) as max_date
            FROM `tabGL Entry`
            WHERE is_cancelled = 0
        """, as_dict=1)

        if result and result[0].min_date and result[0].max_date:
            return result[0].min_date, result[0].max_date

    except Exception as e:
        frappe.log_error("Balance Confirmation Report: " + str(e))

    return "2020-01-01", "2999-12-31"
