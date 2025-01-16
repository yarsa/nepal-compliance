function bs_datepicker(frmField, bs_field , ad_field) {   
    if (typeof $.fn.nepaliDatePicker !== 'undefined') {
        console.log("Nepali Date Field:", bs_field);
        $(frmField.fields_dict[bs_field].input).nepaliDatePicker({
            ndpYear: true,
            ndpMonth: true,
            ndpYearCount: 10,
            onChange: function(e) {
                var date_format_converted = new Date(e.ad);
                if (frmField.fields_dict[ad_field] && frmField.fields_dict[ad_field].df.fieldtype == "Datetime") {
                    var time = "00:00:00";
                    date_format_converted = date_format_converted.toISOString().split("T")[0] + " " + time;
                } 
                frappe.model.set_value(frmField.doctype, frmField.docname, bs_field, e.bs);
                frappe.model.set_value(frmField.doctype, frmField.docname, ad_field, date_format_converted);
            }
        }); 
        $(frmField.fields_dict[bs_field].input);

        $(frmField.fields_dict[bs_field].input).on("change", function() {
            var nepali_date = $(this).val();
            frappe.model.set_value(frmField.doctype, frmField.docname, bs_field, nepali_date);
        
            if (/^[0-9-]+$/.test(nepali_date)) {
                var date = nepali_date.split("-");
                var year = date[0];
                var month = date[1];
                var day = date[2];
                if (year.length == 4 && month.length == 2 && day.length == 2) {
                    frappe.model.set_value(frmField.doctype, frmField.docname, bs_field, nepali_date);
                } else {
                    frappe.model.set_value(frmField.doctype, frmField.docname, bs_field, "");
                    $(frmField.fields_dict[bs_field].input).focus();
                }
             } else {
                frappe.model.set_value(frmField.doctype, frmField.docname, bs_field, "");
                $(frmField.fields_dict[bs_field].input).focus();
            }
            
        });        

    }
}