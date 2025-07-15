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
                const today = new Date();
                let bs;
                try {
                    bs = NepaliFunctions.AD2BS({
                        year: today.getFullYear(),
                        month: today.getMonth() + 1,
                        day: today.getDate()
                    });
                } catch (err) {
                    console.error('BS date conversion failed:', err);
                    frappe.msgprint(__('Failed to convert date to Bikram Sambat calendar'));
                    return;
                }
                const is_first_day = bs.day === 1;

                if (!is_first_day && frappe.user.has_role("HR Manager")) {
                    frappe.confirm(
                        `Today is BS ${bs.year}-${bs.month}-${bs.day}, not the 1st. Do you still want to allocate leave?`,
                        () => allocateBSLeave(listview, bs.year, bs.month, true),
                        () => frappe.msgprint("Cancelled.")
                    );
                } else if (is_first_day) {
                    allocateBSLeave(listview, bs.year, bs.month);
                } else {
                    frappe.msgprint(__("Only HR Managers can override BS 1st day restriction."));
                }
            });

            function allocateBSLeave(listview, bsYear, bsMonth, force = false) {
                frappe.call({
                    method: "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.allocate_monthly_leave_bs",
                    args: {
                        bs_year: bsYear,
                        bs_month: bsMonth,
                        force: force
                    },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(__('Monthly BS Leave Allocated Successfully'));
                            listview.refresh();
                        }
                    }
                });
            }
        }
    }
};

