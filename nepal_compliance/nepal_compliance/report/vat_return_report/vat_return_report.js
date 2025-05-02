// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Vat Return Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "from_nepali_date",
			"label": __("From Nepali Date"),
			"fieldtype": "Data",
		},
		{
			"fieldname": "to_nepali_date",
			"label": __("To Nepali Date"),
			"fieldtype": "Data",
		},
		{
			"fieldname": "party_type",
			"label": __("Party Type"),
			"fieldtype": "Select",
			"options": "Customer\nSupplier\nAll",
			"default": "All"
		}
	],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};