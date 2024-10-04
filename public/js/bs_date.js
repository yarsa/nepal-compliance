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
})

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
