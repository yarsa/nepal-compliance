// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.provide("nepal_compliance");

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
	if (!bounds) {
		nepal_compliance.close_ird_month_picker();
		nepal_compliance._warn_ird_date_unavailable();
		return;
	}
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
	if (!bounds) {
		nepal_compliance.close_ird_month_picker();
		nepal_compliance._warn_ird_date_unavailable();
		return;
	}
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
	const bounds = nepal_compliance.ird_month_bounds();
	if (!bounds) {
		nepal_compliance._warn_ird_date_unavailable();
		return;
	}
	const selected = report.get_filter_value("bs_month") || bounds.default_value;
	const parts = String(selected).split("-").map(Number);
	const view_year = parts[0] || bounds.current.year;
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

