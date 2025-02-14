// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Audit Log"] = {
	"filters": [
        {
            "fieldname": "ref_doctype",
            "label": __("Document Type"),
            "fieldtype": "Link",
            "options": "DocType",
            "required": "1",
            "default": "Sales Invoice",
            "get_query": function() {
                return {
                    "filters": {
                        "name": ["in", ["Sales Invoice", "Purchase Invoice"]]
                    }
                };
            }
        },
        {
            "fieldname": "docname",
            "label": __("Document"),
            "fieldtype": "Dynamic Link",
            "options": "ref_doctype",
            "get_query": function() {
                let ref_doctype = frappe.query_report.get_filter_value('ref_doctype');
                if (ref_doctype) {
                    return {
                        "doctype": ref_doctype,
						filters: {
							'status': ["Not In", ['Draft']],
						}
                    };
                }
                return {};
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "required": "0"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "required": "0"
        },
        {
            "fieldname": "status",
            "label": __("Submit Status"),
            "fieldtype": "Select",
            "options": ["", "After Submit", "Yes", "No"],
            "default": ""
        },
		{
			"fieldname": "doc_status",
			"label": __("Doc Status"),
			"fieldtype": "Select",
			"options": ["", "Return", "Debit Note Issued", "Credit Note Issued", "Paid", "Partly Paid", "Unpaid", "Overdue", "Cancelled", "Internal Transfer"],
			"default": ""
		},
        {
            "fieldname": "from_nepali_date",
            "label": __("From Nepali Date"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "to_nepali_date",
            "label": __("To Nepali Date"),
            "fieldtype": "Data"
        }
	],
	onload: function(report){
		DatePickerConfig.initializePickers(report);
	}
};
