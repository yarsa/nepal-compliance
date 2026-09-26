frappe.ui.form.on("Payment Entry", {
    setup(frm) {
        frm.set_query("tds_receivable_account", () => ({
            filters: { company: frm.doc.company, is_group: 0 },
        }));
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
});

function set_customer_tds_defaults(frm) {
    const doc = frm.doc;
    frm.customer_tds_defaults_for = doc.name;
    if (doc.docstatus !== 0 || doc.payment_type !== "Receive" || doc.party_type !== "Customer" || !doc.party) {
        return;
    }
    frappe.call({
        method: "nepal_compliance.customer_tds.get_customer_tds_defaults",
        args: { company: doc.company, customer: doc.party },
    }).then(({ message }) => {
        if (!message) {
            return;
        }
        frm.set_value("apply_customer_tds", message.apply);
        if (message.apply && message.account && !doc.tds_receivable_account) {
            frm.set_value("tds_receivable_account", message.account);
        }
    });
}
