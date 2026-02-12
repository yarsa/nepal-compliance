frappe.require([
    "/assets/nepal_compliance/js/utils.js",
    "/assets/nepal_compliance/js/validate.js",
    "/assets/nepal_compliance/js/email.js"
], function () {

    frappe.ui.form.on("Sales Invoice", {
        refresh(frm) {
            if (typeof handle_send_email === "function") {
                handle_send_email(frm, "Sales Invoice");
            }
        }
    });

});

frappe.ui.form.on("Sales Invoice", {
    on_submit(frm) {
        frappe.call({
            method: "nepal_compliance.cbms_api.post_sales_invoice_or_return_to_cbms",
            args: {
                doc_name: frm.doc.name
            },
            callback: function(r) {
                if (!r.message) return;

                if (r.message.status === "configuration_error") {
                    frappe.msgprint({
                        title: "CBMS Configuration Required",
                        message: r.message.message,
                        indicator: "red",
                        primary_action: {
                            label: "Configure CBMS",
                            action() {
                                frappe.set_route("Form", "CBMS Settings");
                            }
                        }
                    });
                }

                if (r.message.status === "queued") {
                    frappe.show_alert({
                        message: r.message.message || __("Invoice queued for CBMS"),
                        indicator: "green"
                    });
                } else if (r.message.status !== "configuration_error") {
                    frappe.show_alert({
                        message: r.message.message || __("Unexpected response from CBMS"),
                        indicator: "orange"
                    });
                }
            },
            error: function(r) {
                console.error("CBMS submission error:", r);
                frappe.msgprint({
                    title: __("CBMS Error"),
                    message: __("Failed to submit invoice to CBMS. Please try again or contact support."),
                    indicator: "red"
                });
            }
        });
    }
});
