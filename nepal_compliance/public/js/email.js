function handle_send_email(frm, doctype) {
    if (frm.doc.docstatus === 1) {
      frappe.call({
        method: "nepal_compliance.email_utils.check_email_setup",
        args: { doctype: doctype, docname: frm.doc.name },
        callback: function (r) {
          if (r.message) {
            let email_button = frm
              .add_custom_button(__("Send Email"), function () {
                frappe.call({
                  method: "nepal_compliance.email_utils.send_invoice_email",
                  args: { docname: frm.doc.name, doctype: doctype },
                  freeze: true,
                  freeze_message: __("Sending Email..."),
                  callback: function (response) {
                    frappe.msgprint(__("Email has been queued for sending.")); 
                  },
                  error: function (error) {
                    frappe.msgprint(
                      __("Error occurred while sending the email.")
                    );
                  },
                });
              })
              .addClass("btn-primary");
          }
        },
        error: function (error) {
          frappe.msgprint(__("Error occurred while checking email setup."));
        },
      });
    }
  }
  
  frappe.ui.form.on("Sales Invoice", {
    refresh: function (frm) {
      handle_send_email(frm, "Sales Invoice");
    },
  });
  
  frappe.ui.form.on("Purchase Invoice", {
    refresh: function (frm) {
      handle_send_email(frm, "Purchase Invoice");
    },
  });
  