function getPayrollFrequency(frm) {
    return (frm.doc.payroll_frequency || "").toLowerCase();
}

function shouldUseBsEndDate(frm) {
    const use_ad_date =
        (frappe.boot?.use_ad_date !== undefined)
            ? frappe.boot.use_ad_date
            : frappe.boot?.user?.use_ad_date ?? true;
    const frequency = getPayrollFrequency(frm);

    return (frequency === "monthly" || frequency === "") && (!!frm.doc.nepali_start_date || !use_ad_date);
}

function getBsStartIso(frm) {
    if (frm.doc.nepali_start_date) {
        const parsed = NepaliDateLib?.parse?.(frm.doc.nepali_start_date, "BS");
        if (parsed?.year !== undefined) {
            return `${parsed.year}-${String(parsed.monthIndex + 1).padStart(2, "0")}-${String(parsed.day).padStart(2, "0")}`;
        }
    }

    if (frm.doc.start_date) {
        return NepaliFunctions.AD2BS(frm.doc.start_date, false);
    }

    return null;
}

function computeMonthlyEndDate(frm) {
    const bsIso = getBsStartIso(frm);
    if (!bsIso) {
        return null;
    }

    const parts = bsIso.split("-").map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) {
        return null;
    }

    const [by, bm] = parts;
    const monthIndex = bm - 1;
    const daysInMonth =
        typeof NepaliDateLib?.getDaysInMonth === "function"
            ? NepaliDateLib.getDaysInMonth(by, monthIndex)
            : typeof NepaliDateLib?.getMonthLength === "function"
                ? NepaliDateLib.getMonthLength(by, monthIndex)
                : null;

    if (!daysInMonth) {
        return null;
    }

    const adDate = NepaliDateLib.bsToAd(by, monthIndex, daysInMonth);
    if (!(adDate instanceof Date) || isNaN(adDate.getTime())) {
        return null;
    }

    return `${adDate.getUTCFullYear()}-${String(adDate.getUTCMonth() + 1).padStart(2, "0")}-${String(adDate.getUTCDate()).padStart(2, "0")}`;
}

frappe.ui.form.on("Payroll Entry", {
    refresh(frm) {
        frm.set_df_property("nepali_start_date", "hidden", 1);
        frm.set_df_property("nepali_end_date", "hidden", 1);
    },

    set_end_date(frm) {
        if (shouldUseBsEndDate(frm)) {
            const adIso = computeMonthlyEndDate(frm);
            if (adIso) {
                frm.set_value("end_date", adIso);
                frm.set_value("nepali_end_date", NepaliFunctions.AD2BS(adIso));
                frm.refresh_field("end_date");
                frm.refresh_field("nepali_end_date");
                return;
            }
        }

        frappe.call({
            method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date",
            args: {
                frequency: frm.doc.payroll_frequency,
                start_date: frm.doc.start_date,
            },
            callback(r) {
                if (r.message) {
                    frm.set_value("end_date", r.message.end_date);
                }
            },
        });
    },

    start_date(frm) {
        if (frm.doc.start_date) {
            const nepaliStartDate = NepaliFunctions.AD2BS(frm.doc.start_date);
            frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date", nepaliStartDate);
            frm.refresh_field("nepali_start_date");
        }

        frm.trigger("set_end_date");
    },

    end_date(frm) {
        if (frm.doc.end_date) {
            const nepaliEndDate = NepaliFunctions.AD2BS(frm.doc.end_date);
            frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date", nepaliEndDate);
            frm.refresh_field("nepali_end_date");
        }
    },

    nepali_start_date(frm) {
        if (frm.doc.nepali_start_date) {
            const startDate = NepaliFunctions.BS2AD(frm.doc.nepali_start_date);
            frappe.model.set_value(frm.doctype, frm.docname, "start_date", startDate);
            frm.refresh_field("start_date");
            frm.trigger("set_end_date");
        }
    },

    nepali_end_date(frm) {
        if (frm.doc.nepali_end_date) {
            const endDate = NepaliFunctions.BS2AD(frm.doc.nepali_end_date);
            frappe.model.set_value(frm.doctype, frm.docname, "end_date", endDate);
            frm.refresh_field("end_date");
        }
    },
});