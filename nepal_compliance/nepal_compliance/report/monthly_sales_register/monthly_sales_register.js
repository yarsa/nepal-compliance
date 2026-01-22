// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Monthly Sales Register"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			get_query: function () {
				const company = frappe.query_report.get_filter_value("company");
				return {
					filters: {
						company: company
					}
				};
			}
		},
		{
			fieldname: "nepali_month",
			label: __("Nepali Month"),
			fieldtype: "Select",
			options: [
				"",
				"Baishakh", "Jestha", "Ashadh", "Shrawan",
				"Bhadra", "Ashwin", "Kartik", "Mangsir",
				"Poush", "Magh", "Falgun", "Chaitra"
			]
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer"
		}
	]
};
