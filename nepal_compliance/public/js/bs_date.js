frappe.ui.form.on('Fiscal Year',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    year_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_start_date",NepaliFunctions.AD2BS(frm.doc.year_start_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    year_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_end_date",NepaliFunctions.AD2BS(frm.doc.year_end_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    },
    nepali_year_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "year_start_date",NepaliFunctions.BS2AD(frm.doc.nepali_year_start_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    },
    nepali_year_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "year_end_date",NepaliFunctions.BS2AD(frm.doc.nepali_year_end_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    },
});

frappe.ui.form.on('Salary Slip', {
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
frappe.ui.form.on('Expense Claim', {
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

frappe.ui.form.on('Attendance',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    attendance_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date",NepaliFunctions.AD2BS(frm.doc.attendance_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "attendance_date",NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    }
});

frappe.ui.form.on('Leave Allocation', {
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date_leave_allocation",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date_leave_allocation",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_nepali_date_leave_allocation(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date",NepaliFunctions.BS2AD(frm.doc.from_nepali_date_leave_allocation.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_nepali_date_leave_allocation(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date",NepaliFunctions.BS2AD(frm.doc.to_nepali_date_leave_allocation.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Leave Application',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date_leave_application",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date_leave_application",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_nepali_date_leave_application(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date",NepaliFunctions.BS2AD(frm.doc.from_nepali_date_leave_application.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_nepali_date_leave_application(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date",NepaliFunctions.BS2AD(frm.doc.to_nepali_date_leave_application.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
})

frappe.ui.form.on('Holiday List', {
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_from_date",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_to_date",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date", NepaliFunctions.BS2AD(frm.doc.nepali_from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    nepali_to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date", NepaliFunctions.BS2AD(frm.doc.nepali_to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
});

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.transaction_date) {
            frm.trigger('transaction_date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "transaction_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    transaction_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.transaction_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
})

frappe.ui.form.on('Purchase Invoice', {
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

frappe.ui.form.on('Purchase Receipt', {
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

frappe.ui.form.on('Sales Order', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.transaction_date) {
            frm.trigger('transaction_date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "transaction_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    transaction_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.transaction_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
})

frappe.ui.form.on('Delivery Note', {
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

frappe.ui.form.on('Sales Invoice', {
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