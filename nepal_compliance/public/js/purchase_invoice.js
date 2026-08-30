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
            mark_submit_mandatory_fields(frm);
        }
    });

});

// Visual-only "required" asterisk for fields enforced at submit time,
// so drafts remain saveable without them.
function mark_submit_mandatory_fields(frm) {
    ["bill_no", "bill_date"].forEach((fieldname) => {
        frm.get_field(fieldname)?.$wrapper.find(".control-label").addClass("reqd");
    });
    frappe.call("nepal_compliance.utils.is_purchase_invoice_attachment_required").then((r) => {
        frm.get_field("attach_purchase_invoice")
            ?.$wrapper.find(".control-label")
            .toggleClass("reqd", !!cint(r.message));
    });
}
