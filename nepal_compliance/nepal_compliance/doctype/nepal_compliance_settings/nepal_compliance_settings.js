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
		frm.add_custom_button(__("Audit TDS Bases"), () => {
			open_tds_base_prompt();
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

function listen_for_preview_done() {
	if (frappe._taxable_summary_preview_listener) {
		return;
	}
	frappe._taxable_summary_preview_listener = true;
	frappe._taxable_summary_preview_pending = frappe._taxable_summary_preview_pending || {};
	frappe.realtime.on("taxable_summary_preview_done", (data) => {
		if (!data || !data.request_id) {
			return;
		}
		const pending = frappe._taxable_summary_preview_pending || {};
		const values = pending[data.request_id];
		if (!values) {
			return;
		}
		delete pending[data.request_id];
		frappe.hide_progress();
		if (data.error) {
			frappe.msgprint({
				title: __("Taxable Summary Preview Failed"),
				indicator: "red",
				message: frappe.utils.escape_html(data.error),
			});
			return;
		}
		show_preview_dialog(data, values);
	});
}

function new_preview_request_id() {
	if (window.crypto && typeof window.crypto.randomUUID === "function") {
		return window.crypto.randomUUID();
	}
	return frappe.utils.get_random(16);
}

function run_preview(values) {
	const request_id = new_preview_request_id();
	frappe._taxable_summary_preview_pending = frappe._taxable_summary_preview_pending || {};
	frappe._taxable_summary_preview_pending[request_id] = values;
	listen_for_preview_done();
	frappe.call({
		method: "nepal_compliance.taxable_summary.preview_taxable_summary_refresh",
		args: {
			from_date: values.from_date,
			to_date: values.to_date,
			request_id: request_id,
		},
		freeze: true,
		freeze_message: __("Scanning invoices..."),
		callback(r) {
			if (!r.message) {
				delete frappe._taxable_summary_preview_pending[request_id];
				return;
			}
			if (r.message.queued) {
				if (r.message.duplicate) {
					delete frappe._taxable_summary_preview_pending[request_id];
					frappe.msgprint(
						__("A preview for this date range is already running.")
					);
					return;
				}
				const id = r.message.request_id || request_id;
				if (id !== request_id) {
					frappe._taxable_summary_preview_pending[id] = values;
					delete frappe._taxable_summary_preview_pending[request_id];
				}
				if (!frappe._taxable_summary_preview_pending[id]) {
					return;
				}
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
			delete frappe._taxable_summary_preview_pending[request_id];
			show_preview_dialog(r.message, values);
		},
		error() {
			delete frappe._taxable_summary_preview_pending[request_id];
			frappe.hide_progress();
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
			<li>${__("Denied by permissions")}: <b>${preview.denied || 0}</b></li>
			<li>${__("Failed")}: <b>${preview.failed || 0}</b></li>
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
	frappe._taxable_summary_apply_pending = frappe._taxable_summary_apply_pending || {};
	frappe.realtime.on("taxable_summary_refresh_done", (data) => {
		if (!data || !data.request_id) {
			return;
		}
		const pending = frappe._taxable_summary_apply_pending || {};
		if (!pending[data.request_id]) {
			return;
		}
		delete pending[data.request_id];
		if (data.error) {
			frappe.msgprint({
				title: __("Taxable Summary Refresh Failed"),
				indicator: "red",
				message: frappe.utils.escape_html(data.error),
			});
			return;
		}
		frappe.msgprint({
			title: __("Taxable Summary Refresh"),
			indicator: data.denied || data.failed ? "orange" : "green",
			message: __(
				"Updated {0} invoice(s) from {1} to {2}. Denied: {3}; skipped: {4}; failed: {5}.",
				[
				data.updated,
				data.from_date,
				data.to_date,
				data.denied || 0,
				data.skipped || 0,
				data.failed || 0,
				]
			),
		});
	});
}

function run_apply(values) {
	frappe._taxable_summary_apply_pending = frappe._taxable_summary_apply_pending || {};
	const already_running = Object.values(frappe._taxable_summary_apply_pending).some(
		(pending) =>
			pending.from_date === values.from_date && pending.to_date === values.to_date
	);
	if (already_running) {
		frappe.msgprint(__("An update for this date range is already running."));
		return;
	}
	const request_id = new_preview_request_id();
	frappe._taxable_summary_apply_pending[request_id] = values;
	listen_for_refresh_done();
	frappe.call({
		method: "nepal_compliance.taxable_summary.apply_taxable_summary_refresh",
		args: {
			from_date: values.from_date,
			to_date: values.to_date,
			request_id: request_id,
		},
		freeze: true,
		freeze_message: __("Updating invoices..."),
		callback(r) {
			if (!r.message) {
				delete frappe._taxable_summary_apply_pending[request_id];
				return;
			}
			if (r.message.queued) {
				if (r.message.duplicate) {
					delete frappe._taxable_summary_apply_pending[request_id];
					frappe.msgprint(
						__("An update for this date range is already running.")
					);
					return;
				}
				if (!frappe._taxable_summary_apply_pending[request_id]) {
					return;
				}
				frappe.msgprint(
					__(
						"More than 500 invoices are in this range. The update is running in the background in batches of 500. You will be notified when it finishes."
					)
				);
				return;
			}
			delete frappe._taxable_summary_apply_pending[request_id];
			frappe.msgprint(
				__("Updated {0} invoice(s). Denied: {1}; skipped: {2}; failed: {3}.", [
					r.message.updated,
					r.message.denied || 0,
					r.message.skipped || 0,
					r.message.failed || 0,
				])
			);
		},
		error() {
			delete frappe._taxable_summary_apply_pending[request_id];
			frappe.hide_progress();
		},
	});
}

function open_tds_base_prompt() {
	const dialog = new frappe.ui.Dialog({
		title: __("Audit TDS Bases"),
		fields: [
			{
				fieldname: "fiscal_year",
				fieldtype: "Link",
				options: "Fiscal Year",
				label: __("Fiscal Year"),
				onchange() {
					const fiscal_year = dialog.get_value("fiscal_year");
					if (!fiscal_year) return;
					frappe.db.get_value(
						"Fiscal Year",
						fiscal_year,
						["year_start_date", "year_end_date"],
						(values) => {
							dialog.set_value("from_date", values.year_start_date);
							dialog.set_value("to_date", values.year_end_date);
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
				options: `<p class="text-muted">${__(
					"Preview compares submitted Purchase Invoice TDS bases only. Applying changes the two cumulative-threshold base fields and adds an audit comment; it does not change historical TDS, VAT, or GL entries."
				)}</p>`,
			},
		],
		primary_action_label: __("Preview"),
		primary_action(values) {
			dialog.hide();
			preview_tds_bases(values);
		},
	});
	dialog.show();
}

function preview_tds_bases(values) {
	listen_for_tds_backfill();
	frappe._tds_base_preview_values = values;
	frappe.call({
		method: "nepal_compliance.tds_base_backfill.preview_tds_base_backfill",
		args: values,
		freeze: true,
		freeze_message: __("Auditing TDS bases..."),
		callback(r) {
			if (!r.message) return;
			if (r.message.queued) {
				frappe.msgprint(
					r.message.duplicate
						? __("This TDS-base preview is already running.")
						: __("The TDS-base preview is running in the background.")
				);
				return;
			}
			show_tds_base_preview(r.message, values);
		},
	});
}

function listen_for_tds_backfill() {
	if (frappe._tds_base_listener) return;
	frappe._tds_base_listener = true;
	frappe.realtime.on("tds_base_backfill_preview_done", (result) => {
		const values = frappe._tds_base_preview_values;
		if (values) show_tds_base_preview(result, values);
	});
	frappe.realtime.on("tds_base_backfill_apply_done", show_tds_base_apply_result);
}

function show_tds_base_preview(result, values) {
	const exceptions = (result.exceptions || [])
		.map((row) => {
			const reason = row.reason || __("Wrong historical VAT ledger: {0}", [
				row.wrong_vat_account,
			]);
			return `<li>${frappe.utils.escape_html(row.name)}: ${frappe.utils.escape_html(
				reason
			)}</li>`;
		})
		.join("");
	const dialog = new frappe.ui.Dialog({
		title: __("Confirm TDS-Base Backfill"),
		fields: [
			{
				fieldname: "summary",
				fieldtype: "HTML",
				options: `
					<p>${__("Only TDS base fields will be updated. Historical tax and accounting entries remain unchanged.")}</p>
					<ul>
						<li>${__("Scanned")}: <b>${result.scanned}</b></li>
						<li>${__("Would change")}: <b>${result.changed}</b></li>
						<li>${__("Unchanged")}: <b>${result.unchanged}</b></li>
						<li>${__("Category option off")}: <b>${result.option_off}</b></li>
						<li>${__("Unavailable VAT data")}: <b>${result.unavailable}</b></li>
						<li>${__("Wrong historical VAT ledger")}: <b>${result.wrong_ledger}</b></li>
						<li>${__("Permission denied")}: <b>${result.denied}</b></li>
						<li>${__("Failed")}: <b>${result.failed}</b></li>
					</ul>
					${exceptions ? `<p><b>${__("Accounting review required")}</b></p><ul>${exceptions}</ul>` : ""}
				`,
			},
		],
		primary_action_label: result.changed ? __("Apply Approved Backfill") : __("Close"),
		primary_action() {
			dialog.hide();
			if (result.changed) apply_tds_bases(values);
		},
	});
	dialog.show();
}

function apply_tds_bases(values) {
	frappe.call({
		method: "nepal_compliance.tds_base_backfill.apply_tds_base_backfill",
		args: { ...values, confirmed: 1 },
		freeze: true,
		freeze_message: __("Updating approved TDS bases..."),
		callback(r) {
			if (!r.message) return;
			if (r.message.queued) {
				frappe.msgprint(__("The approved TDS-base backfill is running in the background."));
				return;
			}
			show_tds_base_apply_result(r.message);
		},
	});
}

function show_tds_base_apply_result(result) {
	frappe.msgprint({
		title: __("TDS-Base Backfill"),
		indicator: result.failed || result.denied ? "orange" : "green",
		message: __(
			"Updated {0} invoice(s). Wrong ledger: {1}; unavailable: {2}; denied: {3}; failed: {4}.",
			[
				result.updated,
				result.wrong_ledger || 0,
				result.unavailable || 0,
				result.denied || 0,
				result.failed || 0,
			]
		),
	});
}
