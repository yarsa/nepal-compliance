// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Purchase Return Vat Register"] = {
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
            fieldname: 'bill',
            label: __('Supplier Invoice No'),
            fieldtype: 'Data',
            reqd: 0
        },
        {
            fieldname: 'warehouse',
            label: __('Warehouse'),
            fieldtype: 'Link',
            options: 'Warehouse'
        },
        {
            fieldname: 'return_invoice',
            label: __('Returned Invoice'),
            fieldtype: 'Link',
            options: 'Purchase Invoice',
            get_query: function() {
                return {
                    filters: {
                        'status': 'Return',
                        'is_return': 1
                    }
                };
            }
        }        
    ],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};




