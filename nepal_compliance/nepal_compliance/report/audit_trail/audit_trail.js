// Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.query_reports["Audit Trail"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "report",
            label: __("Report"),
            fieldtype: "Select",
            options: "Detail Report\nDocType Summary\nUser Summary",
            default: "Detail Report",
            reqd: 1,
        },
        {
            label: __("Select Day"),
            fieldtype: "Select",
            fieldname: "date_option",
            default: "This Week",
            options:
                "Today\nYesterday\nThis Week\nThis Month\nThis Quarter\nThis Year\nLast Week\nLast Month\nLast Quarter\nLast Year\nCustom\nNepali Date Filter",
            reqd: 1,
            on_change: function (report) {
                let selected_value = report.get_filter_value("date_option");
                let date_range = report.get_filter("date_range");
                let fields_to_toggle = ["from_nepali_date", "to_nepali_date"];
                fields_to_toggle.forEach(fieldname => {
                    let field = report.get_filter(fieldname);
                    field.df.hidden = selected_value !== "Nepali Date Filter";
                    if (field.df.hidden) field.set_value("");
                    field.refresh();
                });

                date_range.df.hidden = selected_value !== "Custom";
                if (date_range.df.hidden) date_range.set_value("");
                date_range.refresh();

                const report_field = report.get_filter("report");
                report_field.df.options =
                    selected_value === "Nepali Date Filter"
                        ? "Detail Report"
                        : "Detail Report\nDocType Summary\nUser Summary";
                report_field.refresh();

                report.refresh();
            },
        },
        {
            fieldname: "date_range",
            label: __("Select Dates"),
            fieldtype: "DateRange",
            hidden: true,
        },
        {
            fieldname: "from_nepali_date",
            label: __("From Date"),
            fieldtype: "Data",
            hidden: true
        },
        {
            fieldname: "to_nepali_date",
            label: __("To Date"),
            fieldtype: "Data",
            hidden: true
        },
        {
            fieldname: "user",
            label: __("User"),
            fieldtype: "Link",
            default: "",
            options: "User",
        },
        {
            fieldname: "doctype",
            label: __("DocType"),
            fieldtype: "Autocomplete",
            default: "",
            get_query: function () {
                return {
                    query: "nepal_compliance.nepal_compliance.report.audit_trail.audit_trail.get_relevant_doctypes",
                };
            },
        },
    ],
    onload: function(report) {
        if (typeof DatePickerConfig !== "undefined") {
            DatePickerConfig.initializePickers(report);
        }
    },
};
