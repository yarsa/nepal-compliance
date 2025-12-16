function getUserDateFormat() {
    return frappe?.boot?.nepal_compliance?.date_format || "YYYY-MM-DD";
}

const USER_DATE_FORMAT = getUserDateFormat();

function formatDate(y, m, d, format) {
    const map = {
        YYYY: y,
        MM: String(m).padStart(2, "0"),
        M: m,
        DD: String(d).padStart(2, "0"),
        D: d
    };

    return format.replace(/YYYY|MM|DD|M|D/g, k => map[k]);
}

function parseUserDate(str, format) {
    if (!str) return null;

    const nums = str.match(/\d+/g);
    const fmt = format.match(/YYYY|MM|DD|M|D/g);

    if (!nums || !fmt || nums.length !== fmt.length) return null;

    let y, m, d;
    fmt.forEach((f, i) => {
        if (f === "YYYY") y = Number(nums[i]);
        if (f === "MM" || f === "M") m = Number(nums[i]);
        if (f === "DD" || f === "D") d = Number(nums[i]);
    });

    if (![y, m, d].every(Number.isFinite)) return null;
    return { y, m, d };
}

window.NepaliFunctions = {
    AD2BS(adString, forDisplay = true) {
        if (!adString || typeof adString !== "string") return null;

        const [y, m, d] = adString.split("-").map(Number);
        if (![y, m, d].every(Number.isFinite)) return null;

        const date = new Date(Date.UTC(y, m - 1, d));
        if (isNaN(date.getTime())) return null;

        const bs = NepaliDateLib.adToBs(date);
        if (!bs?.year) return null;

        const isoBS = `${bs.year}-${String(bs.monthIndex + 1).padStart(2, "0")}-${String(bs.day).padStart(2, "0")}`;

        if (forDisplay) {
            return formatDate(bs.year, bs.monthIndex + 1, bs.day, USER_DATE_FORMAT);
        } else {
            return isoBS;
        }
    },

    BS2AD(bsString) {
        const parsed = parseUserDate(bsString, USER_DATE_FORMAT);
        if (!parsed) return null;

        const { y, m, d } = parsed;
        const ad = NepaliDateLib.bsToAd(y, m - 1, d);
        if (!(ad instanceof Date) || isNaN(ad.getTime())) return null;

        return `${ad.getUTCFullYear()}-${String(ad.getUTCMonth() + 1).padStart(2, "0")}-${String(ad.getUTCDate()).padStart(2, "0")}`;
    },

    getToday() {
        const bs = NepaliDateLib.adToBs(new Date());
        return formatDate(bs.year, bs.monthIndex + 1, bs.day, USER_DATE_FORMAT);
    }
};

(function waitForFrappeReady() {
    if (
        typeof frappe === "undefined" ||
        !frappe.boot ||
        !frappe.ui?.form?.ControlDate
    ) {
        return setTimeout(waitForFrappeReady, 200);
    }

    if (window._date_picker_overridden) return;
    window._date_picker_overridden = true;

    const use_ad_date =
        (frappe.boot?.use_ad_date !== undefined)
            ? frappe.boot.use_ad_date
            : frappe.boot?.user?.use_ad_date ?? true;

    override_with_nepali_date_picker(use_ad_date);
})();

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
                const bs_date = NepaliFunctions.AD2BS(value);
                this.show_equivalent_date(`BS Date: ${bs_date}`);
            } catch (err) {
                console.error("Failed AD → BS", err);
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

            if (this.datepicker) {
                this.datepicker.destroy();
                this.datepicker = null;
            }

            this.$wrapper.find(".datepicker-icon").remove();

            if (this.$input) {
                this.$input.attr("type", "text");
                this.$input.on("focus", () => this.open_popover());
            }
        }

        safe_set_input(value) {
            if (this.$input && this.$input.length) {
                this.$input.val(value);
            } else {
                const staticField = this.$wrapper.find(".static-input");
                if (staticField.length) staticField.text(value);
            }
        }

        refresh() {
            originalRefresh.call(this);

            const valueAD = this.get_value();
            if (!valueAD) return;

            try {
                const bs = NepaliFunctions.AD2BS(valueAD);
                this.safe_set_input(bs);
                this.show_equivalent_date(`AD Date: ${valueAD}`);
            } catch (err) {
                console.error("Refresh AD→BS failed", err);
            }
        }

        open_popover() {
            if (this._popover || !this.$input) return;

            const rect = this.$input[0].getBoundingClientRect();
            const pop = document.createElement("div");
            pop.classList.add("nepali-calendar-popover");

            Object.assign(pop.style, {
                position: "absolute",
                top: rect.bottom + window.scrollY + "px",
                left: rect.left + window.scrollX + "px",
                zIndex: 99999,
            });

            document.body.appendChild(pop);
            this._popover = pop;

            const onClose = () => {
                NepaliCalendarLib.unmount?.(pop);
                pop.remove();
                this._popover = null;
                document.removeEventListener("mousedown", outsideClick);
            };

            const outsideClick = (e) => {
                if (!pop.contains(e.target) && e.target !== this.$input[0]) onClose();
            };

            document.addEventListener("mousedown", outsideClick);

            const ad = this.get_value();
            const bs = ad ? NepaliFunctions.AD2BS(ad, false) : undefined;

            NepaliCalendarLib.render(pop, {
                selectedDateBS: bs,
                onSelect: (selected) => {
                    const bsDate = selected.format({ format: "YYYY-MM-DD", calendar: "BS" });
                    const adDate = selected.format({ format: "YYYY-MM-DD", calendar: "AD" });
                    const parsed = parseUserDate(bsDate, "YYYY-MM-DD");
                    const bsDisplay = formatDate(parsed.y, parsed.m, parsed.d, USER_DATE_FORMAT);
                    this.safe_set_input(bsDisplay);
                    this.set_model_value(adDate);
                    
                    this.$input?.trigger("change");

                    this.show_equivalent_date(`AD Date: ${adDate}`);

                    onClose();
                }
            });
        }

        format_for_input(valueAD) {
            try {
                return NepaliFunctions.AD2BS(valueAD);
            } catch {
                return valueAD;
            }
        }

        set_formatted_input(valueAD) {
            try {
                const bs = NepaliFunctions.AD2BS(valueAD);
                this.safe_set_input(bs);
                this.show_equivalent_date(`AD Date: ${valueAD}`);
            } catch {
                this.safe_set_input(valueAD);
            }
        }

        parse(valueBS) {
            try {
                return NepaliFunctions.BS2AD(valueBS);
            } catch {
                return valueBS;
            }
        }

        show_equivalent_date(text) {
            display_equivalent_date(this.$wrapper, text);
        }
    };
}

function display_equivalent_date(wrapper, text) {
    const $target = wrapper.find('.static-input');
    const container = $target.length ? $target : wrapper;

    if (!text || text.includes("undefined") || text.includes("null")) {
        container.find('.equivalent-date').remove();
        return;
    }

    const $eq = container.find('.equivalent-date');
    if ($eq.length) {
        $eq.text(text);
    } else {
        container.append(`<div class="equivalent-date">${text}</div>`);
    }
}