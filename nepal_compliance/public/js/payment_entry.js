frappe.ui.form.on("Payment Entry", {
    setup(frm) {
        for (const fieldname of ["tds_receivable_account", "short_payment_write_off_account"]) {
            frm.set_query(fieldname, () => ({
                filters: { company: frm.doc.company, is_group: 0 },
            }));
        }
    },
    refresh(frm) {
        // Create > Payment on an invoice opens a filled draft without firing the party trigger
        if (frm.is_new() && frm.customer_tds_defaults_for !== frm.doc.name) {
            set_customer_tds_defaults(frm);
        }
    },
    party(frm) {
        set_customer_tds_defaults(frm);
    },
    apply_customer_tds(frm) {
        calculate_customer_tds(frm);
    },
    tds_receivable_account(frm) {
        if (frm.doc.apply_customer_tds) {
            calculate_customer_tds(frm);
        }
    },
    write_off_short_payment(frm) {
        calculate_customer_tds(frm);
    },
    short_payment_write_off_account(frm) {
        if (frm.doc.write_off_short_payment) {
            calculate_customer_tds(frm);
        }
    },
    async paid_amount(frm) {
        if (frm.doc.apply_customer_tds || frm.doc.write_off_short_payment) {
            // ERPNext reallocates the invoices from Paid Amount on its own call; redo ours after it
            await frappe.after_ajax();
            calculate_customer_tds(frm);
        }
    },
});

function is_customer_receipt(doc) {
    return doc.docstatus === 0 && doc.payment_type === "Receive" && doc.party_type === "Customer";
}

function set_customer_tds_defaults(frm) {
    const doc = frm.doc;
    frm.customer_tds_defaults_for = doc.name;
    if (!is_customer_receipt(doc) || !doc.party) {
        return;
    }
    frappe.call({
        method: "nepal_compliance.customer_tds.get_customer_tds_defaults",
        args: { company: doc.company, customer: doc.party },
    }).then(async ({ message }) => {
        if (!message) {
            return;
        }
        if (message.apply && message.account && !doc.tds_receivable_account) {
            await frm.set_value("tds_receivable_account", message.account);
        }
        // turning it on fires apply_customer_tds, which nets the TDS off the paid amount
        await frm.set_value("apply_customer_tds", message.apply);
    });
}

function calculate_customer_tds(frm) {
    const doc = frm.doc;
    if (!is_customer_receipt(doc) || (doc.apply_customer_tds && !doc.tds_receivable_account)) {
        return;
    }
    frappe.call({
        method: "nepal_compliance.customer_tds.calculate_customer_tds",
        args: { doc },
        freeze: true,
    }).then(({ message }) => {
        if (!message) {
            return;
        }
        frappe.model.sync(message);
        frm.refresh_fields();
        frm.dirty();
    });
}
