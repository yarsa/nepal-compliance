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

frappe.listview_settings['Leave Allocation'] = {
    onload(listview) {
        if (frappe.user.has_role("HR Manager") || frappe.user.has_role("HR User")) {
            listview.page.add_inner_button(__('Allocate Monthly Leave (BS)'), () => {
                frappe.call({
                    method: "nepal_compliance.custom_code.leave_allocation.bs_leave_allocation.get_bs_today",
                    callback: function(r) {
                        if (!r.exc) {
                            const bs_day = r.message.day;
                            const is_first_day = bs_day === 1;
                            if (frappe.user.has_role("HR Manager") && !is_first_day) {
                                frappe.confirm(
                                    `Today is BS ${r.message.year}-${r.message.month}-${r.message.day}. This is not the 1st day of the Nepali month. Are you sure you want to allocate leave?`,
                                    () => {
                                        allocateBSLeave(listview, true);
                                    },
                                    () => {
                                        frappe.msgprint("Leave allocation canceled.");
                                    }
                                );
                            } else if (is_first_day) {
                                allocateBSLeave(listview);
                            } else {
                                frappe.msgprint("You can only allocate leave on the 1st day of the Nepali month.");
                            }
                        }
                    }
                });
            });
        }

        function allocateBSLeave(listview, force = false) {
            frappe.call({
                method: "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.allocate_monthly_leave_bs",
            args: { force },
            callback: function(r) {
                if (!r.exc) {
                    frappe.msgprint(__('Monthly BS Leave Allocated Successfully'));
                    listview.refresh();
            }
        }
    });
}
    }
};
