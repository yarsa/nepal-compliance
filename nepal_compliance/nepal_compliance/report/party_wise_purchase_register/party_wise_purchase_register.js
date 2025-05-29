// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Party Wise Purchase Register"] = {
    "filters": [
		{
            "fieldname": "from_nepali_date",
            "label": __("From Date"),
            "fieldtype": "Data",
		},
		{
			"fieldname": "to_nepali_date",
            "label": __("To Date"),
            "fieldtype": "Data",
		},
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["", "Paid", "Unpaid", "Overdue", "Partly Paid", "Return", "Debit Note Issued", "Submitted", "Cancelled", "Internal Transfer"],
            "default": "Open"
        },
        {
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        },
        {
            "fieldname": "invoice_number",
            "label": __("Invoice Number"),
            "fieldtype": "Link",
            "options": "Purchase Invoice",
            get_query: function() {
                let supplier = frappe.query_report.get_filter_value('supplier');
                if (supplier) {
                    return {
                        filters: {
                            'status': ["Not In", ['Draft']],
                            'supplier': supplier
                        }
                    };
                } else {
                    return {
                        filters: {
                            'status': ["Not In", ['Draft']]
                        }
                    };
                }
        }
    },
    ],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};
