frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        sync_nepali_date(frm, "transaction_date");
        attach_bs_picker(frm, "transaction_date");
    },
    transaction_date(frm) {
        sync_nepali_date(frm, "transaction_date");
    },
    nepali_date(frm) {
        sync_ad_date(frm, "transaction_date");
    }
});

// Keep the BS "Nepali Date" field in sync with the AD date field both ways.
function sync_nepali_date(frm, ad_field) {
    if (typeof NepaliFunctions === "undefined") return;
    const ad_value = frm.doc[ad_field];
    if (!ad_value) return;

    const bs = NepaliFunctions.AD2BS(ad_value);
    if (bs && frm.doc.nepali_date !== bs) {
        frm.set_value("nepali_date", bs);
    }
}

function sync_ad_date(frm, ad_field) {
    if (typeof NepaliFunctions === "undefined") return;
    if (!frm.doc.nepali_date) return;

    const ad = NepaliFunctions.BS2AD(frm.doc.nepali_date);
    if (ad && frm.doc[ad_field] !== ad) {
        frm.set_value(ad_field, ad);
    }
}

// Open a BS calendar popover when the user clicks the "Nepali Date" field,
// so it can be set manually with a picker (not just typed).
function attach_bs_picker(frm, ad_field) {
    if (typeof NepaliCalendarLib === "undefined" || typeof NepaliFunctions === "undefined") return;

    const field = frm.get_field("nepali_date");
    if (!field || !field.$input || field._bs_picker_attached) return;
    field._bs_picker_attached = true;

    field.$input.on("focus", () => open_bs_popover(frm, field, ad_field));
}

function open_bs_popover(frm, field, ad_field) {
    if (field._popover || !field.$input) return;

    const rect = field.$input[0].getBoundingClientRect();
    const pop = document.createElement("div");
    pop.classList.add("nepali-calendar-popover");
    Object.assign(pop.style, {
        position: "absolute",
        top: rect.bottom + window.scrollY + "px",
        left: rect.left + window.scrollX + "px",
        zIndex: 99999,
    });
    document.body.appendChild(pop);
    field._popover = pop;

    const close = () => {
        NepaliCalendarLib.unmount?.(pop);
        pop.remove();
        field._popover = null;
        document.removeEventListener("mousedown", outside);
    };
    const outside = (e) => {
        if (!pop.contains(e.target) && e.target !== field.$input[0]) close();
    };
    document.addEventListener("mousedown", outside);

    let selectedBS;
    if (frm.doc.nepali_date) {
        const ad = NepaliFunctions.BS2AD(frm.doc.nepali_date);
        if (ad) selectedBS = NepaliFunctions.AD2BS(ad, false);
    } else if (frm.doc[ad_field]) {
        selectedBS = NepaliFunctions.AD2BS(frm.doc[ad_field], false);
    }

    NepaliCalendarLib.render(pop, {
        selectedDateBS: selectedBS,
        onSelect: (selected) => {
            const adDate = selected.format({ format: "YYYY-MM-DD", calendar: "AD" });
            frm.set_value(ad_field, adDate);
            frm.set_value("nepali_date", NepaliFunctions.AD2BS(adDate, true));
            close();
        }
    });
}
