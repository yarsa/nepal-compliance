// Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.ui.form.on("IRD Country Correction", {
	setup(frm) {
		frm.set_query("invoice", () => ({
			filters: {
				docstatus: 1,
			},
		}));
	},

	invoice_type(frm) {
		frm.set_value("invoice", "");
		frm.set_value("company", "");
		frm.set_value("current_country", "");
	},

	invoice(frm) {
		if (!frm.doc.invoice_type || !frm.doc.invoice) {
			return;
		}

		const request_id = (frm._ird_country_request_id || 0) + 1;
		frm._ird_country_request_id = request_id;
		frappe.call({
			method: "nepal_compliance.nepal_compliance.doctype.ird_country_correction.ird_country_correction.get_invoice_details",
			args: {
				invoice_type: frm.doc.invoice_type,
				invoice: frm.doc.invoice,
			},
			callback: (response) => {
				if (request_id !== frm._ird_country_request_id || !response.message) {
					return;
				}
				frm.set_value("company", response.message.company);
				frm.set_value("current_country", response.message.current_country);
			},
		});
	},
});
