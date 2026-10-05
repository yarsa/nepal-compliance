// Bill Summary: the VAT line carries the rate actually charged, e.g. "13% VAT", worked out
// from the saved VAT and Taxable Amount. Loaded for each form listed below, so guarded.
if (!window.nepal_compliance_bill_summary) {
    window.nepal_compliance_bill_summary = true;
    for (const doctype of ["Sales Invoice", "Purchase Invoice", "Sales Order"]) {
        frappe.ui.form.on(doctype, {
            refresh(frm) {
                nepal_compliance_set_vat_label(frm);
            },
        });
    }
    nepal_compliance_follow_totals();
}

function nepal_compliance_set_vat_label(frm) {
    if (!frm.fields_dict.vat_amount) {
        return;
    }
    const taxable = flt(frm.doc.taxable_amount);
    const rate = taxable ? (flt(frm.doc.vat_amount) / taxable) * 100 : 0;
    const shown = Math.abs(rate - Math.round(rate)) < 0.01 ? Math.round(rate) : rate.toFixed(2);
    frm.set_df_property("vat_amount", "label", rate ? __("{0}% VAT", [shown]) : __("VAT"));
}

// ERPNext recalculates the totals in the browser after every item, tax or discount change, but
// the summary figures are worked out on the server. Fetch them after each recalculation instead
// of waiting for a save. Wrapped once on the shared class that every transaction form uses.
function nepal_compliance_follow_totals() {
    const proto = window.erpnext && erpnext.taxes_and_totals && erpnext.taxes_and_totals.prototype;
    if (!proto || proto.nepal_compliance_follows_totals) {
        return;
    }
    const calculate = proto.calculate_taxes_and_totals;
    proto.calculate_taxes_and_totals = function (...args) {
        const result = calculate.apply(this, args);
        Promise.resolve(result).then(
            () => nepal_compliance_queue_bill_summary(this.frm),
            () => {}
        );
        return result;
    };
    proto.nepal_compliance_follows_totals = true;
}

function nepal_compliance_queue_bill_summary(frm) {
    const doctypes = ["Sales Invoice", "Purchase Invoice", "Sales Order"];
    if (!frm || !doctypes.includes(frm.doctype) || frm.doc.docstatus !== 0 || !frm.fields_dict.taxable_amount) {
        return;
    }
    // one request once the typing stops, not one per keystroke
    clearTimeout(frm.nepal_compliance_summary_timer);
    frm.nepal_compliance_summary_timer = setTimeout(() => nepal_compliance_fetch_bill_summary(frm), 300);
}

function nepal_compliance_fetch_bill_summary(frm) {
    const name = frm.doc.name;
    const request = (frm.nepal_compliance_summary_request || 0) + 1;
    frm.nepal_compliance_summary_request = request;
    frappe.call({
        method: "nepal_compliance.utils.get_bill_summary",
        args: { doc: frm.doc },
        callback(r) {
            // an older reply, or the form has moved on to another document
            if (!r.message || request !== frm.nepal_compliance_summary_request || frm.doc.name !== name) {
                return;
            }
            // read-only figures: set directly, as set_value would mark the form dirty and recalculate again
            for (const [fieldname, value] of Object.entries(r.message)) {
                if (frm.fields_dict[fieldname]) {
                    frm.doc[fieldname] = value;
                    frm.refresh_field(fieldname);
                }
            }
            nepal_compliance_set_vat_label(frm);
        },
    });
}
