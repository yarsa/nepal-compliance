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
