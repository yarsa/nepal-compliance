function convertADtoBS(frm, fieldname, targetField) {
    const date = frm.doc[fieldname] ? frm.doc[fieldname].split(" ")[0] : null;
    if (date) {
        const convertedDate = NepaliFunctions.AD2BS(date, "YYYY-MM-DD", "YYYY-MM-DD");
        frappe.model.set_value(frm.doctype, frm.docname, targetField, convertedDate);
    }
}

function convertBStoAD(frm, fieldname, targetField) {
    const date = frm.doc[fieldname] ? frm.doc[fieldname].split(" ")[0] : null;
    if (date) {
        const convertedDate = NepaliFunctions.BS2AD(date, "YYYY-MM-DD", "YYYY-MM-DD");
        frappe.model.set_value(frm.doctype, frm.docname, targetField, convertedDate);
    }
}

function initializeDatePickers(frm) {
    DatePickerConfig.initializePickers(frm);
}

const dateFields = [
    { from: 'from_date', to: 'from_date_bs' },
    { from: 'to_date', to: 'to_date_bs' },
    { from: 'work_from_date', to: 'work_from_date_bs' },
    { from: 'work_end_date', to: 'work_end_date_bs' },
    { from: 'start_date', to: 'start_date_bs' },
    { from: 'end_date', to: 'end_date_bs' },
    { from: 'att_fr_date', to: 'att_fr_date_bs' },
    { from: 'att_to_date', to: 'att_to_date_bs' },
    { from: 'effective_from', to: 'effective_from_bs' },
    { from: 'effective_to', to: 'effective_to_bs' },
    { from: 'encashment_date', to: 'encashment_date_bs' },
    { from: ['attendance_date', 'posting_date', 'claim_date', 'offer_date', 'date', 'transaction_date'], to: 'nepali_date' }
];

const doctypes = [
    'Attendance Request',
    'Compensatory Leave Request',
    'Employee Advance',
    'Shift Assignment',
    'Shift Request',
    'Employee Benefit Claim',
    'Job Offer',
    'Employee Referral',
    'Shift Assignment Tool',
    'Employee Attendance Tool',
    'Upload Attendance',
    'Leave Period',
    'Leave Policy Assignment',
    'Leave Control Panel',
    'Leave Encashment',
    'Stock Entry',
    'Material Request'
];
const hiddenFields = [
    'nepali_date',
    'from_date_bs',
    'to_date_bs',
    'work_from_date_bs',
    'work_end_date_bs',
    'start_date_bs',
    'end_date_bs',
    'att_fr_date_bs',
    'att_to_date_bs',
    'effective_from_bs',
    'effective_to_bs',
    'encashment_date_bs'
];
doctypes.forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        refresh: function(frm) {
            initializeDatePickers(frm);
            if (frm.doc.posting_date) {
                frm.trigger('posting_date');
            }
            if (frm.doc.claim_date) {
                frm.trigger('claim_date');
            }
            if (frm.doc.from_date) {
                frm.trigger('from_date');
            }
            if (frm.doc.start_date){
                frm.trigger('start_date')
            }
            if(frm.doc.end_date){
                frm.trigger('end_date')
            }
            if (frm.doc.transaction_date){
                frm.trigger('transaction_date')
            }
            hiddenFields.forEach(field => {
                frm.set_df_property(field, 'hidden', 1);
            });
        },

        ...dateFields.reduce((acc, field) => {
            if (Array.isArray(field.from)) {
                field.from.forEach(fromField => {
                    acc[fromField] = function(frm) {
                        convertADtoBS(frm, fromField, field.to); 
                    };
                });

                acc[field.to] = function(frm) {
                    field.from.forEach(fromField => {
                        convertBStoAD(frm, field.to, fromField); 
                    });
                };
            } else {
                acc[field.from] = function(frm) {
                    convertADtoBS(frm, field.from, field.to);
                };

                acc[field.to] = function(frm) {
                    convertBStoAD(frm, field.to, field.from);
                };
            }
            return acc;
        }, {}),
    });
});
