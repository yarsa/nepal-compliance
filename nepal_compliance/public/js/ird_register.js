nepal_compliance.ird_fiscal_year_filter = function () {
	return {
		fieldname: "fiscal_year",
		label: __("आर्थिक वर्ष"),
		fieldtype: "Link",
		options: "Fiscal Year",
		default: frappe.defaults.get_user_default("fiscal_year") || (frappe.sys_defaults && frappe.sys_defaults.fiscal_year),
		on_change: function (report) {
			nepal_compliance.on_ird_fiscal_year_change(report);
		},
	};
};

nepal_compliance.ird_bs_month_filter = function () {
	const bounds = nepal_compliance.ird_month_bounds();
	return {
		fieldname: "bs_month",
		label: __("महिना"),
		fieldtype: "Data",
		default: bounds ? bounds.default_value : "",
	};
};

nepal_compliance.ird_from_to_filters = function () {
	return [
		{
			fieldname: "from_nepali_date",
			label: __("मिति देखि"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_nepali_date",
			label: __("मिति सम्म"),
			fieldtype: "Date",
		},
	];
};

nepal_compliance.ird_register_filters = function (opts) {
	opts = opts || {};
	const from_to = nepal_compliance.ird_from_to_filters();
	const filters = [
		{
			fieldname: "company",
			label: __("फर्म / कम्पनी"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("company"),
		},
		nepal_compliance.ird_fiscal_year_filter(),
		nepal_compliance.ird_bs_month_filter(),
		from_to[0],
		from_to[1],
	];
	if (opts.party) {
		filters.push({
			fieldname: opts.party.fieldname,
			label: opts.party.label,
			fieldtype: "Link",
			options: opts.party.options,
		});
	}
	if (opts.document) {
		filters.push({
			fieldname: opts.document.fieldname,
			label: opts.document.label,
			fieldtype: "Link",
			options: opts.document.options,
			get_query: opts.document.get_query,
		});
	}
	return filters;
};

nepal_compliance.ensure_ird_current_month = function (report) {
	const bounds = nepal_compliance.ird_month_bounds();
	if (!bounds) {
		nepal_compliance._warn_ird_date_unavailable();
		return "";
	}
	const field = report.get_filter("bs_month");
	if (!field) {
		return bounds.default_value;
	}
	field.df.default = bounds.default_value;
	const selected = field.get_value ? field.get_value() : field.value;
	const looks_like_key = nepal_compliance._is_bs_month_key(selected);
	const value = looks_like_key && selected !== bounds.default_value ? selected : bounds.default_value;
	nepal_compliance.set_ird_month_filter(report, value);
	return value;
};

nepal_compliance.on_ird_month_change = function (report) {
	if (nepal_compliance._ird_syncing) {
		return;
	}
	nepal_compliance._ird_fiscal_year_request_id =
		(nepal_compliance._ird_fiscal_year_request_id || 0) + 1;
	const month = report.get_filter_value("bs_month");
	if (month) {
		nepal_compliance.sync_ird_dates_from_month(report, month);
	}
	report.refresh(true);
};

nepal_compliance.on_ird_fiscal_year_change = function (report) {
	if (nepal_compliance._ird_syncing) {
		return;
	}
	const fy = report.get_filter_value("fiscal_year");
	const request_id = (nepal_compliance._ird_fiscal_year_request_id || 0) + 1;
	nepal_compliance._ird_fiscal_year_request_id = request_id;
	if (!fy) {
		report.refresh(true);
		return;
	}
	frappe.db.get_value("Fiscal Year", fy, ["year_start_date", "year_end_date"], (r) => {
		if (
			request_id !== nepal_compliance._ird_fiscal_year_request_id ||
			report.get_filter_value("fiscal_year") !== fy
		) {
			return;
		}
		if (!r || !r.year_start_date) {
			report.refresh(true);
			return;
		}
		nepal_compliance._ird_syncing = true;
		nepal_compliance.set_ird_month_filter(report, "");
		nepal_compliance.set_ird_filter_input(report, "from_nepali_date", r.year_start_date);
		nepal_compliance.set_ird_filter_input(report, "to_nepali_date", r.year_end_date);
		nepal_compliance._ird_syncing = false;
		report.refresh(true);
	});
};

nepal_compliance.setup_ird_register = function (report, download_method) {
	if (report && report.page && report.page.main) {
		report.page.main.addClass("ird-register-page");
	}
	nepal_compliance.bind_ird_month_picker(report);
	nepal_compliance.bind_ird_bs_date_filter(report, "from_nepali_date");
	nepal_compliance.bind_ird_bs_date_filter(report, "to_nepali_date");
	const has_explicit_dates =
		report.get_filter_value("from_nepali_date") || report.get_filter_value("to_nepali_date");
	if (has_explicit_dates) {
		nepal_compliance.set_ird_month_filter(report, "");
	} else {
		const month = nepal_compliance.ensure_ird_current_month(report);
		nepal_compliance.sync_ird_dates_from_month(report, month);
	}
	if (typeof DatePickerConfig !== "undefined" && DatePickerConfig.initializePickers) {
		DatePickerConfig.initializePickers(report);
	}
	if (!download_method) {
		return;
	}
	report.page.add_inner_button(__("Download IRD Format"), function () {
		const filters = report.get_filter_values(true);
		frappe.call({
			method: download_method,
			args: {
				filters: JSON.stringify(filters),
			},
			callback: function (r) {
				if (r.message) {
					window.open(r.message);
				} else {
					frappe.msgprint(__("No data found or export failed."));
				}
			},
		});
	});
};

nepal_compliance.ird_invoice_formatter = function (value, row, column, data, default_formatter) {
	const fieldname = column.fieldname || column.id;
	if (data && data.is_section) {
		if (fieldname === "invoice") {
			const label = frappe.utils.escape_html(value || "");
			return `<span style="font-weight:600">${label}</span>`;
		}
		return "";
	}
	if (fieldname === "invoice" && data) {
		const name = data.invoice_name;
		const doctype = data.invoice_doctype;
		if (name && doctype) {
			const href = frappe.utils.get_form_link(doctype, name);
			const label = frappe.utils.escape_html(value || name);
			return `<a class="underline" href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>`;
		}
	}
	if (fieldname === "bill_date" && data && cint(data.bill_month_mismatch)) {
		const formatted = default_formatter(value, row, column, data);
		const days = data.bill_posting_day_diff;
		const title =
			days == null
				? __("Bill date and posting date are in different BS months")
				: __("{0} day(s) between bill date and posting date (different BS months)", [days]);
		return `<span class="ird-bill-date-mismatch" title="${frappe.utils.escape_html(
			title
		)}">${formatted}</span>`;
	}
	return default_formatter(value, row, column, data);
};

nepal_compliance.destroy_prior_fy_purchase_table = function (report) {
	if (report._prior_fy_datatable && report._prior_fy_datatable.destroy) {
		report._prior_fy_datatable.destroy();
	}
	report._prior_fy_datatable = null;
	if (report.$prior_fy_section) {
		report.$prior_fy_section.remove();
		report.$prior_fy_section = null;
	}
};

nepal_compliance.patch_purchase_register_dual_tables = function (report) {
	if (report._prior_fy_prepare_patched) {
		return;
	}
	report._prior_fy_prepare_patched = true;
	const original = report.prepare_report_data.bind(report);
	report.prepare_report_data = function (data) {
		original(data);
		const rows = this.data || [];
		this._prior_fy_purchases = rows.filter((r) => r && r.is_prior_fy);
		this.data = rows.filter((r) => !(r && r.is_prior_fy));
	};
};

nepal_compliance.render_prior_fy_purchase_table = function (report) {
	nepal_compliance.destroy_prior_fy_purchase_table(report);

	if (report.$purchase_register_heading) {
		report.$purchase_register_heading.remove();
		report.$purchase_register_heading = null;
	}

	const prior = report._prior_fy_purchases || [];
	if (!report.$report || !report.$report.length) {
		return;
	}

	if (prior.length) {
		const $main_heading = $(`
			<div class="ird-purchase-register-heading">
				<strong>${__("Purchase Register")}</strong>
				<span class="text-muted"> (${__("खरिद खाता")})</span>
			</div>
		`);
		report.$report.before($main_heading);
		report.$purchase_register_heading = $main_heading;
	}

	if (!prior.length) {
		return;
	}

	const $section = $(`
		<div class="ird-prior-fy-section">
			<div class="ird-prior-fy-heading">
				<strong>${__("Prior Fiscal Year Purchases")}</strong>
				<span class="text-muted"> (${__("गत आर्थिक वर्षका खरिद")})</span>
			</div>
			<div class="ird-prior-fy-datatable"></div>
		</div>
	`);
	report.$report.after($section);
	report.$prior_fy_section = $section;

	const columns = (report.columns || []).filter((col) => !col.hidden);
	report._prior_fy_datatable = new DataTable($section.find(".ird-prior-fy-datatable")[0], {
		columns: columns,
		data: prior,
		inlineFilters: true,
		language: frappe.boot.lang,
		translations: frappe.utils.datatable.get_translations(),
		layout: "fixed",
		cellHeight: 33,
		direction: frappe.utils.is_rtl() ? "rtl" : "ltr",
		hooks: {
			columnTotal: frappe.utils.report_column_total,
		},
	});
};

if (typeof frappe !== "undefined" && frappe.query_reports) {
	(nepal_compliance.IRD_REGISTER_REPORTS || []).forEach(function (name) {
		const settings = frappe.query_reports[name];
		if (settings && settings._ird_month_grid !== nepal_compliance.IRD_MONTH_PICKER_VERSION) {
			delete frappe.query_reports[name];
		}
	});
}
