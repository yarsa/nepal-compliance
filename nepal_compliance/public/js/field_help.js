// Field help: a long description moves behind a "?" beside the field's label, shown on hover
// or tap, so it does not crowd the form. Loaded for each form listed below, so guarded.
if (!window.nepal_compliance_field_help) {
    window.nepal_compliance_field_help = true;
    const help_fields = {
        "Purchase Invoice": ["is_pan_or_abbreviated_bill"],
        "Purchase Order": ["is_pan_or_abbreviated_bill"],
    };
    for (const [doctype, fieldnames] of Object.entries(help_fields)) {
        frappe.ui.form.on(doctype, {
            refresh(frm) {
                for (const fieldname of fieldnames) {
                    nepal_compliance_description_as_help(frm, fieldname);
                }
            },
        });
    }
}

function nepal_compliance_description_as_help(frm, fieldname) {
    const field = frm.fields_dict[fieldname];
    if (!field || !field.$wrapper || !field.df.description) {
        return;
    }
    field.toggle_description(false);
    // the slot Frappe keeps beside the label for a documentation link
    const $help = field.$wrapper.find("span.help").first();
    if ($help.find(".nc-field-help").length) {
        return;
    }
    $(`<a class="nc-field-help" tabindex="0" role="button">${frappe.utils.icon("help", "sm")}</a>`)
        .attr("title", __(field.df.description, null, field.df.parent))
        .attr("aria-label", __("Help"))
        // a check field's label wraps its input, so a click here must not tick the box
        .on("click", (event) => event.preventDefault())
        .tooltip({ trigger: "hover focus", placement: "top" })
        .appendTo($help);
}
