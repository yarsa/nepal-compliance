frappe.require([
    "/assets/nepal_compliance/js/utils.js",
    "/assets/nepal_compliance/js/validate.js",
    "/assets/nepal_compliance/js/email.js"
], function () {

    frappe.ui.form.on("Purchase Invoice", {
        async refresh(frm) {
            if (typeof handle_send_email === "function") {
                handle_send_email(frm, "Purchase Invoice");
            }
            await mark_submit_mandatory_fields(frm);
        },
        async before_submit(frm) {
            if (frappe.flags.in_import || frappe.flags.in_install || frappe.flags.in_migrate) {
                return;
            }
            const requirements = await get_purchase_invoice_requirements();
            if (requirements.bill_date && !frm.doc.bill_date) {
                frappe.throw(__("Please fill in the <b>Supplier Invoice Date</b> before submitting."));
            }
        }
    });

});

// Visual-only "required" asterisk for fields enforced at submit time,
// so drafts remain saveable without them.
async function get_purchase_invoice_requirements() {
    const response = await frappe.call("nepal_compliance.utils.get_purchase_invoice_requirements");
    return response.message || {};
}

async function mark_submit_mandatory_fields(frm) {
    frm.get_field("bill_no")?.$wrapper.find(".control-label").addClass("reqd");
    const requirements = await get_purchase_invoice_requirements();
    frm.get_field("bill_date")
        ?.$wrapper.find(".control-label")
        .toggleClass("reqd", !!cint(requirements.bill_date));
    frm.get_field("attach_purchase_invoice")
        ?.$wrapper.find(".control-label")
        .toggleClass("reqd", !!cint(requirements.attachment));
}
