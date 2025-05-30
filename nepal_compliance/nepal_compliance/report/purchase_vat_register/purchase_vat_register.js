// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

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
            fieldtype: 'Break'
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