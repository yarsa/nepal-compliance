// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Vat Register"] = {
    "filters": [
        {
            fieldname: 'company',
            label: __('Company'),
            fieldtype: 'Link',
            options: 'Company',
            default: frappe.defaults.get_user_default('company')
        },
        {
            fieldname: 'nepali_date',
            label: __('Nepali Date'),
            fieldtype: 'Data'
        },
		{
			fieldname: 'from_date',
			label: __('From Date'),
			fieldtype: 'Date'
		},
		{
			fieldname: 'to_date',
			label: __('To Date'),
			fieldtype: 'Date'
		},
		{
			fieldname: 'from_nepali_date',
			label: __('From Nepali Date'),
			fieldtype: 'Data'
		},
		{
			fieldname: 'to_nepali_date',
			label: __('To Nepali Date'),
			fieldtype: 'Data'
		},
        {
            fieldname: 'supplier',
            label: __('Supplier'),
            fieldtype: 'Link',
            options: 'Supplier'
        },
        {
            fieldname: 'bill_no',
            label: __('Supplier Invoice No'),
            fieldtype: 'Data',
            reqd: 0
        },
        {
            fieldname: 'bill_date',
            label: __('Supplier Invoice Date'),
            fieldtype: 'Date'
        },
        {
            fieldname: 'due_date',
            label: __('Invoice Due Date'),
            fieldtype: 'Date'
        },
        {
            fieldtype: 'Break'
        },
        {
            fieldname: 'expense_account',
            label: __('Expense Account'),
            fieldtype: 'Link',
            options: 'Account'
        },
        {
            fieldname: 'warehouse',
            label: __('Warehouse'),
            fieldtype: 'Link',
            options: 'Warehouse'
        },
        {
            fieldname: 'document_number',
            label: __('Invoice Number'),
            fieldtype: 'Link',
            options: 'Purchase Invoice',
            get_query: function() {
                return{
                    filters: {
                        'status': ["Not In", ['Return','Debit Note Issued']],
                        'is_return': 0
                }
            }
        }
    },
    ],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};