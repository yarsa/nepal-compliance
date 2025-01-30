// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

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
		}
	],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};