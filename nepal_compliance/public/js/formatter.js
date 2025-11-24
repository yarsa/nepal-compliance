(function waitForBoot() {
    if (typeof frappe === "undefined" || !frappe.boot) {
        return setTimeout(waitForBoot, 200);
    }

    frappe.form.formatters.Date = function (value, df, options, doc) {
        if (!value) return '';

        try {
            const use_ad_date =
                (frappe.boot?.use_ad_date !== undefined)
                    ? frappe.boot.use_ad_date
                    : frappe.boot?.user?.use_ad_date ?? true;

            if (use_ad_date) {
                return frappe.datetime.str_to_user(value);
            } else {
                const bs_date = NepaliFunctions.AD2BS(value, "YYYY-MM-DD", "YYYY-MM-DD");
                return bs_date;
            }
        } catch (e) {
            console.error("Date format error:", e);
            return frappe.datetime.str_to_user(value);
        }
    };
})();
