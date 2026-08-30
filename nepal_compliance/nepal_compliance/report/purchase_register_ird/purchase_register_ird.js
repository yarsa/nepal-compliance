// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

{% include "nepal_compliance/public/js/ird_register.js" %}

frappe.query_reports["Purchase Register IRD"] = {
    _ird_month_grid: nepal_compliance.IRD_MONTH_PICKER_VERSION,
    filters: nepal_compliance.ird_register_filters({
        party: {
            fieldname: "supplier",
            label: __("आपूर्तिकर्ता"),
            options: "Supplier",
        },
        document: {
            fieldname: "document_number",
            label: __("बीजक नं."),
            options: "Purchase Invoice",
            get_query: function () {
                return {
                    filters: {
                        status: ["Not In", ["Return", "Debit Note Issued"]],
                        is_return: 0
                    }
                };
            },
        }
    }),
    formatter: nepal_compliance.ird_invoice_formatter,
    onload: function (report) {
        nepal_compliance.setup_ird_register(
            report,
            "nepal_compliance.nepal_compliance.report.purchase_register_ird.download_ird_format.generate_ird_purchase_register_excel"
        );
    }
};
