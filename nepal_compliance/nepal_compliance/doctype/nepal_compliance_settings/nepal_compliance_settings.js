// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.ui.form.on("Nepal Compliance Settings", {
	refresh(frm) {
		if (!frm.has_perm("write")) {
			return;
		}
		frm.add_custom_button(__("Recompute Taxable Summary"), () => {
			open_date_prompt();
		});
	},
});

function open_date_prompt() {
	let dialog;
	dialog = new frappe.ui.Dialog({
		title: __("Recompute Taxable Summary"),
		fields: [
			{
				fieldname: "fiscal_year",
				fieldtype: "Link",
				options: "Fiscal Year",
				label: __("Fiscal Year"),
				onchange() {
					const fy = dialog.get_value("fiscal_year");
					if (!fy) {
						return;
					}
					frappe.db.get_value(
						"Fiscal Year",
						fy,
						["year_start_date", "year_end_date"],
						(r) => {
							if (r && r.year_start_date) {
								dialog.set_value("from_date", r.year_start_date);
								dialog.set_value("to_date", r.year_end_date);
							}
						}
					);
				},
			},
			{
				fieldname: "from_date",
				fieldtype: "Date",
				label: __("From Posting Date"),
				reqd: 1,
			},
			{
				fieldname: "to_date",
				fieldtype: "Date",
				label: __("To Posting Date"),
				reqd: 1,
			},
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">
					${__(
						"Select a Fiscal Year to fill the dates, or enter a posting date range. Only submitted Sales and Purchase Invoices in this range will be scanned."
					)}
				</p>`,
			},
		],
		primary_action_label: __("Preview"),
		primary_action(values) {
			if (values.from_date > values.to_date) {
				frappe.msgprint(__("From Posting Date cannot be after To Posting Date."));
				return;
			}
			dialog.hide();
			run_preview(values);
		},
	});
	dialog.show();
}

function listen_for_preview_done(values) {
	frappe._taxable_summary_preview_values = values;
	if (frappe._taxable_summary_preview_listener) {
		return;
	}
	frappe._taxable_summary_preview_listener = true;
	frappe.realtime.on("taxable_summary_preview_done", (data) => {
		frappe.hide_progress();
		if (!data) {
			return;
		}
		show_preview_dialog(data, frappe._taxable_summary_preview_values || {});
	});
}

function run_preview(values) {
	frappe.call({
		method: "nepal_compliance.taxable_summary.preview_taxable_summary_refresh",
		args: {
			from_date: values.from_date,
			to_date: values.to_date,
		},
		freeze: true,
		freeze_message: __("Scanning invoices..."),
		callback(r) {
			if (!r.message) {
				return;
			}
			if (r.message.queued) {
				listen_for_preview_done(values);
				frappe.show_progress(
					__("Scanning invoices..."),
					1,
					100,
					__(
						"More than 500 invoices are in this range. Preview is running in the background."
					)
				);
				return;
			}
			show_preview_dialog(r.message, values);
		},
	});
}

function fmt(value) {
	if (value === null || value === undefined || value === "") {
		return "—";
	}
	return format_number(value, null, 2);
}

function show_preview_dialog(preview, values) {
	const fy_line = values.fiscal_year
		? `<li>${__("Fiscal Year")}: <b>${frappe.utils.escape_html(values.fiscal_year)}</b></li>`
		: "";
	const more_line = preview.hidden_rows
		? `<p class="text-muted">${__("…and {0} more invoice(s) not shown in the table. Confirm still updates all of them.", [preview.hidden_rows])}</p>`
		: "";
	const batch_line = preview.batched
		? `<p><b>${__("More than 500 invoices are in this range. Confirm will run in the background in batches of 500.")}</b></p>`
		: "";

	let table = "";
	if (preview.changes && preview.changes.length) {
		const rows = preview.changes
			.map((row) => {
				const name = frappe.utils.escape_html(row.name);
				const company = frappe.utils.escape_html(row.company || "");
				const doctype = frappe.utils.escape_html(row.doctype);
				const invoice_link = frappe.utils.get_form_link(
					row.doctype,
					row.name,
					true,
					name
				);
				return `<tr>
					<td>${doctype}</td>
					<td>${invoice_link}</td>
					<td>${frappe.utils.escape_html(row.posting_date || "")}</td>
					<td>${company}</td>
					<td class="text-right">${fmt(row.old_taxable_amount)} → ${fmt(row.new_taxable_amount)}</td>
					<td class="text-right">${fmt(row.old_non_taxable_amount)} → ${fmt(row.new_non_taxable_amount)}</td>
					<td class="text-right">${fmt(row.old_vat_amount)} → ${fmt(row.new_vat_amount)}</td>
				</tr>`;
			})
			.join("");
		table = `<div class="mt-3" style="max-height: 320px; overflow: auto;">
			<table class="table table-bordered table-sm">
				<thead>
					<tr>
						<th>${__("Type")}</th>
						<th>${__("Invoice")}</th>
						<th>${__("Posting Date")}</th>
						<th>${__("Company")}</th>
						<th>${__("Taxable")}</th>
						<th>${__("Non-Taxable")}</th>
						<th>${__("VAT")}</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		</div>${more_line}`;
	}

	const html = `
		<p>${__("Taxable amount will become the VAT base (VAT ÷ rate). Invoices where VAT is charged on a previous-row total (excise, import duty) will increase. Invoices where VAT is charged on net total stay the same.")}</p>
		<p>${__("Fields that may change: Taxable Amount, Non-Taxable Amount, VAT Amount, and the hidden item VAT detail. IRD Sales/Purchase (and return) registers will use the new taxable column for these invoices. A comment with the new figures is added on each changed invoice.")}</p>
		<ul>
			${fy_line}
			<li>${__("Posting date range")}: <b>${frappe.utils.escape_html(preview.from_date)}</b> – <b>${frappe.utils.escape_html(preview.to_date)}</b></li>
			<li>${__("Scanned")}: <b>${preview.scanned}</b></li>
			<li>${__("Would change")}: <b>${preview.changed}</b> (${__("Sales")}: ${preview.sales_changed}, ${__("Purchase")}: ${preview.purchase_changed})</li>
			<li>${__("Unchanged")}: <b>${preview.unchanged}</b></li>
			<li>${__("Skipped (no VAT account configured)")}: <b>${preview.skipped}</b></li>
		</ul>
		${batch_line}
		${table}
	`;

	const dialog = new frappe.ui.Dialog({
		title: __("Confirm Taxable Summary Refresh"),
		size: "extra-large",
		fields: [{ fieldname: "preview_html", fieldtype: "HTML" }],
		primary_action_label: preview.changed ? __("Apply Changes") : __("Close"),
		primary_action() {
			dialog.hide();
			if (preview.changed) {
				run_apply(values);
			}
		},
	});
	dialog.show();
	dialog.fields_dict.preview_html.$wrapper.html(html);
	if (!preview.changed) {
		dialog.$wrapper.find(".modal-body").prepend(
			`<div class="alert alert-info">${__("No invoices in this range would change.")}</div>`
		);
	}
}

function listen_for_refresh_done() {
	if (frappe._taxable_summary_refresh_listener) {
		return;
	}
	frappe._taxable_summary_refresh_listener = true;
	frappe.realtime.on("taxable_summary_refresh_done", (data) => {
		if (!data) {
			return;
		}
		frappe.msgprint({
			title: __("Taxable Summary Refresh"),
			indicator: "green",
			message: __("Updated {0} invoice(s) from {1} to {2}.", [
				data.updated,
				data.from_date,
				data.to_date,
			]),
		});
	});
}

function run_apply(values) {
	frappe.call({
		method: "nepal_compliance.taxable_summary.apply_taxable_summary_refresh",
		args: {
			from_date: values.from_date,
			to_date: values.to_date,
		},
		freeze: true,
		freeze_message: __("Updating invoices..."),
		callback(r) {
			if (!r.message) {
				return;
			}
			if (r.message.queued) {
				listen_for_refresh_done();
				frappe.msgprint(
					__(
						"More than 500 invoices are in this range. The update is running in the background in batches of 500. You will be notified when it finishes."
					)
				);
				return;
			}
			frappe.msgprint(__("Updated {0} invoice(s).", [r.message.updated]));
		},
	});
}
