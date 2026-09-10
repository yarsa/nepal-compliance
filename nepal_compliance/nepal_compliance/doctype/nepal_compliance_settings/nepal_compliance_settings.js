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
				fieldname: "recompute_help_button",
				fieldtype: "HTML",
				options: `<div class="text-right">
					<button type="button" class="btn btn-xs btn-default recompute-help" title="${__(
						"About Recompute Taxable Summary"
					)}">?</button>
				</div>`,
			},
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
				fieldname: "consider_is_non_taxable_item",
				fieldtype: "Check",
				label: __("Consider Is Non-Taxable Item"),
				default: 0,
				description: __(
					"Classify flagged item rows as non-taxable. A Purchase Invoice is fully non-taxable when it is a PAN/Abbreviated Bill, has no tax rows, or has zero recorded VAT."
				),
			},
			{
				fieldname: "help",
				fieldtype: "HTML",
				options: `<p class="text-muted">
					${__(
						"Only submitted Sales and Purchase Invoices in this range will be scanned. VAT calculation mismatches are warnings; VAT recorded in invoice tax rows is retained."
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
	dialog.fields_dict.recompute_help_button.$wrapper
		.find(".recompute-help")
		.on("click", show_taxable_summary_help);
}

function show_taxable_summary_help() {
	frappe.msgprint({
		title: __("About Recompute Taxable Summary"),
		message: `
			<p>${__(
				"Use this tool to preview and correct the Taxable Amount, Non-Taxable Amount, VAT Amount, Bill Total, and item VAT summary stored on submitted Sales and Purchase Invoices. You can select which suggestions to apply."
			)}</p>
			<p><b>${__("Example")}</b></p>
			<ul>
				<li>${__("Taxable item total")}: ${fmt(4189.33)}</li>
				<li>${__("Non-taxable item total")}: ${fmt(28029)}</li>
				<li>${__("Expected VAT")}: ${fmt(4189.33)} × 13% = ${fmt(544.61)}</li>
				<li>${__("Bill Total")}: ${fmt(32218.33)} + ${fmt(544.61)} = ${fmt(32762.94)}</li>
			</ul>
			<p>${__(
				"If Is PAN/Abbreviated Bill is checked, a Purchase Invoice has no Taxes and Charges rows, or its recorded VAT is zero, all its items are treated as non-taxable and expected VAT is zero."
			)}</p>
			<p>${__(
				"If VAT is charged on a previous tax row (import duty, excise, or similar), taxable value is the VAT base (item net plus those added taxes), then expected VAT is that base × 13%."
			)}</p>
		`,
		indicator: "blue",
	});
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
			consider_is_non_taxable_item: values.consider_is_non_taxable_item || 0,
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
	const batch_line = preview.batched
		? `<p><b>${__("More than 500 invoices were scanned. Large selections will be applied in the background.")}</b></p>`
		: "";
	const suggestions = preview.changes || [];
	const can_select = (row) => row.would_change;
	const selectable_count = suggestions.filter(can_select).length;
	const selected = new Set(
		suggestions
			.map((row, index) => (can_select(row) ? index : null))
			.filter((index) => index !== null)
	);
	const page_size = 50;
	let page = 0;

	const html = `
		<p>${__("When the item flag option is enabled, flagged item totals are Non-Taxable and the remaining item totals are Taxable. A Purchase Invoice is fully non-taxable when it is a PAN/Abbreviated Bill, has no tax rows, or has zero recorded VAT. Expected VAT is Taxable × 13%, including duty or excise when VAT is charged on a previous tax row. A mismatch is reported, but recorded VAT is retained.")}</p>
		<p>${__("Applying updates only the selected taxable-summary suggestions. The audit comment records old and new Taxable, Non-Taxable, VAT, and Bill Total values.")}</p>
		<ul>
			${fy_line}
			<li>${__("Posting date range")}: <b>${frappe.utils.escape_html(preview.from_date)}</b> – <b>${frappe.utils.escape_html(preview.to_date)}</b></li>
			<li>${__("Consider Is Non-Taxable Item")}: <b>${preview.consider_is_non_taxable_item ? __("Yes") : __("No")}</b></li>
			<li>${__("Scanned")}: <b>${preview.scanned}</b></li>
			<li>${__("Would change")}: <b>${preview.changed}</b> (${__("Sales")}: ${preview.sales_changed}, ${__("Purchase")}: ${preview.purchase_changed})</li>
			<li>${__("Calculation warnings")}: <b>${preview.calculation_warnings || 0}</b></li>
			<li>${__("Unchanged")}: <b>${preview.unchanged}</b></li>
			<li>${__("Skipped (no VAT account configured)")}: <b>${preview.skipped}</b></li>
			<li>${__("Denied by permissions")}: <b>${preview.denied || 0}</b></li>
			<li>${__("Failed")}: <b>${preview.failed || 0}</b></li>
		</ul>
		${batch_line}
		<div class="taxable-summary-selection ${suggestions.length ? "" : "hide"}">
			<div class="d-flex align-items-center mb-2" style="gap: 8px; flex-wrap: wrap;">
				<button type="button" class="btn btn-xs btn-default select-all">${__("Select All")}</button>
				<button type="button" class="btn btn-xs btn-default unselect-all">${__("Unselect All")}</button>
				<select class="form-control input-xs document-type-filter" style="width: auto;">
					<option value="Sales Invoice">${__("Sales Invoice")}</option>
					<option value="Sales Return">${__("Sales Return")}</option>
					<option value="Purchase Invoice">${__("Purchase Invoice")}</option>
					<option value="Purchase Return">${__("Purchase Return")}</option>
				</select>
				<button type="button" class="btn btn-xs btn-default select-type">${__("Select Type")}</button>
				<button type="button" class="btn btn-xs btn-default unselect-type">${__("Unselect Type")}</button>
				<button type="button" class="btn btn-xs btn-default download-csv">${__("Download CSV")}</button>
				<span class="selected-count text-muted"></span>
				<span class="pagination-controls ml-auto">
					<button type="button" class="btn btn-xs btn-default previous-page">${__("Previous")}</button>
					<span class="page-count mx-2"></span>
					<button type="button" class="btn btn-xs btn-default next-page">${__("Next")}</button>
				</span>
			</div>
			<div style="max-height: 420px; overflow: auto;">
				<table class="table table-bordered table-sm">
					<thead>
						<tr>
							<th style="width: 32px;"></th>
							<th>${__("Type")}</th>
							<th>${__("Invoice")}</th>
							<th>${__("Posting Date")}</th>
							<th>${__("Company")}</th>
							<th>${__("Taxable")}</th>
							<th>${__("Non-Taxable")}</th>
							<th>${__("VAT")}</th>
							<th>${__("Bill Total")}</th>
							<th>${__("Calculation Check")}</th>
						</tr>
					</thead>
					<tbody class="suggestion-rows"></tbody>
				</table>
			</div>
		</div>
	`;

	const dialog = new frappe.ui.Dialog({
		title: __("Confirm Taxable Summary Refresh"),
		size: "extra-large",
		fields: [{ fieldname: "preview_html", fieldtype: "HTML" }],
		primary_action_label: selectable_count ? __("Apply Changes") : __("Close"),
		primary_action() {
			if (!selectable_count) {
				dialog.hide();
				return;
			}
			const selected_invoices = [...selected]
				.filter((index) => can_select(suggestions[index]))
				.map((index) => ({
					doctype: suggestions[index].doctype,
					name: suggestions[index].name,
				}));
			if (!selected_invoices.length) {
				frappe.msgprint(__("Select at least one suggestion to apply."));
				return;
			}
			dialog.hide();
			run_apply(values, selected_invoices);
		},
	});
	dialog.show();
	const $wrapper = dialog.fields_dict.preview_html.$wrapper;
	$wrapper.html(html);

	const render_row = (row, extra_check) => {
		const name = frappe.utils.escape_html(row.name);
		const invoice_link = frappe.utils.get_form_link(
			row.doctype,
			row.name,
			true,
			name
		);
		const check = row.calculation_check || {};
		const calculation = check.has_vat_mismatch
			? `<span class="text-danger">${__(
					"Expected {0}; recorded {1}; difference {2}",
					[
						fmt(check.expected_vat),
						fmt(check.recorded_vat),
						fmt(check.vat_difference),
					]
				)}</span>`
			: `<span class="text-success">${__("OK")}</span>`;
		return `${extra_check}
			<td>${frappe.utils.escape_html(row.document_type || row.doctype)}</td>
			<td>${invoice_link}</td>
			<td>${frappe.utils.escape_html(row.posting_date || "")}</td>
			<td>${frappe.utils.escape_html(row.company || "")}</td>
			<td class="text-right">${fmt(row.old_taxable_amount)} → ${fmt(row.new_taxable_amount)}</td>
			<td class="text-right">${fmt(row.old_non_taxable_amount)} → ${fmt(row.new_non_taxable_amount)}</td>
			<td class="text-right">${fmt(row.old_vat_amount)} → ${fmt(row.new_vat_amount)}</td>
			<td class="text-right">${fmt(row.old_summary_grand_total)} → ${fmt(row.new_summary_grand_total)}</td>
			<td>${calculation}${row.would_change ? "" : `<br><small>${__("Review only; no summary change")}</small>`}</td>`;
	};

	const render_page = () => {
		const page_count = Math.max(Math.ceil(suggestions.length / page_size), 1);
		page = Math.min(Math.max(page, 0), page_count - 1);
		const start = page * page_size;
		const rows = suggestions.slice(start, start + page_size).map((row, offset) => {
			const index = start + offset;
			const disabled = can_select(row) ? "" : "disabled";
			const checked = selected.has(index) ? "checked" : "";
			return `<tr>${render_row(
				row,
				`<td><input type="checkbox" class="suggestion-select" data-index="${index}" ${checked} ${disabled}></td>`
			)}</tr>`;
		});
		$wrapper.find(".suggestion-rows").html(rows.join(""));
		$wrapper.find(".selected-count").text(
			__("{0} of {1} suggestion(s) selected", [selected.size, selectable_count])
		);
		$wrapper.find(".download-csv").prop("disabled", !selected.size);
		$wrapper.find(".page-count").text(
			__("Page {0} of {1}", [page + 1, page_count])
		);
		$wrapper.find(".previous-page").prop("disabled", page === 0);
		$wrapper.find(".next-page").prop("disabled", page >= page_count - 1);
		dialog.get_primary_btn().prop("disabled", selectable_count && !selected.size);
	};

	$wrapper.on("change", ".suggestion-select", function () {
		const index = Number(this.dataset.index);
		if (this.checked) {
			selected.add(index);
		} else {
			selected.delete(index);
		}
		render_page();
	});
	$wrapper.on("click", ".select-all", () => {
		suggestions.forEach((row, index) => {
			if (can_select(row)) selected.add(index);
		});
		render_page();
	});
	$wrapper.on("click", ".unselect-all", () => {
		selected.clear();
		render_page();
	});
	$wrapper.on("click", ".select-type", () => {
		const document_type = $wrapper.find(".document-type-filter").val();
		suggestions.forEach((row, index) => {
			if (can_select(row) && row.document_type === document_type) {
				selected.add(index);
			}
		});
		render_page();
	});
	$wrapper.on("click", ".unselect-type", () => {
		const document_type = $wrapper.find(".document-type-filter").val();
		suggestions.forEach((row, index) => {
			if (row.document_type === document_type) {
				selected.delete(index);
			}
		});
		render_page();
	});
	$wrapper.on("click", ".download-csv", () => {
		const selected_rows = [...selected]
			.sort((a, b) => a - b)
			.map((index) => suggestions[index])
			.filter(Boolean);
		if (!selected_rows.length) {
			frappe.msgprint(__("Select at least one row to download."));
			return;
		}
		frappe.call({
			method: "nepal_compliance.taxable_summary.download_taxable_summary_csv",
			args: {
				rows: JSON.stringify(selected_rows),
				from_date: preview.from_date,
				to_date: preview.to_date,
			},
			freeze: true,
			freeze_message: __("Preparing CSV..."),
			callback(r) {
				if (!r.message || !r.message.csv) {
					return;
				}
				const blob = new Blob(["\uFEFF" + r.message.csv], {
					type: "text/csv;charset=utf-8;",
				});
				const link = document.createElement("a");
				link.href = URL.createObjectURL(blob);
				link.download = r.message.filename || "taxable_summary.csv";
				document.body.appendChild(link);
				link.click();
				link.remove();
				URL.revokeObjectURL(link.href);
			},
		});
	});
	$wrapper.on("click", ".previous-page", () => {
		page -= 1;
		render_page();
	});
	$wrapper.on("click", ".next-page", () => {
		page += 1;
		render_page();
	});
	render_page();
	if (!selectable_count) {
		dialog.$wrapper.find(".modal-body").prepend(
			`<div class="alert alert-info">${__("No invoices in this range would change. Review any calculation warnings below.")}</div>`
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
			indicator:
				data.denied || data.failed || data.stale || data.calculation_warnings
					? "orange"
					: "green",
			message: __(
				"Updated {0} invoice(s) from {1} to {2}. Warnings: {3}; denied: {4}; stale: {5}; failed: {6}.",
				[
				data.updated,
				data.from_date,
				data.to_date,
				data.calculation_warnings || 0,
				data.denied || 0,
				data.stale || 0,
				data.failed || 0,
				]
			),
		});
	});
}

function run_apply(values, selected_invoices) {
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
			selected_invoices: JSON.stringify(selected_invoices),
			consider_is_non_taxable_item: values.consider_is_non_taxable_item || 0,
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
						"More than 500 invoices were selected. The update is running in the background in batches of 500. You will be notified when it finishes."
					)
				);
				return;
			}
			delete frappe._taxable_summary_apply_pending[request_id];
			frappe.msgprint(
				__("Updated {0} invoice(s). Warnings: {1}; denied: {2}; stale: {3}; failed: {4}.", [
					r.message.updated,
					r.message.calculation_warnings || 0,
					r.message.denied || 0,
					r.message.stale || 0,
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
				fieldname: "tds_help_button",
				fieldtype: "HTML",
				options: `<div class="text-right">
					<button type="button" class="btn btn-xs btn-default tds-base-help" title="${__(
						"About Audit TDS Bases"
					)}">?</button>
				</div>`,
			},
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
	dialog.fields_dict.tds_help_button.$wrapper
		.find(".tds-base-help")
		.on("click", show_tds_base_help);
}

function show_tds_base_help() {
	frappe.msgprint({
		title: __("About Audit TDS Bases"),
		message: `
			<p>${__(
				"Use this tool to check the transaction-currency and company-currency TDS base fields on submitted Purchase Invoices where TDS is enabled and the withholding category calculates TDS on the taxable amount."
			)}</p>
			<p><b>${__("Example")}</b></p>
			<p>${__(
				"An invoice has a taxable value of {0} and VAT of {1}. If its stored TDS base is incorrectly {2}, the audit suggests changing the TDS base to {0}.",
				[fmt(1000), fmt(130), fmt(1130)]
			)}</p>
			<p>${__(
				"Applying updates only the two TDS base fields and adds an audit comment. It does not recalculate historical TDS, change VAT rows, or alter General Ledger entries."
			)}</p>
		`,
		indicator: "blue",
	});
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
