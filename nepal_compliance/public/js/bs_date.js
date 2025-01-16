frappe.ui.form.on('Fiscal Year',{
    refresh(frm){
        bs_datepicker(frm, "nepali_year_start_date", "year_start_date")
        bs_datepicker(frm, "nepali_year_end_date", "year_end_date")
    },
    year_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_start_date",NepaliFunctions.AD2BS(frm.doc.year_start_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    year_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_end_date",NepaliFunctions.AD2BS(frm.doc.year_end_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    }
});

frappe.ui.form.on('Salary Slip', {
    refresh(frm){
        bs_datepicker(frm, "nepali_start_date", "start_date");
        bs_datepicker(frm, "nepali_end_date", "end_date")
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

frappe.ui.form.on('Attendance',{
    refresh(frm){
        bs_datepicker(frm, "nepali_date", "attendance_date")
    },
    attendance_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date",NepaliFunctions.AD2BS(frm.doc.attendance_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    }
});

frappe.ui.form.on('Leave Allocation', {
    refresh(frm){
        bs_datepicker(frm, "from_nepali_date_leave_allocation", "from_date")
        bs_datepicker(frm, "to_nepali_date_leave_allocation", "to_date")
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date_leave_allocation",NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date_leave_allocation",NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Leave Applicattion',{
    refresh(frm){
        bs_datepicker(frm, "from_nepali_date_leave_application", "from_date")
        bs_datepicker(frm, "to_nepali_date_leave_application", "to_date")
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
    refresh(frm){
        bs_datepicker(frm, "nepali_from_date", "from_date")
        bs_datepicker(frm, "nepali_to_date", "to_date")
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



