frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        frm.set_df_property('cbms_status', 'read_only', 1);
        frm.set_df_property('cbms_response', 'read_only', 1);
        frm.set_df_property('vat_number', 'read_only', 1);
        frm.set_df_property('supplier_vat_number', 'read_only', 1);
        if (!frm.doc.customer) {
            frm.set_df_property('customs_declaration_number', 'hidden', 1);
            frm.set_df_property('customs_declaration_date', 'hidden', 1);
        }
    },
    customer: function(frm) {
        if (!frm.doc.customer) {
            frm.set_df_property('customs_declaration_number', 'hidden', 1);
            frm.set_df_property('customs_declaration_date', 'hidden', 1);
            return;
        }
        frappe.db.get_doc('Customer', frm.doc.customer).then(customer => {
            if (customer.territory && customer.territory !== 'Nepal') {
                frm.set_df_property('customs_declaration_number', 'hidden', 0);
                frm.set_df_property('customs_declaration_date', 'hidden', 0);
            } else {
                frm.set_df_property('customs_declaration_number', 'hidden', 1);
                frm.set_df_property('customs_declaration_date', 'hidden', 1);
            }
        });
    }
});


frappe.ui.form.on('Purchase Invoice',{
    refresh: function(frm) {
        frm.set_df_property('vat_number', 'read_only', 1);
        frm.set_df_property('customer_vat_number', 'read_only', 1);
        if (!frm.doc.supplier) {
            frm.set_df_property('customs_declaration_number', 'hidden', 1);
        }
    },
    supplier: function(frm) {
        if (!frm.doc.supplier) {
            frm.set_df_property('customs_declaration_number', 'hidden', 1);
            return;
        }
        frappe.db.get_doc('Supplier', frm.doc.supplier).then(supplier => {
            if (supplier.country && supplier.country !== 'Nepal') {
                frm.set_df_property('customs_declaration_number', 'hidden', 0);
            } else {
                frm.set_df_property('customs_declaration_number', 'hidden', 1);
            }
        });
    }
})

frappe.ui.form.on('Journal Entry', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.posting_date && !frm.doc.nepali_date) {
            const nepali = convertADtoBS(frm.doc.posting_date);
            frappe.db.set_value('Journal Entry', frm.doc.name, 'nepali_date', nepali)
                .then(() => frm.reload_doc());
        }
    }
});
