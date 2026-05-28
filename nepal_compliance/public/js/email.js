window.handle_send_email = function (frm, doctype) {
    if (frm.doc.docstatus !== 1) return;

    frappe.call({
        method: "nepal_compliance.email_utils.check_email_setup",
        args: {
            doctype: doctype,
            docname: frm.doc.name
        },
        callback(r) {
            if (!r.message) return;

            frm.add_custom_button(__("Send Email"), function () {
                frappe.call({
                    method: "nepal_compliance.email_utils.send_invoice_email",
                    args: {
                        docname: frm.doc.name,
                        doctype: doctype
                    },
                    freeze: true,
                    freeze_message: __("Sending Email..."),
                    callback() {
                        frappe.msgprint(__("Email has been queued for sending."));
                    },
                    error() {
                        frappe.msgprint(__("Error occurred while sending the email."));
                    }
                });
            }).addClass("btn-primary");
        },
        error() {
            frappe.msgprint(__("Error occurred while checking email setup."));
        }
    });
};
