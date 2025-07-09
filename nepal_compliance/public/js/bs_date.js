const convertADtoBS = date => NepaliFunctions.AD2BS(date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");
const convertBStoAD = date => NepaliFunctions.BS2AD(date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD");

const hideFields = (frm, fields = []) => {
    fields.forEach(field => frm.set_df_property(field, 'hidden', 1));
};

const createDateFieldTriggers = (datePairs = []) => {
    return datePairs.reduce((triggers, [adField, bsField]) => {
        triggers[adField] = frm => {
            frappe.model.set_value(frm.doctype, frm.docname, bsField, convertADtoBS(frm.doc[adField]));
        };
        triggers[bsField] = frm => {
            frappe.model.set_value(frm.doctype, frm.docname, adField, convertBStoAD(frm.doc[bsField]));
        };
        return triggers;
    }, {});
};

const setupFieldTriggers = (doctype, config) => {
    frappe.ui.form.on(doctype, {
        refresh(frm) {
            if (config.hide_fields) hideFields(frm, config.hide_fields);
            if (config.auto_trigger && frm.doc[config.auto_trigger]) {
                frm.trigger(config.auto_trigger);
            }
            config.refresh_action?.(frm);
        },
        ...createDateFieldTriggers(config.date_pairs)
    });
};

const singleNepaliDateConfig = (field = 'posting_date') => ({
    hide_fields: ['nepali_date'],
    auto_trigger: field,
    date_pairs: [[field, 'nepali_date']]
});

const multipleNepaliDateConfig = (fromField, toField, fromNepali, toNepali) => ({
    hide_fields: [fromNepali, toNepali],
    date_pairs: [[fromField, fromNepali], [toField, toNepali]]
});

const nepaliDateConfig = {
    "Fiscal Year": multipleNepaliDateConfig('year_start_date', 'year_end_date', 'nepali_year_start_date', 'nepali_year_end_date'),
    "Expense Claim": singleNepaliDateConfig('posting_date'),
    "Attendance": {
        hide_fields: ['nepali_date'],
        date_pairs: [['attendance_date', 'nepali_date']],
        refresh_action(frm) {
            if (!frm.is_new() && frm.doc.attendance_date && !frm.doc.nepali_date) {
                const nepali = convertADtoBS(frm.doc.attendance_date);
                frappe.db.set_value(frm.doc.doctype, frm.doc.name, 'nepali_date', nepali)
                    .then(() => frm.reload_doc());
            }
        }
    },
    "Sales Invoice": {
        hide_fields: ['nepali_date'],
        date_pairs: [['posting_date', 'nepali_date']],
        refresh_action(frm) {
            if (!frm.is_new() && frm.doc.posting_date && !frm.doc.nepali_date) {
                const nepali = convertADtoBS(frm.doc.posting_date);
                frappe.db.set_value('Sales Invoice', frm.doc.name, 'nepali_date', nepali)
                    .then(() => frm.reload_doc());
            }
        }
    },
    "Purchase Invoice": {
        hide_fields: ['nepali_date'],
        date_pairs: [['posting_date', 'nepali_date']],
        refresh_action(frm) {
            if (!frm.is_new() && frm.doc.posting_date && !frm.doc.nepali_date) {
                const nepali = convertADtoBS(frm.doc.posting_date);
                frappe.db.set_value('Purchase Invoice', frm.doc.name, 'nepali_date', nepali)
                    .then(() => frm.reload_doc());
            }
        }
    },
    "Leave Allocation": multipleNepaliDateConfig('from_date', 'to_date', 'from_nepali_date_leave_allocation', 'to_nepali_date_leave_allocation'),
    "Leave Application": multipleNepaliDateConfig('from_date', 'to_date', 'from_nepali_date_leave_application', 'to_nepali_date_leave_application'),
    "Holiday List": multipleNepaliDateConfig('from_date', 'to_date', 'nepali_from_date', 'nepali_to_date'),
    "Purchase Order": singleNepaliDateConfig('transaction_date'),
    "Purchase Receipt": singleNepaliDateConfig('posting_date'),
    "Sales Order": singleNepaliDateConfig('transaction_date'),
    "Delivery Note": singleNepaliDateConfig('posting_date'),
    "Payment Entry": singleNepaliDateConfig('posting_date'),
    "Journal Entry": singleNepaliDateConfig('posting_date'),
    "Request for Quotation": singleNepaliDateConfig('transaction_date'),
    "Supplier Quotation": singleNepaliDateConfig('transaction_date'),
    "Quotation": singleNepaliDateConfig('transaction_date'),
    "Blanket Order": multipleNepaliDateConfig('from_date', 'to_date', 'from_nepali_date', 'to_nepali_date'),
    "Landed Cost Voucher": singleNepaliDateConfig('posting_date'),
    "Asset": singleNepaliDateConfig('posting_date'),
    "Asset Repair": singleNepaliDateConfig('transaction_date'),
    "Asset Movement": singleNepaliDateConfig('transaction_date'),
    "Asset Value Adjustment": singleNepaliDateConfig('date'),
    "Asset Capitalization": singleNepaliDateConfig('posting_date'),
    "POS Opening Entry": singleNepaliDateConfig('posting_date'),
    "POS Closing Entry": singleNepaliDateConfig('posting_date'),
    "Loyalty Program": multipleNepaliDateConfig('from_date', 'to_date', 'from_nepali_date', 'to_nepali_date'),
    "Promotional Scheme": multipleNepaliDateConfig('valid_from', 'valid_upto', 'valid_from_bs', 'valid_to_bs'),
    "Pricing Rule": multipleNepaliDateConfig('valid_from', 'valid_upto', 'valid_from_bs', 'valid_to_bs'),
    "Coupon Code": multipleNepaliDateConfig('valid_from', 'valid_upto', 'valid_from_bs', 'valid_to_bs'),
    "Serial No": multipleNepaliDateConfig('warranty_expiry_date', 'amc_expiry_date', 'warranty_expiry_date_bs', 'amc_expiry_date_bs'),
    "Batch": multipleNepaliDateConfig('manufacturing_date', 'expiry_date', 'manufacturing_date_bs', 'expiry_date_bs'),
    "Installation Note": singleNepaliDateConfig('inst_date'),
    "Stock Reconciliation": singleNepaliDateConfig('posting_date'),
    "Quality Inspection": singleNepaliDateConfig('report_date_bs_quality_inspection'),
    "Quick Stock Balance": singleNepaliDateConfig('date'),
    "Bulk Salary Structure Assignment": singleNepaliDateConfig('from_date'),
    "Employee Attendance Tool": singleNepaliDateConfig('date'),
    "Period Closing Voucher": singleNepaliDateConfig('transaction_date'),
    "Invoice Discounting": singleNepaliDateConfig('posting_date'),
    "Dunning": singleNepaliDateConfig('posting_date'),
    "Process Deferred Accounting": singleNepaliDateConfig('posting_date'),
    "POS Invoice": singleNepaliDateConfig('posting_date')
};

Object.entries(nepaliDateConfig).forEach(([doctype, config]) => {
    setupFieldTriggers(doctype, config);
});