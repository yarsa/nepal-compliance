$(document).on("app_ready", function () {
    if (!frappe.query_report || frappe.query_report._nepal_patched) return;

    frappe.query_report._nepal_patched = true;

    if (!frappe.query_report.get_filter_display) {
        console.warn("Nepal Compliance: get_filter_display not found, skipping patch");
        return;
    }

    const original = frappe.query_report.get_filter_display;

    frappe.query_report.get_filter_display = function (fieldname, value) {
        const df = frappe.query_report.get_filter_docfield(fieldname);

        if (
            Array.isArray(value) &&
            frappe.boot?.nepal_compliance_enabled &&
            df &&
            ["Date", "Datetime"].includes(df.fieldtype)
        ) {
            try {
                return value
                    .filter(v => v)
                    .map(v => frappe.datetime.str_to_user(v))
                    .join(" to ");
            } catch (e) {
                console.error("Nepal Compliance date conversion failed", e);
                return original.call(this, fieldname, value);
            }
        }

        if (
            frappe.boot?.nepal_compliance_enabled &&
            df &&
            ["Date", "Datetime"].includes(df.fieldtype) &&
            value
        ) {
            try {
                return frappe.datetime.str_to_user(value);
            } catch (e) {
                console.error("Nepal Compliance date conversion failed", e);
                return original.call(this, fieldname, value);
            }
        }

        return original.call(this, fieldname, value);
    };
});