// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.provide("nepal_compliance");

nepal_compliance.IRD_MONTH_PICKER_VERSION = "grid-6";

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
	return null;
};

nepal_compliance._warn_ird_date_unavailable = function () {
	if (nepal_compliance._ird_date_warning_shown) {
		return;
	}
	nepal_compliance._ird_date_warning_shown = true;
	frappe.msgprint({
		title: __("Nepali Date Unavailable"),
		indicator: "orange",
		message: __("The report is available, but Nepali date defaults could not be loaded. Select a fiscal year or reload after the date assets are available."),
	});
};

nepal_compliance._ird_bs_to_ad = function (year, month, day) {
	try {
		if (typeof NepaliDateLib !== "undefined" && NepaliDateLib.bsToAd) {
			return nepal_compliance._ad_iso(NepaliDateLib.bsToAd(year, month - 1, day));
		}
		if (typeof NepaliFunctions !== "undefined" && NepaliFunctions.BS2AD) {
			const value =
				typeof formatDate === "function" && typeof getUserDateFormat === "function"
					? formatDate(year, month, day, getUserDateFormat())
					: `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
			return NepaliFunctions.BS2AD(value);
		}
	} catch (error) {
		console.error("Unable to convert the BS date", error);
	}
	return null;
};

nepal_compliance.ird_bs_month_ad_range = function (value) {
	if (!value) {
		return null;
	}
	const parts = String(value).split("-").map(Number);
	if (parts.length < 2 || !parts[0] || !parts[1]) {
		return null;
	}
	const year = parts[0];
	const month = parts[1];
	const monthIndex = month - 1;
	let days = null;
	if (typeof NepaliDateLib !== "undefined") {
		days =
			(typeof NepaliDateLib.getDaysInMonth === "function" && NepaliDateLib.getDaysInMonth(year, monthIndex)) ||
			(typeof NepaliDateLib.getMonthLength === "function" && NepaliDateLib.getMonthLength(year, monthIndex));
	}
	const from = nepal_compliance._ird_bs_to_ad(year, month, 1);
	let to = days ? nepal_compliance._ird_bs_to_ad(year, month, days) : null;
	for (let day = 32; !to && day >= 28; day--) {
		to = nepal_compliance._ird_bs_to_ad(year, month, day);
	}
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
	if (!current) {
		return null;
	}
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
