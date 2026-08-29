// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.provide("nepal_compliance");

nepal_compliance.IRD_MONTH_PICKER_VERSION = "grid-1";

nepal_compliance.IRD_REGISTER_REPORTS = [
	"Sales Register IRD",
	"Purchase Register IRD",
	"Sales Return Register IRD",
	"Purchase Return Register IRD",
];

nepal_compliance.IRD_BS_MONTHS_EN = [
	"Baisakh",
	"Jestha",
	"Ashadh",
	"Shrawan",
	"Bhadra",
	"Ashwin",
	"Kartik",
	"Mangsir",
	"Poush",
	"Magh",
	"Falgun",
	"Chaitra",
];

nepal_compliance._ird_syncing = false;

nepal_compliance._is_bs_month_key = function (value) {
	const parts = String(value || "").split("-");
	if (parts.length !== 2) {
		return false;
	}
	const year = Number(parts[0]);
	const month = Number(parts[1]);
	return parts[0].length === 4 && year >= 2000 && month >= 1 && month <= 12;
};

nepal_compliance._bs_month_key = function (year, month) {
	return `${year}-${String(month).padStart(2, "0")}`;
};

nepal_compliance._add_bs_month = function (year, month, n) {
	const t = year * 12 + (month - 1) + n;
	return { year: Math.floor(t / 12), month: (t % 12) + 1 };
};

nepal_compliance._nepali_fy_start = function (year, month) {
	if (month >= 4) {
		return { year, month: 4 };
	}
	return { year: year - 1, month: 4 };
};

nepal_compliance._ad_iso = function (d) {
	if (!(d instanceof Date) || isNaN(d.getTime())) {
		return null;
	}
	return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`;
};

nepal_compliance.get_current_bs_year_month = function () {
	try {
		if (typeof NepaliDateLib !== "undefined" && NepaliDateLib.adToBs) {
			const bs = NepaliDateLib.adToBs(new Date());
			if (bs && bs.year) {
				const month = Number.isInteger(bs.monthIndex) ? bs.monthIndex + 1 : bs.month;
				if (month) {
					return { year: bs.year, month: month };
				}
			}
		}
		if (typeof NepaliFunctions !== "undefined" && NepaliFunctions.AD2BS) {
			const today = new Date();
			const ad = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
			const iso = NepaliFunctions.AD2BS(ad, false);
			if (iso) {
				const [year, month] = iso.split("-").map(Number);
				if (year && month) {
					return { year, month };
				}
			}
		}
	} catch (error) {
		console.error("Unable to determine the current BS month", error);
	}
	throw new Error("Nepali date conversion is unavailable.");
};

nepal_compliance.ird_bs_month_ad_range = function (value) {
	if (!value || typeof NepaliDateLib === "undefined" || !NepaliDateLib.bsToAd) {
		return null;
	}
	const parts = String(value).split("-").map(Number);
	if (parts.length < 2 || !parts[0] || !parts[1]) {
		return null;
	}
	const year = parts[0];
	const monthIndex = parts[1] - 1;
	const start = NepaliDateLib.bsToAd(year, monthIndex, 1);
	const days =
		(typeof NepaliDateLib.getDaysInMonth === "function" && NepaliDateLib.getDaysInMonth(year, monthIndex)) ||
		(typeof NepaliDateLib.getMonthLength === "function" && NepaliDateLib.getMonthLength(year, monthIndex));
	if (!days) {
		return null;
	}
	const end = NepaliDateLib.bsToAd(year, monthIndex, days);
	const from = nepal_compliance._ad_iso(start);
	const to = nepal_compliance._ad_iso(end);
	if (!from || !to) {
		return null;
	}
	return { from, to };
};

nepal_compliance.format_ird_bs_date = function (ad_value) {
	if (!ad_value || typeof NepaliFunctions === "undefined" || !NepaliFunctions.AD2BS) {
		return ad_value || "";
	}
	return NepaliFunctions.AD2BS(ad_value, true) || ad_value;
};

nepal_compliance.clear_ird_period_filters = function (report) {
	nepal_compliance._ird_fiscal_year_request_id =
		(nepal_compliance._ird_fiscal_year_request_id || 0) + 1;
	nepal_compliance.set_ird_month_filter(report, "");
	nepal_compliance.set_ird_filter_input(report, "fiscal_year", "");
};

nepal_compliance.bind_ird_bs_date_filter = function (report, fieldname) {
	const field = report.get_filter(fieldname);
	if (!field || !field.$input || field._ird_bs_date_bound) {
		return;
	}
	field._ird_bs_date_bound = true;
	const $input = field.$input;
	const original_get_value = field.get_value ? field.get_value.bind(field) : null;
	if (field.datepicker) {
		field.datepicker.destroy();
		field.datepicker = null;
	}
	field.$wrapper && field.$wrapper.find(".datepicker-icon").remove();
	$input.attr({ type: "text", readonly: true, autocomplete: "off" });

	field.get_value = function () {
		if ($input.is("[data-ird-ad-value]")) {
			return $input.attr("data-ird-ad-value") || "";
		}
		return original_get_value ? original_get_value() : field.value || "";
	};

	$input.on("change.irdBsDate", function () {
		if (nepal_compliance._ird_syncing) {
			return;
		}
		setTimeout(() => {
			const visible = $input.val();
			const previous_ad = $input.attr("data-ird-ad-value") || "";
			const had_period_filter =
				Boolean(report.get_filter_value("bs_month")) ||
				Boolean(report.get_filter_value("fiscal_year"));
			nepal_compliance.clear_ird_period_filters(report);
			if (!visible) {
				$input.attr("data-ird-ad-value", "");
				field.value = "";
				if (previous_ad || had_period_filter) {
					report.refresh(true);
				}
				return;
			}
			const selected_ad = $input.data("ad-value");
			const converted_ad =
				selected_ad ||
				(typeof NepaliFunctions !== "undefined" && NepaliFunctions.BS2AD
					? NepaliFunctions.BS2AD(visible)
					: "");
			if (converted_ad) {
				$input.attr("data-ird-ad-value", converted_ad);
				field.value = converted_ad;
				$input.val(nepal_compliance.format_ird_bs_date(converted_ad));
				if (converted_ad !== previous_ad || had_period_filter) {
					report.refresh(true);
				}
			}
		}, 0);
	});
};

nepal_compliance.set_ird_filter_input = function (report, fieldname, value) {
	const field = report.get_filter(fieldname);
	if (!field) {
		return;
	}
	const normalized = value || "";
	field.set_input(normalized);
	field.value = normalized;
	if (!field.$input) {
		return;
	}
	if (fieldname === "from_nepali_date" || fieldname === "to_nepali_date") {
		field.$input.attr("data-ird-ad-value", normalized);
		field.$input.val(nepal_compliance.format_ird_bs_date(normalized));
		return;
	}
	field.$input.val(normalized);
};

nepal_compliance.sync_ird_dates_from_month = function (report, month) {
	const range = nepal_compliance.ird_bs_month_ad_range(month);
	if (!range) {
		return;
	}
	nepal_compliance._ird_syncing = true;
	nepal_compliance.set_ird_filter_input(report, "from_nepali_date", range.from);
	nepal_compliance.set_ird_filter_input(report, "to_nepali_date", range.to);
	nepal_compliance._ird_syncing = false;
};

nepal_compliance.ird_month_bounds = function () {
	const current = nepal_compliance.get_current_bs_year_month();
	const default_value = nepal_compliance._bs_month_key(current.year, current.month);
	const fy_start = nepal_compliance._nepali_fy_start(current.year, current.month);
	const last_fy_start = nepal_compliance._add_bs_month(fy_start.year, fy_start.month, -12);
	const last_allowed = nepal_compliance._add_bs_month(current.year, current.month, 1);
	return {
		current,
		default_value,
		min_year: last_fy_start.year,
		max_year: last_allowed.year,
		min_key: nepal_compliance._bs_month_key(last_fy_start.year, last_fy_start.month),
		last_allowed_key: nepal_compliance._bs_month_key(last_allowed.year, last_allowed.month),
	};
};

nepal_compliance.format_ird_year_np = function (year) {
	if (typeof NepaliDateLib !== "undefined" && typeof NepaliDateLib.formatNumber === "function") {
		return NepaliDateLib.formatNumber(year, "ne");
	}
	return String(year);
};

nepal_compliance.format_ird_month_label = function (value) {
	if (!value) {
		return "";
	}
	const parts = String(value).split("-").map(Number);
	if (parts.length < 2 || !parts[0] || !parts[1]) {
		return value;
	}
	const names =
		(typeof NepaliDateLib !== "undefined" && NepaliDateLib.MONTH_NAMES_NE_BS) ||
		nepal_compliance.IRD_BS_MONTHS_EN;
	const np = names[parts[1] - 1] || value;
	return `${np} ${nepal_compliance.format_ird_year_np(parts[0])}`;
};

nepal_compliance.ird_month_entries = function () {
	if (typeof NepaliDateLib !== "undefined" && NepaliDateLib.BS_MONTHS_WITH_AD) {
		return NepaliDateLib.BS_MONTHS_WITH_AD;
	}
	return nepal_compliance.IRD_BS_MONTHS_EN.map((en) => {
		return { en, np: en, ad: "" };
	});
};

nepal_compliance.set_ird_month_filter = function (report, key) {
	const field = report.get_filter("bs_month");
	if (!field) {
		return;
	}
	field.value = key || "";
	if (field.$input) {
		field.$input.attr("data-bs-month-key", key || "");
		field.$input.val(key ? nepal_compliance.format_ird_month_label(key) : "");
	}
};

nepal_compliance.close_ird_month_picker = function () {
	const pop = document.querySelector(".ird-month-picker");
	if (pop) {
		pop.remove();
	}
	$(document).off("mousedown.irdMonthPicker");
	$(document).off("keydown.irdMonthPicker");
};

nepal_compliance.render_ird_month_picker = function (pop, report, view_year) {
	const bounds = nepal_compliance.ird_month_bounds();
	const current = bounds.current;
	const selected = report.get_filter_value("bs_month") || bounds.default_value;
	const entries = nepal_compliance.ird_month_entries();
	const year_np = nepal_compliance.format_ird_year_np(view_year);
	const months_html = entries
		.map((entry, index) => {
			const month = index + 1;
			const key = nepal_compliance._bs_month_key(view_year, month);
			const is_current = view_year === current.year && month === current.month;
			const is_selected = key === selected;
			const is_disabled = key < bounds.min_key || key > bounds.last_allowed_key;
			const classes = ["month"];
			if (is_current) {
				classes.push("current");
			}
			if (is_selected) {
				classes.push("selected");
			}
			if (is_disabled) {
				classes.push("disabled");
			}
			return `<button type="button" class="${classes.join(" ")}" data-month-key="${key}" ${
				is_disabled ? "disabled" : ""
			} aria-label="${entry.np} (${entry.ad})">
				<p class="np">${entry.np}</p>
				<p class="ad">${entry.ad}</p>
			</button>`;
		})
		.join("");

	pop.innerHTML = `<div class="calendar-wrapper" role="application" aria-label="Nepali Month Picker">
		<div class="picker-action-bar">
			<button type="button" class="back-button ird-month-back">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
				</svg>
				<span>${year_np} – महिना रोज्नुहोस्</span>
			</button>
		</div>
		<div class="content-scroll">
			<div class="month-grid">${months_html}</div>
		</div>
	</div>`;

	pop.querySelector(".ird-month-back").addEventListener("click", (e) => {
		e.preventDefault();
		e.stopPropagation();
		nepal_compliance.render_ird_year_picker(pop, report, view_year);
	});

	Array.from(pop.querySelectorAll(".month:not(.disabled)")).forEach((btn) => {
		btn.addEventListener("click", (e) => {
			e.preventDefault();
			e.stopPropagation();
			const key = btn.getAttribute("data-month-key");
			nepal_compliance.set_ird_month_filter(report, key);
			nepal_compliance.close_ird_month_picker();
			nepal_compliance.on_ird_month_change(report);
		});
	});
};

nepal_compliance.render_ird_year_picker = function (pop, report, view_year) {
	const bounds = nepal_compliance.ird_month_bounds();
	const selected = report.get_filter_value("bs_month") || bounds.default_value;
	const years = [];
	for (let y = bounds.min_year; y <= bounds.max_year; y++) {
		years.push(y);
	}
	const selected_year = Number(String(selected || "").split("-")[0]);
	const years_html = years
		.map((year) => {
			const classes = ["year"];
			if (year === bounds.current.year) {
				classes.push("current");
			}
			if (year === selected_year) {
				classes.push("selected");
			}
			return `<button type="button" class="${classes.join(" ")}" data-year="${year}">${nepal_compliance.format_ird_year_np(
				year
			)}</button>`;
		})
		.join("");

	pop.innerHTML = `<div class="calendar-wrapper" role="application" aria-label="Nepali Year Picker">
		<div class="picker-action-bar">
			<button type="button" class="back-button ird-year-back">
				<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
				</svg>
				<span>वर्ष रोज्नुहोस्</span>
			</button>
		</div>
		<div class="content-scroll">
			<div class="year-grid">${years_html}</div>
		</div>
	</div>`;

	pop.querySelector(".ird-year-back").addEventListener("click", (e) => {
		e.preventDefault();
		e.stopPropagation();
		nepal_compliance.render_ird_month_picker(pop, report, view_year);
	});

	Array.from(pop.querySelectorAll(".year")).forEach((btn) => {
		btn.addEventListener("click", (e) => {
			e.preventDefault();
			e.stopPropagation();
			const year = Number(btn.getAttribute("data-year"));
			nepal_compliance.render_ird_month_picker(pop, report, year);
		});
	});
};

nepal_compliance.open_ird_month_picker = function (report, $input) {
	if (document.querySelector(".ird-month-picker")) {
		nepal_compliance.close_ird_month_picker();
		return;
	}
	const selected = report.get_filter_value("bs_month") || nepal_compliance.ird_month_bounds().default_value;
	const parts = String(selected).split("-").map(Number);
	const view_year = parts[0] || nepal_compliance.get_current_bs_year_month().year;
	const rect = $input[0].getBoundingClientRect();
	const pop = document.createElement("div");
	pop.className = "nepali-calendar-popover ird-month-picker";
	Object.assign(pop.style, {
		position: "fixed",
		top: rect.bottom + 4 + "px",
		left: rect.left + "px",
		zIndex: 999999,
	});
	document.body.appendChild(pop);
	nepal_compliance.render_ird_month_picker(pop, report, view_year);

	const pop_rect = pop.getBoundingClientRect();
	if (pop_rect.bottom > window.innerHeight - 8) {
		pop.style.top = Math.max(8, rect.top - pop_rect.height - 4) + "px";
	}
	if (pop_rect.right > window.innerWidth - 8) {
		pop.style.left = Math.max(8, window.innerWidth - pop_rect.width - 8) + "px";
	}

	setTimeout(() => {
		$(document).on("mousedown.irdMonthPicker", (e) => {
			if (!pop.contains(e.target) && e.target !== $input[0] && !$(e.target).closest(".ird-month-icon").length) {
				nepal_compliance.close_ird_month_picker();
			}
		});
		$(document).on("keydown.irdMonthPicker", (e) => {
			if (e.key === "Escape") {
				nepal_compliance.close_ird_month_picker();
			}
		});
	}, 0);
};

nepal_compliance.bind_ird_month_picker = function (report, attempt) {
	const field = report.get_filter("bs_month");
	if (!field) {
		return;
	}
	if (!field.$input) {
		if ((attempt || 0) < 20) {
			setTimeout(() => nepal_compliance.bind_ird_month_picker(report, (attempt || 0) + 1), 50);
		}
		return;
	}
	if (field.$input.hasClass("ird-month-picker-initialized")) {
		return;
	}
	const $input = field.$input;
	$input.addClass("ird-month-picker-initialized");
	$input.attr({ readonly: true, autocomplete: "off", placeholder: __("महिना रोज्नुहोस्") });
	$input.css("cursor", "pointer");

	if (!$input.parent().hasClass("picker-wrap")) {
		$input.wrap('<div class="picker-wrap ird-month-input-wrap"></div>');
	}
	const wrap = $input.parent();
	if (!wrap.find(".ird-month-icon").length) {
		wrap.append('<i class="fa fa-calendar ird-month-icon nepali-calendar-icon"></i>');
	}

	const original_get_value = field.get_value ? field.get_value.bind(field) : null;
	field.get_value = function () {
		if ($input.is("[data-bs-month-key]")) {
			return $input.attr("data-bs-month-key") || "";
		}
		return original_get_value ? original_get_value() : field.value || "";
	};

	const current_key = field.value || $input.attr("data-bs-month-key") || "";
	if (nepal_compliance._is_bs_month_key(current_key)) {
		nepal_compliance.set_ird_month_filter(report, current_key);
	}

	const open = function (e) {
		if (e) {
			e.preventDefault();
			e.stopPropagation();
		}
		nepal_compliance.open_ird_month_picker(report, $input);
	};
	$input.on("mousedown", open);
	$input.on("keydown", function (e) {
		if (e.key === "Tab") {
			return;
		}
		if (e.key === "Escape") {
			nepal_compliance.close_ird_month_picker();
			return;
		}
		e.preventDefault();
		if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
			open(e);
		}
	});
	wrap.find(".ird-month-icon").on("mousedown", open);
};

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
		default: bounds.default_value,
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
	filters.push({ fieldtype: "Break" });
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
	if (fieldname === "invoice" && data) {
		const name = data.invoice_name;
		const doctype = data.invoice_doctype;
		if (name && doctype) {
			const href = frappe.utils.get_form_link(doctype, name);
			const label = frappe.utils.escape_html(value || name);
			return `<a class="underline" href="${href}" target="_blank" rel="noopener noreferrer">${label}</a>`;
		}
	}
	return default_formatter(value, row, column, data);
};

if (typeof frappe !== "undefined" && frappe.query_reports) {
	(nepal_compliance.IRD_REGISTER_REPORTS || []).forEach(function (name) {
		const settings = frappe.query_reports[name];
		if (settings && settings._ird_month_grid !== nepal_compliance.IRD_MONTH_PICKER_VERSION) {
			delete frappe.query_reports[name];
		}
	});
}
