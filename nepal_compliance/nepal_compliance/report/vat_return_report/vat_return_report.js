// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Vat Return Report"] = {
	"filters": [
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
			"default": "All",
            on_change: function (report) {
				const party_type = frappe.query_report.get_filter_value("party_type");
				const customer_filter = frappe.query_report.get_filter("customer");
				const supplier_filter = frappe.query_report.get_filter("supplier");

				customer_filter.toggle(false);
				supplier_filter.toggle(false);

				if (party_type === "Customer") {
					customer_filter.toggle(true);
					frappe.query_report.set_filter_value("supplier", "");
				} else if (party_type === "Supplier") {
					supplier_filter.toggle(true);
					frappe.query_report.set_filter_value("customer", "");
				} else {
					frappe.query_report.set_filter_value("customer", "");
					frappe.query_report.set_filter_value("supplier", "");
				}
				frappe.query_report.refresh();
            }
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		}
	],
	onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};
