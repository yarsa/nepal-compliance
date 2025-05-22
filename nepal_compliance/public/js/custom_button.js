frappe.listview_settings["Salary Component"] = {
    onload: function (listview) {
        const allowed_roles = ["System Manager", "HR Manager", "Accounts Manager"];
        const has_allowed_role = allowed_roles.some(role => frappe.user.has_role(role));

        if (has_allowed_role) {
            listview.page.add_inner_button(__('Generate Salary Structures'), function () {
                frappe.call({
                    method: 'nepal_compliance.custom_code.payroll.salary_structure.create_salary_structures',
                    callback: function (r) {
                        if (!r.exc) {
                            const messages = r.message || [];

                            const created = messages.filter(msg => msg.includes("created"));
                            const existing = messages.filter(msg => msg.includes("already exists"));

                            if (created.length > 0) {
                                frappe.msgprint({
                                    title: __("New Salary Structures Created"),
                                    message: created.join("<br>"),
                                    indicator: "green",
                                    wide: true
                                });
                            } else if (existing.length > 0) {
                                frappe.msgprint({
                                    title: __("No New Structures"),
                                    message: existing.join("<br>"),
                                    indicator: "orange",
                                    wide: true
                                });
                            } else {
                                frappe.msgprint(__("No salary structures processed."));
                            }
                        } else {
                            frappe.msgprint(__('Error generating salary structures. Check server logs.'));
                        }
                    }
                });
            });
        }
    }
};