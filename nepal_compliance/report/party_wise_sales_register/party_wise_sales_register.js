// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

frappe.query_reports["Party Wise Sales Register"] = {
	"filters": [
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.nowdate(), -30)
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.nowdate()
        },
        {
            "fieldname": "nepali_date",
            "label": __("Nepali Date"),
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
            "fieldname": "invoice_number",
            "label": __("Invoice Number"),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            get_query: function(){
            return {
                filters: {
                    'status': ["Not In", ['Draft']],
                }
            }
        }
    },
	]
}