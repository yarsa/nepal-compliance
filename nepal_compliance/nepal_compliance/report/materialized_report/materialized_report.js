// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

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
            fieldname: "party_name",
            label: __("Party Name"),
            fieldtype: "Link",
            options: "Customer",
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
            default: "Sales Invoice",
            get_query: function () {
                return {
                    query: "nepal_compliance.nepal_compliance.report.materialized_report.materialized_report.get_purchase_sales_doctype",
                };
            },
            on_change: function (report) {
                const doctype = frappe.query_report.get_filter_value("doctype");
                let party_filter = frappe.query_report.get_filter("party_name");
                let ird_filter = frappe.query_report.get_filter("sync_with_ird");

                if (doctype === "Sales Invoice") {
                    party_filter.df.options = "Customer";
                    party_filter.df.label = __("Customer");
                    ird_filter.toggle(true);
                } else if (doctype === "Purchase Invoice") {
                    party_filter.df.options = "Supplier";
                    party_filter.df.label = __("Supplier");
                    ird_filter.toggle(false);
                } else {
                    party_filter.df.options = "";
                    party_filter.df.label = __("Party Name");
                    ird_filter.toggle(true);
                }

                party_filter.refresh();
                frappe.query_report.refresh();
            }
        },
    ],
};
