function convertToNepaliAndSet(frm, ad_field, bs_field) {
    if (frm.doc[ad_field]) {
        const bs = NepaliFunctions.AD2BS(frm.doc[ad_field].split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
        frappe.model.set_value(frm.doctype, frm.docname, bs_field, bs);
    }
}

function convertToADAndSet(frm, bs_field, ad_field) {
    if (frm.doc[bs_field]) {
        const ad = NepaliFunctions.BS2AD(frm.doc[bs_field].split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
        frappe.model.set_value(frm.doctype, frm.docname, ad_field, ad);
    }
}

function hideNepaliField(frm, fieldname = 'nepali_date') {
    frm.set_df_property(fieldname, 'hidden', 1);
}

const nepaliDateConfig = {
    "Payroll Entry": {
        mappings: [
            { ad: "start_date", bs: "nepali_start_date" },
            { ad: "end_date", bs: "nepali_end_date" }
        ]
    },
    "Income Tax Slab": {
        mappings: [
            { ad: "effective_from", bs: "nepali_date" }
        ],
        initDatePicker: true
    },
    "Payroll Period": {
        mappings: [
            { ad: "start_date", bs: "nepali_start_date" },
            { ad: "end_date", bs: "nepali_end_date" }
        ]
    },
    "Salary Structure Assignment": {
        mappings: [
            { ad: "from_date", bs: "nepali_date", reverseSet: "form_date" }
        ],
        initDatePicker: true
    },
    "Salary Withholding": { mappings: [{ ad: "posting_date", bs: "nepali_date" }] },
    "Additional Salary": { mappings: [{ ad: "payroll_date", bs: "nepali_date" }] },
    "Employee Incentive": { mappings: [{ ad: "payroll_date", bs: "nepali_date" }] },
    "Retention Bonus": { mappings: [{ ad: "bonus_payment_date", bs: "nepali_date" }] },
    "Employee Tax Exemption Proof Submission": { mappings: [{ ad: "payroll_date", bs: "nepali_date" }] },
    "Employee Benefit Application": { mappings: [{ ad: "payroll_date", bs: "nepali_date" }] },
    "Employee Benefit Claim": { mappings: [{ ad: "claim_date", bs: "nepali_date" }] }
};

Object.keys(nepaliDateConfig).forEach(doctype => {
    const config = nepaliDateConfig[doctype];
    const fieldMappings = config.mappings;

    frappe.ui.form.on(doctype, {
        refresh(frm) {
            if (config.initDatePicker) {
                DatePickerConfig.initializePickers(frm);
            }
            fieldMappings.forEach(map => {
                hideNepaliField(frm, map.bs);
            });

            if (doctype === "Salary Structure Assignment" && !frm.is_new()) {
                setTimeout(() => {
                    const map = fieldMappings[0];
                    if (frm.doc[map.ad] && !frm.doc[map.bs]) {
                        const nepali = NepaliFunctions.AD2BS(frm.doc[map.ad].split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
                        frappe.db.set_value(frm.doc.doctype, frm.doc.name, map.bs, nepali).then(() => { frm.reload_doc(); });
                    }
                }, 100);
            }
        },
        ...Object.fromEntries(fieldMappings.flatMap(map => [
            [
                map.ad,
                function (frm) {
                    convertToNepaliAndSet(frm, map.ad, map.bs);
                }
            ],
            [
                map.bs,
                function (frm) {
                    const targetField = map.reverseSet || map.ad;
                    convertToADAndSet(frm, map.bs, targetField);
                }
            ]
        ]))
    });
});
