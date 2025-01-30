// Copyright (c) 2024, njsubedi, Mukesh and contributors
// For license information, please see license.txt

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
                let fields_to_toggle = ["from_date", "to_date", "from_nepali_date", "to_nepali_date"];
                fields_to_toggle.forEach(fieldname => {
                    let field = report.get_filter(fieldname);
                    if (selected_value === "Nepali Date Filter") {
                        field.df.hidden = false;
                    } 
                    else {
                        field.df.hidden = true;
                        field.set_value('')
                    }
                    field.refresh();
                });
                if (selected_value === "Custom") {
                    date_range.df.hidden = false;
                } else {
                    date_range.df.hidden = true;
                }
                date_range.refresh()
                let report_field = report.get_filter("report");
                if (selected_value === "Nepali Date Filter") {
                    report_field.df.options = "Detail Report";  
                } else {
                    report_field.df.options = "Detail Report\nDocType Summary\nUser Summary";  
                }
            
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
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            hidden: true
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            hidden: true
        },
        {
            fieldname: "from_nepali_date",
            label: __("From Nepali Date"),
            fieldtype: "Data",
            hidden: true
        },
        {
            fieldname: "to_nepali_date",
            label: __("To Nepali Date"),
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
                    query: "nepal_compliance.nepal_compliance.report.audit_trail.audit_trail.get_relavant_doctypes",
                };
            },
        },
    ],
    onload: function(report) {
        DatePickerConfig.initializePickers(report);
    },
};
$(document).ready(function() {
    setTimeout(() => {
        if (cur_list && cur_list.doctype) {
            if (cur_list.filter_area) {
                cur_list.filter_area.clear();
            }
            DatePickerConfig.initializePickers(cur_list);
        }
    }, 1000);
});

