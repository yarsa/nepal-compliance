// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Purchase Register IRD"] = {
    "filters": [
        {
            fieldname: 'company',
            label: __('फर्म / कम्पनी'),
            fieldtype: 'Link',
            options: 'Company',
            default: frappe.defaults.get_user_default('company')
        },
		{
			fieldname: 'from_nepali_date',
			label: __('मिति देखि'),
			fieldtype: 'Date'
		},
		{
			fieldname: 'to_nepali_date',
			label: __('मिति सम्म'),
			fieldtype: 'Date'
		},
        {
            fieldname: 'supplier',
            label: __('आपूर्तिकर्ता'),
            fieldtype: 'Link',
            options: 'Supplier'
        },
        {
            fieldtype: 'Break'
        },
        {
            fieldname: 'document_number',
            label: __('बीजक नं.'),
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
		report.page.add_inner_button(__('Download IRD Format'), function () {
    const filters = report.get_filter_values(true);
    frappe.call({
        method: "nepal_compliance.nepal_compliance.report.purchase_register_ird.download_ird_format.generate_ird_purchase_register_excel",
        args: {
            filters: JSON.stringify(filters)
        },
        callback: function (r) {
            if (r.message) {
                window.open(r.message);
            } else {
                frappe.msgprint(__('No data found or export failed.'));
            }
        }
    });
});

    }
};
