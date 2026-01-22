frappe.provide('frappe.listview_settings');

const DatePickerConfig = {

    _eventsAttached: false,

    FIELDS: [
        'nepali_date', 'from_nepali_date', 'to_nepali_date',
        'nepali_start_date', 'nepali_end_date',
        'valid_from_bs', 'valid_to_bs',
        'from_date_bs', 'to_date_bs',
        'start_date_bs', 'end_date_bs',
        'att_fr_date_bs', 'att_to_date_bs',
        'effective_from_bs', 'effective_to_bs',
        'manufacturing_date_bs', 'expiry_date_bs',
        'encashment_date_bs'
    ],

    initializePickers(listview) {
        this.listview = listview;
        this._initializePickerInputs();
    },

    _initializePickerInputs() {
        this.FIELDS.forEach(fieldname => {
            const input = $(`input[data-fieldname="${fieldname}"]`);
            if (!input.length) return;
            if (input.hasClass("nepali-picker-initialized")) return;

            input.addClass("nepali-picker-initialized");
            this.setupInput(input);
            this.setupCalendarPopover(input);
        });
    },

    setupInput($input) {
        $input.attr("type", "text");

        if (!$input.parent().hasClass("picker-wrap")) {
            $input.wrap(`<div class="picker-wrap" style="position:relative;"></div>`);
        }

        const wrap = $input.parent();
        if (!wrap.find(".nepali-calendar-icon").length) {
            wrap.append(`
                <i class="fa fa-calendar nepali-calendar-icon"
                   style="position:absolute;right:8px;top:50%;transform:translateY(-50%);cursor:pointer;"></i>
            `);
        }

        wrap.find(".nepali-calendar-icon").on("click", () => {
            $input.trigger("focus");
        });
    },

    setupCalendarPopover($input) {
        $input.on("focus", () => {
            if ($input.data("nepali-popover")) return;

            const rect = $input[0].getBoundingClientRect();
            const pop = document.createElement("div");

            Object.assign(pop.style, {
                position: "absolute",
                top: rect.bottom + window.scrollY + "px",
                left: rect.left + window.scrollX + "px",
                zIndex: 999999,
                background: "white",
                border: "1px solid #ddd",
                borderRadius: "6px",
                boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
            });

            document.body.appendChild(pop);
            $input.data("nepali-popover", pop);

            const close = () => {
                NepaliCalendarLib.unmount?.(pop);
                pop.remove();
                $input.removeData("nepali-popover");
                document.removeEventListener("mousedown", handleOutside);
            };

            const handleOutside = (e) => {
                if (!pop.contains(e.target) && e.target !== $input[0]) close();
            };
            document.addEventListener("mousedown", handleOutside);

            const currentValue = $input.val();
            let initialBS = currentValue || (NepaliFunctions?.getToday?.() ?? '');
            if (initialBS && typeof initialBS === "string") {
                initialBS = initialBS.replace(/\./g, "-");
            }
            if (typeof NepaliCalendarLib?.render !== "function") {
                console.warn("NepaliCalendarLib.render is not available");
                close();
                return;
            }

            NepaliCalendarLib.render(pop, {
                selectedDateBS: initialBS,
                onSelect: (dateObj) => {
                    const bs = dateObj.format({ format: "YYYY-MM-DD", calendar: "BS" });
                    const ad = dateObj.format({ format: "YYYY-MM-DD", calendar: "AD" });

                    // $input.val(bs).trigger("change");
                    const parsed = bs.split("-").map(Number);
                    const bsDisplay = NepaliFunctions?.AD2BS?.(ad) || bs;
                    $input.val(bsDisplay).trigger("change");
                    $input.data("ad-value", ad);

                    close();
                }
            });
        });
    },

    attachEvents(listview) {
        if (this._eventsAttached) return;
        this._eventsAttached = true;
        
        $(document).on("change", "input.nepali-picker-initialized", (e) => {
            // const fieldName = $inp.attr("data-fieldname");
            const $inp = $(e.target);
            const fieldName = $inp.attr("data-fieldname");
            const adValue = $inp.data("ad-value");
            if (!adValue) return;
            const adFieldName = fieldName.endsWith("_bs") 
                ? fieldName.slice(0, -3) 
                : fieldName;

            listview.filter_area?.add([
                [listview.doctype, adFieldName, "=", adValue]
            ]);

            listview.refresh();
        });
    }
};

function enableNepaliDateFilters(doctype) {
    const existing = frappe.listview_settings[doctype] || {};
    const existingOnload = existing.onload;
    
    frappe.listview_settings[doctype] = {
        ...existing,
        onload(listview) {
            if (existingOnload) existingOnload.call(this, listview);
            DatePickerConfig.initializePickers(listview);
            DatePickerConfig.attachEvents(listview);
        }
    };
}

[   "Purchase Invoice", "GL Entry", "Sales Invoice",
    "Journal Entry", "POS Invoice", "Employee Attendance Tool"
].forEach(enableNepaliDateFilters);