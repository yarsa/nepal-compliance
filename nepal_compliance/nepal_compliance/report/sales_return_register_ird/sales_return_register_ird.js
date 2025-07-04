// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Sales Return Register IRD"] = {
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
			fieldtype: 'Data'
		},
		{
			fieldname: 'to_nepali_date',
			label: __('मिति सम्म'),
			fieldtype: 'Data'
		},
        {
            fieldname: 'customer',
            label: __('आपूर्तिकर्ता'),
            fieldtype: 'Link',
            options: 'Customer'
        },
        {
            fieldtype: 'Break'
        },
        {
            fieldname: 'return_invoice',
            label: __('Returned Invoice'),
            fieldtype: 'Link',
            options: 'Sales Invoice',
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
		report.page.add_inner_button(__('Download IRD Format'), function () {
    const filters = report.get_filter_values(true);
    frappe.call({
        method: "nepal_compliance.nepal_compliance.report.sales_return_register_ird.download_ird_format.generate_ird_sales_register_excel",
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
