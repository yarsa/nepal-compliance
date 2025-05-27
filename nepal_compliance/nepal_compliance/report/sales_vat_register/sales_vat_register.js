// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Sales Vat Register"] = {
	"filters": [
		{
			fieldname: 'company',
			label: __('Company'),
			fieldtype: 'Link',
			options: 'Company',
			default: frappe.defaults.get_user_default('company')
		},
		{
			fieldname: 'from_nepali_date',
			label: __('From Date'),
			fieldtype: 'Data'
		},
		{
			fieldname: 'to_nepali_date',
			label: __('To Date'),
			fieldtype: 'Data'
		},
		{
			fieldname: 'customer',
			label: __('Customer'),
			fieldtype: 'Link',
			options: 'Customer'
		},
		{
			fieldname: 'customer_group',
			label: __('Customer Group'),
			fieldtype: 'Link',
			options: 'Customer Group'
		},
		{
			fieldname: 'owner',
			label: __('Owner'),
			fieldtype: 'Link',
			options: 'User'
		},
		{
			fieldname: 'cost_center',
			label: __('Cost Center'),
			fieldtype: 'Link',
			options: 'Cost Center'
		},
		{
			fieldname: 'project',
			label: __('Project'),
			fieldtype: 'Link',
			options: 'Project'
		},
		{
			fieldname: 'document_number',
			label: __('Invoice Number'),
			fieldtype: 'Link',
			options: 'Sales Invoice',
			get_query: function() {
				return {
					filters: {
						'status': ["Not In", ['Return','Credit Note Issued']],
						'is_return': 0
					}
				}
			}
		}
	],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};
