frappe.ui.form.on('Fiscal Year',{
    refresh(frm){
        bs_datepicker(frm, "nepali_year_start_date", "year_start_date")
        bs_datepicker(frm, "nepali_year_end_date", "year_end_date")
    },
    year_start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_start_date", NepaliFunctions.AD2BS(frm.doc.year_start_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    year_end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_year_end_date", NepaliFunctions.AD2BS(frm.doc.year_end_date.split(" ") [0], "YYYY-MM-DD", "YYYY-MM-DD"));       
    }
});

frappe.ui.form.on('Holiday List', {
    refresh(frm){
        add_nepali_date_picker(frm, "nepali_from_date", "from_date")
        add_nepali_date_picker(frm, "nepali_to_date", "to_date")
    },
    from_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_from_date", NepaliFunctions.AD2BS(frm.doc.from_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD")); 
    },
    to_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_to_date", NepaliFunctions.AD2BS(frm.doc.to_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    nepali_from_date: function (frm) {
		if (frm.doc.nepali_from_date && !frm.doc.nepali_to_date) {
			var a_year_from_start = frappe.datetime.add_months(frm.doc.nepali_from_date, 12);
			frm.set_value("nepali_to_date", frappe.datetime.add_days(a_year_from_start, -1));
		}
	},

});

frappe.ui.form.on('Salary Slip', {
    refresh(frm){
        bs_datepicker(frm, "nepali_start_date", "start_date");
        bs_datepicker(frm, "nepali_end_date", "end_date")
    },
    start_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date", NepaliFunctions.AD2BS(frm.doc.start_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
    end_date(frm){
        frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date", NepaliFunctions.AD2BS(frm.doc.end_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
    },
});

