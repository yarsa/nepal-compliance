frappe.call({
    method: "frappe.client.get_list",
    args: {
        doctype: "Fiscal Year",
        fields: ["name", "year_start_date", "year_end_date"]
    },
    callback: function(response) {
        if (response.message) {
            response.message.forEach(function(fy) {
                var year_start_date = fy.year_start_date.split(" ")[0];
                var year_end_date = fy.year_end_date.split(" ")[0];

                var nepali_year_start_date = NepaliFunctions.AD2BS(year_start_date, "YYYY-MM-DD", "YYYY-MM-DD");
                var nepali_year_end_date = NepaliFunctions.AD2BS(year_end_date, "YYYY-MM-DD", "YYYY-MM-DD");

                frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "Fiscal Year",
                        name: fy.name,
                        fieldname: {
                            "nepali_year_start_date": nepali_year_start_date,
                            "nepali_year_end_date": nepali_year_end_date
                        }
                    }
                });
            });
        }
    }
});

frappe.provide("nepal_compliance.public.js.update_fiscal_year_dates");

nepal_compliance.public.js.update_fiscal_year_dates.convert_to_nepali_date = function(date) {
    return NepaliFunctions.AD2BS(date, "YYYY-MM-DD", "YYYY-MM-DD");
};