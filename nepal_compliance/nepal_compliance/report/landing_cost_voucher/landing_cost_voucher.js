// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Landing Cost Voucher"] = {
	"filters": [
		{
			fieldname: 'company',
			label: __('Company'),
			fieldtype: 'Link',
			options: 'Company',
			default: frappe.defaults.get_user_default('company')
		},
		{ fieldname: 'supplier', label: __('Supplier'), fieldtype: 'Link', options: 'Supplier'},
		{
			fieldname: 'posting_date',
			label: __('Posting Date'),
			fieldtype: 'Date'
		},
		{
			fieldname: 'nepali_date',
			label: __('Nepali Date'),
			fieldtype: 'Data'
		},
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
            "reqd": 0,
        },
        {
            "fieldname": "to_nepali_date",
            "label": __("To Nepali Date"),
            "fieldtype": "Data",
            "reqd": 0
        },
		{
			fieldname: 'distribute_charges_based_on',
			label: __('Distribute Charge Based On'),
			fieldtype: 'Select',
			options: [
				'',
				'Qty',
				'Amount',
				'Distribute Manually'
			],
		},
		{
			fieldname: 'expense_account',
			label: __('Expense Account'),
			fieldtype: 'Link',
			options: 'Account',
			get_query: function() {
				return {
				  filters: {
					'root_type': 'Expense'  
				  }
				};
			  }
		},
		{
			fieldname: 'receipt_document_type',
			label: __('Receipt Document Type'),
			fieldtype: 'Select',
			options: [
				'',
				'Purchase Invoice',
				'Purchase Receipt'
			]
		},
		{
			fieldname: 'document_number',
			label: __('Receipt Document'),
			fieldtype: 'Link',
			options: 'Landed Cost Voucher'
		}
	],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};

