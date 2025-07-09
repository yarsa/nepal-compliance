frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
            frm.set_df_property('cbms_status', 'read_only', 1);
            frm.set_df_property('cbms_response', 'read_only', 1);
            frm.set_df_property('vat_number', 'read_only', 1);
            frm.set_df_property('supplier_vat_number', 'read_only', 1);
        }
});

frappe.ui.form.on('Purchase Invoice',{
    refresh: function(frm){
        frm.set_df_property('vat_number', 'read_only', 1);
        frm.set_df_property('customer_vat_number', 'read_only', 1);
    }
})

frappe.ui.form.on('Journal Entry', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.posting_date && !frm.doc.nepali_date) {
            try {
                const nepali = convertADtoBS(frm.doc.posting_date);
                frappe.db.set_value('Journal Entry', frm.doc.name, 'nepali_date', nepali)
                    .then(() => frm.reload_doc())
                    .catch(err => {
                        console.error('Failed to update nepali_date:', err);
                        frappe.msgprint(__('Failed to update Nepali date'));
                    });
            } catch (err) {
                console.error('Date conversion error:', err);
                frappe.msgprint(__('Invalid date format for Nepali conversion'));
            }
        }
    }
});
