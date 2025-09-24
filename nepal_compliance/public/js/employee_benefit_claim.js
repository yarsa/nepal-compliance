frappe.ui.form.on('Employee Benefit Claim', {
    validate: function(frm) {
        if (frm.doc.docstatus === 1) return;

        if (frm.doc.claim_festival_allowance) {
            if (!frm.doc.claimed_amount || frm.doc.claimed_amount === 0) {
                if (frm.doc.max_amount_eligible) {
                    frm.set_value('claimed_amount', frm.doc.max_amount_eligible);
                }
            }
        }
    },

    employee: function(frm) {
        frm.trigger('fetch_max_eligible');
    },
    claim_date: function(frm) {
        frm.trigger('fetch_max_eligible');
    },
    earning_component: function(frm) {
        frm.trigger('fetch_max_eligible');
    },
    claim_festival_allowance: function(frm) {
        frm.trigger('fetch_max_eligible');
    },

    fetch_max_eligible: function(frm) {
        if (frm.doc.docstatus === 1) return;

        if (
            frm.doc.claim_festival_allowance &&
            frm.doc.employee &&
            frm.doc.claim_date &&
            frm.doc.earning_component
        ) {
            frappe.call({
                method: 'nepal_compliance.api.employee_benefit_claim.get_max_amount_eligible',
                args: {
                    employee: frm.doc.employee,
                    claim_date: frm.doc.claim_date
                },
                callback: function(r) {
                    if (!r.exc && r.message !== undefined) {
                        frm.set_value('max_amount_eligible', r.message);

                        if (!frm.doc.claimed_amount || frm.doc.claimed_amount === 0) {
                            frm.set_value('claimed_amount', r.message);
                        }

                        frm.refresh_fields();
                    }
                }
            });
        } else {
            frm.set_value('max_amount_eligible', 0);
            frm.set_value('claimed_amount', 0);
        }
    }
});