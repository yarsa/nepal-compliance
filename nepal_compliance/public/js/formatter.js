frappe.form.formatters.Date = function(value, df, options, doc) {
    if (!value) return '';

    try {
        const bs_date = NepaliFunctions.AD2BS(value, "YYYY-MM-DD", "YYYY-MM-DD");
        return bs_date;
    } catch (e) {
        return frappe.datetime.str_to_user(value); 
    }
};
