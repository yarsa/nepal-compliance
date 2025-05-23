// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.ui.form.on('CBMS Settings', {
    refresh: function (frm) {
      frm.add_custom_button(__('Sync Failed Invoices'), function () {
          frappe.call({
            method: 'nepal_compliance.cbms_api.sync_failed_cbms_invoices',
            freeze: true,
            freeze_message: __('Syncing failed invoices...'),
            callback: function (r) {
              if (!r.exc) {
                frappe.msgprint(__("Sync job started in background."));
              } else {
                frappe.msgprint(__('An error occurred while syncing the failed invoices.'));
              }
            },
          });
        }),
        frm.add_custom_button(__('Taxpayer Portal'), function () {
          var link = document.createElement('a');
          link.href = 'https://taxpayerportal.ird.gov.np/taxpayer/app.html';
          link.target = '_blank'; 
          link.click();
      });
      frm.fields_dict.user_name.$wrapper.find("input").attr("placeholder", "Use your CBMS username");
      frm.fields_dict.password.$wrapper.find("input").attr("placeholder", "Use your CBMS password");
      frm.fields_dict.panvat_no.$wrapper.find("input").attr("placeholder", "Use your CBMS VAT/PAN");
    },
  });