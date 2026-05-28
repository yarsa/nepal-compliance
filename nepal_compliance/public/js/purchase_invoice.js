frappe.require([
    "/assets/nepal_compliance/js/utils.js",
    "/assets/nepal_compliance/js/validate.js",
    "/assets/nepal_compliance/js/email.js"
], function () {

    frappe.ui.form.on("Purchase Invoice", {
        refresh(frm) {
            if (typeof handle_send_email === "function") {
                handle_send_email(frm, "Purchase Invoice");
            }
        }
    });

});
