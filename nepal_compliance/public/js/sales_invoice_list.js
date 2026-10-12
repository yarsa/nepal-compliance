// Bulk download: merge the attached Tax Invoice and/or Invoice copies of the
// selected invoices into one PDF, to print or file a batch at once.
const INVOICE_COPY_FIELDS = {
	tax_invoice: ["tax_invoice_attachment"],
	invoice: ["invoice_attachment"],
	both: ["tax_invoice_attachment", "invoice_attachment"],
};

// Wraps any onload set before this file, once even if the list script runs again.
const sales_invoice_list = (frappe.listview_settings["Sales Invoice"] ||= {});
if (!sales_invoice_list.nc_invoice_download) {
	sales_invoice_list.nc_invoice_download = true;
	const previous_onload = sales_invoice_list.onload;
	sales_invoice_list.onload = function (listview) {
		previous_onload?.call(this, listview);
		listview.page.add_actions_menu_item(
			__("Download Attached Invoices"),
			() => open_invoice_download(listview),
			false
		);
	};
}

function open_invoice_download(listview) {
	const names = listview.get_checked_items(true);
	const dialog = new frappe.ui.Dialog({
		title: __("Download Attached Invoices"),
		fields: [
			{
				fieldname: "copies",
				fieldtype: "Select",
				label: __("Copies"),
				reqd: 1,
				default: "both",
				options: [
					{ value: "tax_invoice", label: __("Tax Invoice (customer copy)") },
					{ value: "invoice", label: __("Invoice (company copy)") },
					{ value: "both", label: __("Both: all tax invoices, then all invoices") },
				],
			},
		],
		primary_action_label: __("Download"),
		async primary_action({ copies }) {
			const fields = INVOICE_COPY_FIELDS[copies];
			const rows = await frappe.db.get_list("Sales Invoice", {
				filters: { name: ["in", names] },
				fields: ["name", ...fields],
				limit: names.length,
			});
			const missing = rows.filter((row) => fields.some((field) => !row[field])).map((row) => row.name);
			const download = () => {
				dialog.hide();
				open_url_post("/api/method/nepal_compliance.invoice_download.download_attached_invoices", {
					names: JSON.stringify(names),
					copies,
				});
			};
			if (!missing.length) {
				download();
			} else if (!rows.some((row) => fields.some((field) => row[field]))) {
				frappe.msgprint(__("None of the selected invoices has that copy attached."));
			} else {
				frappe.confirm(
					__("{0} of {1} invoices are missing an attached copy, which is left out: {2}. Download the rest?", [
						missing.length,
						rows.length,
						missing.map((name) => frappe.utils.escape_html(name)).join(", "),
					]),
					download
				);
			}
		},
	});
	dialog.show();
}
