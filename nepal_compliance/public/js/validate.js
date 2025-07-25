function validate_field_value(frm, field_name) {
    var field_value = frm.doc[field_name];
    
    if (field_value) {
        var field_value_str = field_value.toString(); 
        if (field_value_str.length !== 9 || isNaN(field_value_str)) {
            frappe.throw(frappe._('The field {0} must be exactly 9 digits and should be a valid VAT/PAN Number.', [field_name]));
            frappe.validated = false; 
            return true;
        }
    }
    return false;
}

function validate_field(frm) {
    var vat_number = frm.doc.vat_number ? frm.doc.vat_number.toString().trim() : '';
    var customer_vat_number = frm.doc.customer_vat_number ? frm.doc.customer_vat_number.toString().trim() : '';
    var supplier_vat_number = frm.doc.supplier_vat_number ? frm.doc.supplier_vat_number.toString().trim() : '';

    if (vat_number && ((customer_vat_number && vat_number === customer_vat_number) || (supplier_vat_number && vat_number === supplier_vat_number))) {
        frappe.throw(__('Supplier VAT/PAN Number and Customer VAT/PAN Number should not be the same.'));
        frappe.validated = false; 
        return;
    }
    if (validate_field_value(frm, 'vat_number') || validate_field_value(frm, 'customer_vat_number') || validate_field_value(frm, 'supplier_vat_number')) {
        return; 
    }
}

function fetch_vat_number(frm, doc_type, field_name) {
    var doc_field = (doc_type === "Supplier" || doc_type === "Customer") ? doc_type.toLowerCase() : 'company';
    var field_map = doc_type === "Supplier" ? 'supplier_vat_number' :
                    doc_type === "Customer" ? 'customer_vat_number' :
                    'company_vat_number';

    if (frm.doc[doc_field]) {
        frappe.db.get_value(doc_type, frm.doc[doc_field], field_map, function(value) {
            if (value && value[field_map]) {
                frm.set_value(field_name, value[field_map]);
            } else {
                frm.set_value(field_name, '');
            }
        });
    } else {
        frm.set_value(field_name, '');
    }
}

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
        fetch_vat_number(frm, 'Company', 'supplier_vat_number');
    }
});

frappe.ui.form.on("Purchase Invoice", {
    validate: function(frm) {
        validate_field(frm);
    },
    supplier: function(frm) {
        fetch_vat_number(frm, 'Supplier', 'vat_number');
    },
    company: function (frm) {
        fetch_vat_number(frm, 'Company', 'customer_vat_number')
    },
    onload: function(frm){
        fetch_vat_number(frm, 'Company', 'customer_vat_number');
    }
});

frappe.ui.form.on("Company", {
    validate: function(frm) {
        validate_field_value(frm, 'company_vat_number');
    }
});

frappe.ui.form.on("Supplier", {
    validate: function(frm) {
        validate_field_value(frm, 'supplier_vat_number');
    }
});

frappe.ui.form.on("Customer", {
    validate: function(frm) {
        validate_field_value(frm, 'customer_vat_number');
    }
});