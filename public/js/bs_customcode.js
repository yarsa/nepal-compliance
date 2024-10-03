function bs_datepicker(frmField, bs_field, ad_field){
    if(typeof $.fn.nepaliDatePicker !== "undefined"){
        console.log("BS Date Field:", bs_field);
        $(frmField.fields_dict[bs_field].input).nepaliDatePicker({
            ndpYear: true,
            ndpMonth: true,
            ndpYearCount: 10,
        });
        $(frmField.fields_dict[bs_field].input);

        $(frmField.fields_dict[bs_field].input).on("change", function(){
            var bs_date = $(this).val();
            frappe.module.set_value(frmField.doctype, frmField.docname, bs_field, bs_date);
            if(/^[0-9-]+$/.test(bs_date)){
                var date = bs_date.split("-");
                var y = date[0];
                var m = date[1];
                var d = date[2];
                if(y.length == 4 && m.length == 2 && d.length == 2){
                    frappe.module.set_value(frmField.doctype, frmField.docname, bs_field, bs_date)
                }
                else{
                    frappe.model.set_value(frmField.doctype, frmField.docname, nepali_date_field, "");
                    $(frmField.fields_dict[nepali_date_field].input).focus();
                }
            }
        })
    }
}