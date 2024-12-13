// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Cancellation Register"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
        {
            "fieldname": "from_nepali_date",
            "label": __("From Nepali Date"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "to_nepali_date",
            "label": __("To Nepali Date"),
            "fieldtype": "Data",
            "reqd": 0
        }
    ],
};