// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

frappe.query_reports["Materialized Report"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 0,
        },
        {
            fieldname: "sync_with_ird",
            label: __("Synced with IRD"),
            fieldtype: "Select",
            options: ["","Yes", "No"],
            default: "",
            reqd: 0
        },
        {
            fieldname: "materialized_report",
            label: __("Materialized Report"),
            fieldtype: "Select",
            options: "Materialized View",
            default: "Materialized View",
            reqd: 0,
        },
        {
            fieldname: "doctype",
            label: __("DocType"),
            fieldtype: "Autocomplete",
            default: "",
            get_query: function () {
                return {
                    query: "nepal_compliance.nepal_compliance.report.materialized_report.materialized_report.get_purchase_sales_doctype",
                };
            },
        },
    ],
};
