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
    if (frappe.user.has_role("HR User") || frappe.user.has_role("HR Manager")) {
      listview.page.add_inner_button(__('Allocate Monthly Leave (BS)'), async () => {
        const today = new Date();
        let bs;
        try {
          bs = NepaliFunctions.AD2BS({
            year: today.getFullYear(),
            month: today.getMonth() + 1,
            day: today.getDate()
          });
        } catch {
          frappe.msgprint(__('Failed to convert to BS date'));
          return;
        }

        const res = await frappe.call({
          method: "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.get_bs_eligible_leave_types"
        });

        const leave_types = res.message || [];
        if (!leave_types.length) {
          frappe.msgprint(__("No eligible leave types found."));
          return;
        }

        const d = new frappe.ui.Dialog({
          title: __('Select Leave Type to Allocate'),
          fields: [
            {
              fieldname: 'select_all',
              label: __('Apply to All Leave Types'),
              fieldtype: 'Check'
            },
            {
              fieldname: 'leave_type',
              label: __('Leave Type'),
              fieldtype: 'MultiCheck',
              options: leave_types.map(lt => ({ label: lt.name, value: lt.name }))
            }
          ],
          primary_action: values => {
            let selected = [];
            if (values.select_all) {
              selected = leave_types.map(lt => lt.name);
            } else {
              selected = values.leave_type || [];
            }
            if (!selected.length) {
              frappe.msgprint(__("No leave type selected."));
              return;
            }

            const is_first = bs.day === 1;
            const proceed = () => {
              frappe.call({
                method: "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.allocate_monthly_leave_bs",
                args: {
                  bs_year: bs.year,
                  bs_month: bs.month,
                  leave_types: selected,
                  force: !is_first
                },
                callback: r => {
                  if (!r.exc) {
                    frappe.msgprint(__('✅ Leave Allocation Done'));
                    listview.refresh();
                  }
                }
              });
            };

            if (!is_first && frappe.user.has_role("HR Manager")) {
              frappe.confirm(
                `Today is BS ${bs.year}-${bs.month}-${bs.day}, not the 1st. Do you still want to allocate leave?`,
                proceed,
                () => frappe.msgprint(__("Cancelled."))
              );
            } else if (is_first) {
              proceed();
            } else {
              frappe.msgprint(__("Only HR Managers can allocate other than 1st of BS Month."));
            }
            d.hide();
          }
        });
        d.show();
      });
    }
  }
};
