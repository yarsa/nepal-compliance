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
        },
        on_submit(frm) {
            frappe.call({
                method: "nepal_compliance.cbms_api.post_sales_invoice_status",
                args: {
                    doc_name: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Checking CBMS configuration..."),
                callback: function(r) {
                    if (!r.message) return;

                    if (r.message.status === "configuration_error") {
                        frappe.msgprint({
                            title: __("CBMS Configuration Required"),
                            message: r.message.message || __("CBMS is not properly configured. Please check your settings."),
                            indicator: "red",
                            primary_action: {
                                label: __("Configure CBMS"),
                                action() {
                                    frappe.set_route("Form", "CBMS Settings");
                                }
                            }
                        });
                    }
                    else if (r.message.status === "queued") {
                        frappe.show_alert({
                            message: r.message.message || __("Invoice queued for CBMS"),
                            indicator: "green"
                        });
                    }
                    else if (r.message.status === "disabled" || r.message.status === "not_found") {
                        // Silent skip (intended behavior)
                    }
                    else if (r.message.status === "error") {
                        frappe.msgprint({
                            title: __("CBMS Error"),
                            message: r.message.message || __("An error occurred while submitting to CBMS."),
                            indicator: "red"
                        });
                    }
                    else {
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
});