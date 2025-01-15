frappe.ui.form.on('Fiscal Year',{
    refresh(frm){
        bs_datepicker(frm, "nepali_year_start_date", "year_start_date")
        bs_datepicker(frm, "nepali_year_end_date", "year_end_date")
    },
    year_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_start_date", BsFunctions.AD2BS(frm.doc.year_start_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    year_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_end_date", BsFunctions.AD2BS(frm.doc.year_end_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    }
});

frappe.ui.form.on('Salary Slip', {
    refresh(frm){
        bs_datepicker(frm, "nepali_start_date", "start_date");
        bs_datepicker(frm, "nepali_end_date", "end_date")
    },
    start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date", BsFunctions.AD2BS(frm.doc.start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date", BsFunctions.AD2BS(frm.doc.end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
});

frappe.ui.form.on('Attendance',{
    refresh(frm){
        bs_datepicker(frm, "nepali_date", "attendance_date")
    },
    attendance_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_date", BsFunctions.AD2BS(frm.doc.attendance_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    }
});

frappe.ui.form.on('Leave Allocation', {
    refresh(frm){
        bs_datepicker(frm, "from_nepali_date_leave_allocation", "from_date")
        bs_datepicker(frm, "to_nepali_date_leave_allocation", "to_date")
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date_leave_allocation", BsFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date_leave_allocation", BsFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    }
});

frappe.ui.form.on('Leave Applicattion',{
    refresh(frm){
        bs_datepicker(frm, "from_nepali_date_leave_application", "from_date")
        bs_datepicker(frm, "to_nepali_date_leave_application", "to_date")
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_nepali_date_leave_application", BsFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_nepali_date_leave_application", BsFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    from_nepali_date_leave_application(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "from_date", BsFunctions.BS2AD(frm.doc.from_nepali_date_leave_application.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_nepali_date_leave_application(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "to_date", BsFunctions.BS2AD(frm.doc.to_nepali_date_leave_application.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
})

frappe.ui.form.on('Holiday List', {
    refresh(frm){
        bs_datepicker(frm, "nepali_from_date", "from_date")
        bs_datepicker(frm, "nepali_to_date", "to_date")
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_from_date", BsFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_to_date", BsFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_from_date: function (frm) {
		if (frm.doc.nepali_from_date && !frm.doc.nepali_to_date) {
			var a_year_from_start = frappe.datetime.add_months(frm.doc.nepali_from_date, 12);
			frm.set_value("nepali_to_date", frappe.datetime.add_days(a_year_from_start, -1));
		}
	},

});

frappe.ui.frm.on("Holiday", "holiday_date", function(frm, cdt, cdn){
    frappe.model.set_value(cdt, cdn, "neplai_date", BsFunctions.AD2BS(locals[cdt][cdn].holiday_date, "YYYY-MM-DD", "YYYY-MM-DD")); 
})

frappe.ui.frm.on("Holiday", "nepali_date", function(frm, cdt, cdn){
    frappe.model.set_value(cdt, cdn, "holiday_date", BsFunctions.BS2AD(locals[cdt][cdn].nepali_date, "YYYY-MM-DD", "YYYY-MM-DD")); 
})



