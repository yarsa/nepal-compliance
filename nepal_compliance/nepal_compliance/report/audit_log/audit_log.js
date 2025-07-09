// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

const doctypesWithStatus = [
    "Sales Invoice", "Purchase Invoice", "Payment Entry", "Sales Order", "Purchase Order",
    "Delivery Note", "Purchase Receipt", "POS Invoice", "Asset", "Expense Claim"
];

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
                        name: ["in", [
                            "Sales Invoice", "Purchase Invoice", "Journal Entry", "Payment Entry",
                            "Sales Order", "Purchase Order", "Delivery Note", "Purchase Receipt",
                            "Stock Entry", "Stock Reconciliation", "POS Invoice", "Asset",
                            "Expense Claim"
                        ]]
                    }
                };
            },
            "on_change": function() {
                const ref_doctype = frappe.query_report.get_filter_value('ref_doctype');
                const hasStatus = doctypesWithStatus.includes(ref_doctype);

                const docStatusFilter = frappe.query_report.get_filter('doc_status');
                if (docStatusFilter) {
                    docStatusFilter.df.hidden = !hasStatus;
                    if (!hasStatus) {
                        docStatusFilter.set_input("");
                    }
                    docStatusFilter.refresh();
                }
                frappe.query_report.refresh();
            }
        },
        {
            "fieldname": "docname",
            "label": __("Document"),
            "fieldtype": "Dynamic Link",
            "options": "ref_doctype",
            "get_query": function() {
                let ref_doctype = frappe.query_report.get_filter_value('ref_doctype');
                if (!ref_doctype) return {};

                if (doctypesWithStatus.includes(ref_doctype)) {
                    return {
                        "doctype": ref_doctype,
                        filters: {
                            'status': ["Not In", ['Draft']],
                            }
                        };
                    }      
                    else {
                        return {
                            "doctype": ref_doctype,
                            filters: {}
                        };
                    }
                },
        },
        {
            "fieldname": "status",
            "label": __("Submit Status"),
            "fieldtype": "Select",
            "options": ["", "After Submit", "Yes", "No"],
            "default": ""
        },
        {
            "fieldname": "modified_by",
            "label": "Modified By",
            "fieldtype": "Link",
            "options": "User"
        },
		{
			"fieldname": "doc_status",
			"label": __("Doc Status"),
			"fieldtype": "Select",
			"options": ["", "Draft", "Submitted", "Return", "Debit Note Issued", "Credit Note Issued", "Paid", "Partly Paid", "Unpaid", "Overdue", "To Bill", "Cancelled", "Internal Transfer"],
			"default": ""
		},
        {
            "fieldname": "operation",
            "label": __("Operation Type"),
            "fieldtype": "Select",
            "options": ["", "Create", "Update", "Delete", "Submit", "Cancel"],
            "default": ""
        },
        {
            "fieldname": "from_nepali_date",
            "label": __("From Date"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "to_nepali_date",
            "label": __("To Date"),
            "fieldtype": "Data"
        }
	],
	onload: function(report){
		DatePickerConfig.initializePickers(report);
        const refDoctypeFilter = report.get_filter('ref_doctype');
        if (refDoctypeFilter && refDoctypeFilter.df.on_change) {
            refDoctypeFilter.df.on_change();
        }
	}
};
