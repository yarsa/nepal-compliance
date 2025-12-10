(function waitForFrappeReady() {
  if (
    typeof frappe === "undefined" ||
    !frappe.boot ||
    !frappe.ui?.form?.ControlDate
  ) {
    return setTimeout(waitForFrappeReady, 200);
  }

  if (window._bs_date_picker_overridden) return;
  window._bs_date_picker_overridden = true;

  if (!NepaliCalendarLib || !NepaliDateLib) {
    console.error(
      "NepaliCalendarLib or NepaliDateLib missing. Make sure it is loaded via hooks.py.",
    );
    return;
  }

  const use_ad_date =
    frappe.boot?.use_ad_date !== undefined
      ? frappe.boot.use_ad_date
      : (frappe.boot?.user?.use_ad_date ?? true);
  window.use_ad_date = use_ad_date;

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
  const originalSetFormattedInput =
    frappe.ui.form.ControlDate.prototype.set_formatted_input;
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
        const bs_date = NepaliFunctions.AD2BS(
          value,
          "YYYY-MM-DD",
          "YYYY-MM-DD",
        );
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
  const OriginalControlDate = frappe.ui.form.ControlDate;
  const originalRefresh = OriginalControlDate.prototype.refresh;

  frappe.ui.form.ControlDate = class ControlNepaliDate extends (
    OriginalControlDate
  ) {
    make_input() {
      super.make_input();
      this.remove_default_datepicker();
      this.$input.attr("type", "text");
      this.$input.on("focus", () => this.open_popover());
    }

    remove_default_datepicker() {
      if (this.datepicker) {
        this.datepicker.destroy();
        this.datepicker = null;
      }
      this.$wrapper.find(".datepicker-icon").remove();
    }

    refresh() {
      originalRefresh.call(this);
      const { NepaliDate } = NepaliDateLib;
      let modelValue = this.get_value();

      if (!modelValue) {
        const today = new NepaliDate();
        const bsString = today.format({ format: "YYYY-MM-DD", calendar: "BS" });
        const adString = today.format({ format: "YYYY-MM-DD", calendar: "AD" });

        this.$input?.val(bsString);
        this.set_model_value(bsString);
        this.show_equivalent_date(`AD: ${adString}`);
        return;
      }

      try {
        const nepaliDate = NepaliDate.fromBS(modelValue);
        const bsString = nepaliDate.format({
          format: "YYYY-MM-DD",
          calendar: "BS",
        });
        const adString = nepaliDate.format({
          format: "YYYY-MM-DD",
          calendar: "AD",
        });
        this.$input.val(bsString);
        this.show_equivalent_date(`AD: ${adString}`);
      } catch (err) {
        console.error("AD -> BS conversion error", modelValue, err);
      }
    }
    open_popover() {
      if (this._popover) return;

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

      const close = () => {
        if (!this._popover) return;
        if (NepaliCalendarLib.unmount) {
          NepaliCalendarLib.unmount(this._popover);
        }

        this._popover.remove();
        this._popover = null;
        document.removeEventListener("mousedown", outsideHandler);
      };

      const outsideHandler = (e) => {
        if (!this._popover) return;
        if (!this._popover.contains(e.target) && e.target !== this.$input[0]) {
          close();
        }
      };

      document.addEventListener("mousedown", outsideHandler);

      const selectedBS = this.get_value() || undefined;
      NepaliCalendarLib.render(pop, {
        selectedDateBS: selectedBS,
        onSelect: (selected) => {
          const bs = selected.format({ format: "YYYY-MM-DD", calendar: "BS" });
          const ad = selected.format({ format: "YYYY-MM-DD", calendar: "AD" });

          this.$input.val(bs);
          this.set_model_value(bs);
          this.$input.trigger("change");

          this.show_equivalent_date(`AD: ${ad}`);

          close();
        },
      });
    }

    show_equivalent_date(text) {
      const container = this.$wrapper.find(".static-input").length
        ? this.$wrapper.find(".static-input")
        : this.$wrapper;

      const existing = container.find(".equivalent-date");

      if (existing.length) {
        existing.text(text);
      } else {
        container.append(`<div class="equivalent-date">${text}</div>`);
      }
    }

    parse(value) {
      return value;
    }

    format_for_input(value) {
      return value;
    }
  };
}
