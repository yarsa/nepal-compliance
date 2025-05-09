frappe.after_ajax(() => {
    fetch_user_date_preference().then(use_ad_date => {
        window.use_ad_date = use_ad_date;
        override_with_nepali_date_picker(use_ad_date);
    });
});

function fetch_user_date_preference() {
    return new Promise((resolve) => {
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "User",
                filters: { name: frappe.session.user },
                fieldname: "use_ad_date"
            },
            callback: (r) => {
                resolve(r.message?.use_ad_date ?? true);
            }
        });
    });
}

function override_with_nepali_date_picker(use_ad_date) {
    if (use_ad_date) {
        extend_with_ad_date_picker();
    } else {
        extend_with_bs_date_picker();
    }
}

function extend_with_ad_date_picker() {
    const originalSetFormattedInput = frappe.ui.form.ControlDate.prototype.set_formatted_input;
    const originalRefresh = frappe.ui.form.ControlDate.prototype.refresh;

    frappe.ui.form.ControlDate = class extends frappe.ui.form.ControlDate {
        set_formatted_input(value) {
            originalSetFormattedInput.call(this, value);
            if (value) this.render_equivalent_date(value);
        }

        refresh() {
            originalRefresh.call(this);
            if (this.get_value()) this.render_equivalent_date(this.get_value());
        }

        render_equivalent_date(value) {
            try {
                const bs_date = NepaliFunctions.AD2BS(value, "YYYY-MM-DD", "YYYY-MM-DD");
                this.show_equivalent_date(`BS Date: ${bs_date}`);
            } catch (err) {
                console.error("Failed to convert AD to BS", err);
            }
        }

        show_equivalent_date(text) {
            display_equivalent_date(this.$wrapper, text);
        }
    };
}

function extend_with_bs_date_picker() {
    const originalRefresh = frappe.ui.form.ControlDate.prototype.refresh;

    frappe.ui.form.ControlDate = class extends frappe.ui.form.ControlDate {
        make_input() {
            super.make_input();

            this.destroy_existing_datepicker();
            this.setup_nepali_date_picker();
        }

        destroy_existing_datepicker() {
            if (this.datepicker) {
                this.datepicker.destroy();
                this.datepicker = null;
            }
            this.$wrapper.find(".datepicker-icon").remove();
            this.$input.attr("type", "text");
        }

        setup_nepali_date_picker() {
            this.$input.nepaliDatePicker({
                ndpYear: true,
                ndpMonth: true,
                ndpYearCount: 10,
                ndpFormat: 'YYYY-MM-DD',
                closeOnDateSelect: true,
                onChange: (e) => {
                    const bs_date = e.bs;
                    try {
                        const ad_date = NepaliFunctions.BS2AD(bs_date, "YYYY-MM-DD", "YYYY-MM-DD");
                        this.$input.val(bs_date);
                        this.set_model_value(ad_date);
                        this.show_equivalent_date(`AD Date: ${ad_date}`);
                    } catch (err) {
                        console.error("BS to AD conversion failed", err);
                    }
                }
            });

            this.refresh_input();
        }

        refresh() {
            originalRefresh.call(this);
            if (this.get_value()) this.render_equivalent_date(this.get_value());
        }

        set_formatted_input(value) {
            if (!value) return;

            try {
                const bs_date = NepaliFunctions.AD2BS(value, "YYYY-MM-DD", "YYYY-MM-DD");
                this.$input?.val(bs_date);
                this.show_equivalent_date(`AD Date: ${value}`);
            } catch (err) {
                console.error("AD conversion failed", value, err);
            }
        }

        render_equivalent_date(value) {
            this.show_equivalent_date(`AD Date: ${value}`);
        }

        show_equivalent_date(text) {
            display_equivalent_date(this.$wrapper, text);
        }

        format_for_input(value) {
            if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
                try {
                    return NepaliFunctions.AD2BS(value, "YYYY-MM-DD", "YYYY-MM-DD");
                } catch (e) {
                    console.error("format_for_input failed", value, e);
                }
            }
            return '';
        }

        parse(value) {
            if (value === "Today") {
                const bs_today = NepaliFunctions.getToday();
                return NepaliFunctions.BS2AD(bs_today, "YYYY-MM-DD", "YYYY-MM-DD");
            }

            if (/^20\d{2}-\d{2}-\d{2}$/.test(value)) {
                return NepaliFunctions.BS2AD(value, "YYYY-MM-DD", "YYYY-MM-DD");
            }

            return value || '';
        }
    };
}

function display_equivalent_date(wrapper, text) {
    const $target = wrapper.find('.static-input');
    const existing = $target.length ? $target : wrapper;

    const $equivalent = existing.find('.equivalent-date');
    if ($equivalent.length) {
        $equivalent.text(text);
    } else {
        existing.append(`<div class="equivalent-date">${text}</div>`);
    }
}
