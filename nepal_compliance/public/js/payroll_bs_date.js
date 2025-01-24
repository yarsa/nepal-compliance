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
        if (frm.doc.from_date) {
            frm.trigger('from_date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
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