// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Party Wise Sales Register"] = {
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
            "options": ["", "Paid", "Unpaid", "Overdue", "Partly Paid", "Return", "Credit Note Issued", "Unpaid and Discounted", "Partly Paid and Discounted", "Overdue and Discounted", "Submitted", "Cancelled", "Internal Transfer"],
            "default": "Open"
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "invoice_number",
            "label": __("Invoice Number"),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            get_query: function(){
                let customer = frappe.query_report.get_filter_value('customer');
                if (customer) {
                    return {
                        filters: {
                            'status': ["Not In", ['Draft']],
                            'customer': customer
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
