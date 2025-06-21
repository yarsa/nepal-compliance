// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

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
            "fieldname": "from_nepali_date",
            "label": __("From Date"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "to_nepali_date",
            "label": __("To Date"),
            "fieldtype": "Data",
            "reqd": 0
        },
        {
            "fieldname": "customer_name",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "cancelled_by",
            "label": __("Cancelled By"),
            "fieldtype": "Link",
            "options": "User"
        }
    ],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};