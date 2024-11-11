// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Vat Register"] = {
    "filters": [
        {
            fieldname: 'company',
            label: __('Company'),
            fieldtype: 'Link',
            options: 'Company',
            default: frappe.default.get_user_default('company')
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
            fieldtype: 'Date',
        },
        {
            fieldname: 'due_date',
            label: __('Invoice Due Date'),
            fieldtype: 'Data'
        },
        {
            fieldname: 'is_vat_applicable',
            label: __('Is Vat Applicable'),
            fieldtype: 'Check'
        }
    ]
};