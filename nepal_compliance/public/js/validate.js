window.validate_field_value = function (frm, field_name) {
    const value = frm.doc[field_name];
    if (!value) return false;

    const str = value.toString();
    if (str.length !== 9 || isNaN(str)) {
        frappe.throw(
            __('The field {0} must be exactly 9 digits and should be a valid VAT/PAN Number.', [field_name])
        );
    }
    return false;
};

window.validate_field = function (frm) {
    const vat = (frm.doc.vat_number || "").toString().trim();
    const customer = (frm.doc.customer_vat_number || "").toString().trim();
    const supplier = (frm.doc.supplier_vat_number || "").toString().trim();

    if (vat && ((customer && vat === customer) || (supplier && vat === supplier))) {
        frappe.throw(__('Supplier VAT/PAN Number and Customer VAT/PAN Number should not be the same.'));
        return;
    }

    window.validate_field_value(frm, 'vat_number');
    window.validate_field_value(frm, 'customer_vat_number');
    window.validate_field_value(frm, 'supplier_vat_number');
};

window.fetch_vat_number = function (frm, doctype, target_field) {
    const doc_field =
        (doctype === "Supplier" || doctype === "Customer") ? doctype.toLowerCase() : "company";

    const field_map =
        doctype === "Supplier" ? "supplier_vat_number" :
        doctype === "Customer" ? "customer_vat_number" :
        "company_vat_number";

    if (!frm.doc[doc_field]) {
        frm.set_value(target_field, "");
        return;
    }

    frappe.db.get_value(doctype, frm.doc[doc_field], field_map, r => {
        frm.set_value(target_field, r ? r[field_map] || "" : "");
    });
};

window.expand_section_and_focus = function (frm, fieldname) {
    const field = frm.fields_dict[fieldname];
    if (!field) return;

    const section = field.layout_section;
    if (section?.df?.collapsible && section.wrapper?.hasClass("collapsed")) {
        section.wrapper.find(".section-head").trigger("click");
    }

    setTimeout(() => {
        frm.scroll_to_field(fieldname);
        field.$input?.focus();
    }, 300);
};

frappe.ui.form.on("Sales Invoice", {
    validate: function(frm) {
        validate_field(frm);
    },
    customer: function(frm) {
        fetch_vat_number(frm, 'Customer', 'vat_number');
    },
    company: function(frm) {
        fetch_vat_number(frm, 'Company', 'supplier_vat_number')
    },
    onload: function(frm){
        if (frm.is_new()) {
            fetch_vat_number(frm, 'Company', 'supplier_vat_number');
        }
    }
});

frappe.ui.form.on("Sales Invoice", {
    validate: frm => validate_field(frm),
    customer: frm => fetch_vat_number(frm, "Customer", "vat_number"),
    company: frm => fetch_vat_number(frm, "Company", "supplier_vat_number"),
    onload: frm => frm.is_new() && fetch_vat_number(frm, "Company", "supplier_vat_number")
});

frappe.ui.form.on("Purchase Invoice", {
    validate: frm => validate_field(frm),
    supplier: frm => fetch_vat_number(frm, "Supplier", "vat_number"),
    company: frm => fetch_vat_number(frm, "Company", "customer_vat_number"),
    onload: frm => frm.is_new() && fetch_vat_number(frm, "Company", "customer_vat_number"),
    before_submit(frm) {
        if (frappe.flags.in_import || frappe.flags.in_install || frappe.flags.in_migrate) return;

        if (!frm.doc.bill_no?.toString().trim()) {
            frappe.msgprint({
                title: __('Missing Bill Number'),
                indicator: 'red',
                message: __('Please fill in the <b>Bill No</b> before submitting.')
            });
            expand_section_and_focus(frm, 'bill_no');
            frappe.validated = false;
        }
    }
});

frappe.ui.form.on("Company", {
    validate: frm => validate_field_value(frm, 'company_vat_number')
});
frappe.ui.form.on("Supplier", {
    validate: frm => validate_field_value(frm, 'supplier_vat_number')
});
frappe.ui.form.on("Customer", {
    validate: frm => validate_field_value(frm, 'customer_vat_number')
});
