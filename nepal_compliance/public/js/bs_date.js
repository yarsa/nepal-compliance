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
        if (frm.doc.attendance_date) {
            frm.trigger('attendance_date');
        }
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
});

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
});

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
});

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

frappe.ui.form.on('Payment Entry', {
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

frappe.ui.form.on('Journal Entry', {
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

frappe.ui.form.on('Request for Quotation', {
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
});

frappe.ui.form.on('Supplier Quotation', {
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
});

frappe.ui.form.on('Quotation', {
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
});

frappe.ui.form.on('Blanket Order',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date",NepaliFunctions.BS2AD(frm.doc.from_nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date",NepaliFunctions.BS2AD(frm.doc.to_nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Landed Cost Voucher', {
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

frappe.ui.form.on('Asset', {
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

frappe.ui.form.on('Asset Repair', {
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
});

frappe.ui.form.on('Asset Movement', {
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
});

frappe.ui.form.on('Asset Value Adjustment', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.date) {
            frm.trigger('date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Asset Capitalization', {
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

frappe.ui.form.on('POS Opening Entry', {
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

frappe.ui.form.on('POS Closing Entry', {
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

frappe.ui.form.on('Loyalty Program',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date",NepaliFunctions.BS2AD(frm.doc.from_nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date",NepaliFunctions.BS2AD(frm.doc.to_nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Promotional Scheme',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
        if (frm.doc.valid_from) {
            frm.trigger('valid_from');
        }
    },
    valid_from(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from_bs",NepaliFunctions.AD2BS(frm.doc.valid_from.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_upto(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_to_bs",NepaliFunctions.AD2BS(frm.doc.valid_upto.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_from_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from",NepaliFunctions.BS2AD(frm.doc.valid_from_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_to_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_upto",NepaliFunctions.BS2AD(frm.doc.valid_to_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Pricing Rule',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
        if (frm.doc.valid_from) {
            frm.trigger('valid_from');
        }
    },
    valid_from(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from_bs",NepaliFunctions.AD2BS(frm.doc.valid_from.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_upto(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_to_bs",NepaliFunctions.AD2BS(frm.doc.valid_upto.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_from_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from",NepaliFunctions.BS2AD(frm.doc.valid_from_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_to_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_upto",NepaliFunctions.BS2AD(frm.doc.valid_to_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Coupon Code',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    valid_from(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from_bs",NepaliFunctions.AD2BS(frm.doc.valid_from.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_upto(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_to_bs",NepaliFunctions.AD2BS(frm.doc.valid_upto.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_from_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_from",NepaliFunctions.BS2AD(frm.doc.valid_from_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    valid_to_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "valid_upto",NepaliFunctions.BS2AD(frm.doc.valid_to_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Serial No',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
    },
    warranty_expiry_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "warranty_expiry_date_bs",NepaliFunctions.AD2BS(frm.doc.warranty_expiry_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    amc_expiry_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "amc_expiry_date_bs",NepaliFunctions.AD2BS(frm.doc.amc_expiry_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    warranty_expiry_date_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "warranty_expiry_date",NepaliFunctions.BS2AD(frm.doc.warranty_expiry_date_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    amc_expiry_date_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "amc_expiry_date",NepaliFunctions.BS2AD(frm.doc.amc_expiry_date_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Batch',{
    refresh: function(frm) {
        DatePickerConfig.initializePickers(frm);
        if (frm.doc.manufacturing_date) {
            frm.trigger('manufacturing_date');
        }
    },
    manufacturing_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "manufacturing_date_bs",NepaliFunctions.AD2BS(frm.doc.manufacturing_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    expiry_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "expiry_date_bs",NepaliFunctions.AD2BS(frm.doc.expiry_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    manufacturing_date_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "manufacturing_date",NepaliFunctions.BS2AD(frm.doc.manufacturing_date_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    expiry_date_bs(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "expiry_date",NepaliFunctions.BS2AD(frm.doc.expiry_date_bs.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
});

frappe.ui.form.on('Installation Note', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.inst_date) {
            frm.trigger('inst_date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "inst_date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    inst_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.inst_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Stock Reconciliation', {
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

frappe.ui.form.on('Quality Inspection', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.report_date) {
            frm.trigger('report_date');
        }
    },
    report_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "report_date_bs_quality_inspection", NepaliFunctions.AD2BS(frm.doc.report_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    report_date_bs_quality_inspection(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "report_date", NepaliFunctions.BS2AD(frm.doc.report_date_bs_quality_inspection.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Quick Stock Balance', {
    refresh: function(frm){
        DatePickerConfig.initializePickers(frm)
        if (frm.doc.date) {
            frm.trigger('date');
        }
    },
    nepali_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "date", NepaliFunctions.BS2AD(frm.doc.nepali_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", NepaliFunctions.AD2BS(frm.doc.date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});