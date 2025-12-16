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
        // Format as YYYY-MM-DD
        const adString = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;

        let bs;
        try {
          bs = NepaliFunctions.AD2BS(adString);
        } catch (err) {
          console.error(err);
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
            // Split BS string to get day, month, year (const [bsYear, bsMonth, bsDay] = bs.split('-').map(Number);)
            if (typeof bs !== 'string') {
              console.error('AD2BS returned non-string value:', bs);
              frappe.msgprint(__('Invalid BS date format returned'));
              return;
            }
            const parts = bs.split('-').map(Number);
            if (parts.length !== 3 || parts.some(isNaN)) {
              console.error('Invalid BS date format:', bs);
              frappe.msgprint(__('Invalid BS date format returned'));
              return;
            }
            const [bsYear, bsMonth, bsDay] = parts;

            const is_first = bsDay === 1;

            const proceed = () => {
              frappe.call({
                method: "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.allocate_monthly_leave_bs",
                args: {
                  bs_year: bsYear,
                  bs_month: bsMonth,
                  leave_types: selected,
                  force: !is_first
                },
                callback: r => {
                  if (!r.exc) {
                    frappe.msgprint(__('Leave Allocation Done'));
                    listview.refresh();
                  }
                }
              });
            };

            if (!is_first && frappe.user.has_role("HR Manager")) {
              frappe.confirm(
                `Today is BS ${bsYear}-${bsMonth}-${bsDay}, not the 1st. Do you still want to allocate leave?`,
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
