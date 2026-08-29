// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

{% include "nepal_compliance/public/js/ird_register.js" %}

frappe.query_reports["Sales Return Register IRD"] = {
    _ird_month_grid: nepal_compliance.IRD_MONTH_PICKER_VERSION,
    filters: nepal_compliance.ird_register_filters({
        party: {
            fieldname: "customer",
            label: __("ग्राहक"),
            options: "Customer",
        },
        document: {
            fieldname: "return_invoice",
            label: __("Returned Invoice"),
            options: "Sales Invoice",
            get_query: function () {
                return {
                    filters: {
                        status: "Return",
                        is_return: 1
                    }
                };
            },
        }
    }),
    formatter: nepal_compliance.ird_invoice_formatter,
    onload: function (report) {
        nepal_compliance.setup_ird_register(
            report,
            "nepal_compliance.nepal_compliance.report.sales_return_register_ird.download_ird_format.generate_ird_sales_register_excel"
        );
    }
};
