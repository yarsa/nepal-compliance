frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
            frm.set_df_property('cbms_status', 'read_only', 1);
            frm.set_df_property('cbms_response', 'read_only', 1);
        }
});
