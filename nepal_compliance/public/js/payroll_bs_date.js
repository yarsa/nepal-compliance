frappe.ui.form.on('Payroll Entry', {
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date",NepaliFunctions.AD2BS(frm.doc.start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date",NepaliFunctions.AD2BS(frm.doc.end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "end_date",NepaliFunctions.BS2AD(frm.doc.nepali_end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "start_date",NepaliFunctions.BS2AD(frm.doc.nepali_start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
});

frappe.ui.form.on('Income Tax Slab', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.effective_from) {
            frm.trigger('effective_from');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "effective_from", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    effective_from(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.effective_from.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Payroll Period', {
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date",NepaliFunctions.AD2BS(frm.doc.start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date",NepaliFunctions.AD2BS(frm.doc.end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "end_date",NepaliFunctions.BS2AD(frm.doc.nepali_end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "start_date",NepaliFunctions.BS2AD(frm.doc.nepali_start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
});

frappe.ui.form.on('Salary Structure Assignment', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.is_new()) return;

        if (frm.doc.from_date && !frm.doc.nepali_date) {
            const nepali = NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'nepali_date', nepali).then(() => {frm.reload_doc()});
        }
    },
    from_date(frm){
        if (frm.doc.docstatus === 0){
            const nepali = NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, 'nepali_date', nepali);
        }
    },
    nepali_date(frm){
        if (frm.doc.docstatus === 0){
            const ad = NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, 'form_date', ad);
        }
    }
});

frappe.ui.form.on('Salary Withholding', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.posting_date) {
            frm.trigger('posting_date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "posting_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    posting_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.posting_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Additional Salary', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "payroll_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    payroll_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.payroll_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Employee Incentive', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "payroll_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    payroll_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.payroll_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Retention Bonus', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "bonus_payment_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    bonus_payment_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.bonus_payment_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Employee Tax Exemption Proof Submission', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "payroll_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    payroll_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.payroll_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Employee Benefit Application', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "payroll_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    payroll_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.payroll_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Employee Benefit Claim', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "claim_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    claim_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.claim_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});



