# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate
from datetime import datetime, timedelta
from nepali_datetime import date as nepali_date


def execute(filters=None):
    if not filters:
        filters = {}

    nepali_month = filters.get("nepali_month")
    if nepali_month:
        from_date, to_date = get_english_date_range_from_nepali_month(nepali_month)
        filters["from_date"] = from_date
        filters["to_date"] = to_date
    else:
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
    """.format(
        conditions=conditions,
        date_field=date_field
    ), {
        "from_date": from_date,
        "to_date": to_date,
        **filters
    }, as_dict=1)

def get_dynamic_date_range():

    try:
        result = frappe.db.sql("""
            SELECT MIN(posting_date) as min_date, MAX(posting_date) as max_date
            FROM `tabGL Entry`
            WHERE is_cancelled = 0
        """, as_dict=1)

        if result and result[0].min_date and result[0].max_date:
            return result[0].min_date, result[0].max_date
        else:
            return "2020-01-01", "2999-12-31"
    except Exception as e:
        frappe.log_error(f"Error in get_dynamic_date_range: {str(e)}")
        return "2020-01-01", "2999-12-31"

def get_english_date_range_from_nepali_month(nepali_month_name):
    if not nepali_month_name or not isinstance(nepali_month_name, str):
        return ("1900-01-01", "2999-12-31")
    nepali_months = [
        "Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
        "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
    ]
    try:
        today = datetime.today()
        today_nepali = nepali_date.from_datetime_date(today.date())
        nepali_year = today_nepali.year
    except Exception as e:
        frappe.log_error(f"Error getting today's Nepali date: {str(e)}")
        return ("1900-01-01", "2999-12-31")
    
    if nepali_month_name not in nepali_months:
        return ("1900-01-01", "2999-12-31")

    try:
        month_index = nepali_months.index(nepali_month_name) + 1
        nepali_start_date = nepali_date(nepali_year, month_index, 1)

        if month_index == 12:
            next_month_index = 1
            next_year = nepali_year + 1
        else:
            next_month_index = month_index + 1
            next_year = nepali_year

        nepali_next_month_start = nepali_date(next_year, next_month_index, 1)
        eng_start_date = nepali_start_date.to_datetime_date()
        eng_end_date = nepali_next_month_start.to_datetime_date() - timedelta(days=1)
    
    except Exception as e:
        frappe.log_error(f"Error converting Nepali month to English date range: {str(e)}")
        return ("1900-01-01", "2999-12-31")

    return (eng_start_date.strftime("%Y-%m-%d"), eng_end_date.strftime("%Y-%m-%d"))