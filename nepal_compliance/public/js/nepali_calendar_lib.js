(function (global, factory) {
  typeof exports === "object" && typeof module !== "undefined"
    ? factory(
        exports,
        require("react"),
        require("nepali-date"),
        require("react-dom/client"),
      )
    : typeof define === "function" && define.amd
      ? define(["exports", "react", "nepali-date", "react-dom/client"], factory)
      : ((global =
          typeof globalThis !== "undefined" ? globalThis : global || self),
        factory(
          (global.NepaliCalendarLib = {}),
          global.React,
          global.NepaliDateLib,
          global.ReactDOM,
        ));
})(this, function (exports, React, nepaliDate, client) {
  "use strict";

  function r(e) {
    var t,
      f,
      n = "";
    if ("string" == typeof e || "number" == typeof e) n += e;
    else if ("object" == typeof e)
      if (Array.isArray(e)) {
        var o = e.length;
        for (t = 0; t < o; t++)
          e[t] && (f = r(e[t])) && (n && (n += " "), (n += f));
      } else for (f in e) e[f] && (n && (n += " "), (n += f));
    return n;
  }
  function clsx() {
    for (var e, t, f = 0, n = "", o = arguments.length; f < o; f++)
      (e = arguments[f]) && (t = r(e)) && (n && (n += " "), (n += t));
    return n;
  }

  const MONTH_START_INDEX = 0;
  const MONTH_END_INDEX = 11;
  function NepaliCalendarView({ selectedDateAD, selectedDateBS, onSelect }) {
    const today = React.useMemo(() => new nepaliDate.NepaliDate(), []);
    const selectedNepaliDate = React.useMemo(() => {
      if (selectedDateBS) return nepaliDate.NepaliDate.fromBS(selectedDateBS);
      if (selectedDateAD) {
        const selectedAD = nepaliDate.NepaliDate.parse(
          selectedDateAD,
          "AD",
        ).toAD();
        if (selectedAD) return nepaliDate.NepaliDate.fromAD(selectedAD);
      }
      return null;
    }, [selectedDateBS, selectedDateAD]);
    const navigationDate =
      selectedNepaliDate !== null && selectedNepaliDate !== void 0
        ? selectedNepaliDate
        : today;
    const [currentYear, setCurrentYear] = React.useState(navigationDate.year);
    const [currentMonthIndex, setCurrentMonthIndex] = React.useState(
      navigationDate.monthIndex,
    );
    const [mode, setMode] = React.useState("day");
    // Create calendar for current year (only month requested is computed)
    const calendar = React.useMemo(
      () => new nepaliDate.NepaliCalendar(currentYear),
      [currentYear],
    );
    const monthData = React.useMemo(
      () => calendar.getMonth(currentMonthIndex),
      [calendar, currentMonthIndex],
    );
    const canGoPrev =
      currentYear > nepaliDate.NepaliCalendar.minYear ||
      currentMonthIndex > MONTH_START_INDEX;
    const canGoNext =
      currentYear < nepaliDate.NepaliCalendar.maxYear ||
      currentMonthIndex < MONTH_END_INDEX;
    const handlePrevMonth = React.useCallback(() => {
      if (!canGoPrev) return;
      let y = currentYear;
      let m = currentMonthIndex - 1;
      if (m < MONTH_START_INDEX) {
        m = MONTH_END_INDEX;
        y--;
      }
      setCurrentYear(y);
      setCurrentMonthIndex(m);
    }, [currentYear, currentMonthIndex, canGoPrev]);
    const handleNextMonth = React.useCallback(() => {
      if (!canGoNext) return;
      let y = currentYear;
      let m = currentMonthIndex + 1;
      if (m > MONTH_END_INDEX) {
        m = MONTH_START_INDEX;
        y++;
      }
      setCurrentYear(y);
      setCurrentMonthIndex(m);
    }, [currentYear, currentMonthIndex, canGoNext]);
    const handleYearSelect = React.useCallback((year) => {
      setCurrentYear(year);
      setMode("month");
    }, []);
    const handleMonthSelect = React.useCallback((month) => {
      setCurrentMonthIndex(month);
      setMode("day");
    }, []);
    const handleDateSelect = React.useCallback(
      (date) =>
        onSelect === null || onSelect === void 0 ? void 0 : onSelect(date),
      [onSelect],
    );
    const handleTodayClick = React.useCallback(() => {
      const today = new nepaliDate.NepaliDate();
      onSelect === null || onSelect === void 0 ? void 0 : onSelect(today);
      setCurrentYear(today.year);
      setCurrentMonthIndex(today.monthIndex);
      setMode("day");
    }, [today, onSelect]);
    const currentMonthStartADYear = React.useMemo(
      () => calendar.getMonthAdYear(currentMonthIndex),
      [calendar, currentMonthIndex],
    );
    return /*#__PURE__*/ React.createElement(
      "div",
      {
        className: "calendar-wrapper",
        role: "application",
        "aria-label": "Nepali Calendar",
      },
      mode === "year" &&
        /*#__PURE__*/ React.createElement(CalendarYears, {
          currentYear: currentYear,
          onSelect: handleYearSelect,
          onBack: () => setMode("day"),
        }),
      mode === "month" &&
        /*#__PURE__*/ React.createElement(CalendarMonths, {
          currentMonth: currentMonthIndex,
          currentYear: currentYear,
          onSelect: handleMonthSelect,
          onBack: () => setMode("year"),
        }),
      mode === "day" &&
        /*#__PURE__*/ React.createElement(CalendarDays, {
          selectedADString:
            selectedNepaliDate === null || selectedNepaliDate === void 0
              ? void 0
              : selectedNepaliDate.format({
                  format: "YYYY-MM-DD",
                  calendar: "AD",
                }),
          weeks: chunkWeeks(monthData.days),
          today: today,
          monthAd: monthData.month.ad,
          monthNp: monthData.month.np,
          yearNp: nepaliDate.formatNumber(currentYear, "ne"),
          yearEn: currentYear,
          yearAd: currentMonthStartADYear,
          onClickPrev: handlePrevMonth,
          onClickNext: handleNextMonth,
          onClickYear: () => setMode("year"),
          onClickToday: handleTodayClick,
          onSelectDate: handleDateSelect,
          nextDisabled: !canGoNext,
          prevDisabled: !canGoPrev,
        }),
    );
  }
  function chunkWeeks(days) {
    const weeks = [];
    for (let i = 0; i < days.length; i += 7) weeks.push(days.slice(i, i + 7));
    return weeks;
  }
  function CalendarYears({ currentYear, onSelect, onBack }) {
    const years = React.useMemo(() => {
      return [...nepaliDate.NepaliCalendar.years].reverse();
    }, []);
    return /*#__PURE__*/ React.createElement(
      "div",
      null,
      /*#__PURE__*/ React.createElement(ActionBar, {
        title:
          "\u0935\u0930\u094D\u0937 \u0930\u094B\u091C\u094D\u0928\u0941\u0939\u094B\u0938\u094D",
        onBack: onBack,
      }),
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "content-scroll",
        },
        /*#__PURE__*/ React.createElement(
          "div",
          {
            className: "year-grid",
          },
          years.map((year) => {
            const isCurrent = year === currentYear;
            return /*#__PURE__*/ React.createElement(
              "button",
              {
                key: year,
                onClick: () => onSelect(year),
                type: "button",
                className: clsx("year", isCurrent && "current"),
                "aria-label": `Year ${year}`,
                "aria-current": isCurrent ? "date" : undefined,
              },
              nepaliDate.formatNumber(year, "ne"),
            );
          }),
        ),
      ),
    );
  }
  function CalendarMonths({ currentMonth, currentYear, onSelect, onBack }) {
    return /*#__PURE__*/ React.createElement(
      "div",
      null,
      /*#__PURE__*/ React.createElement(ActionBar, {
        title: `${nepaliDate.formatNumber(currentYear, "ne")} – महिना रोज्नुहोस्`,
        onBack: onBack,
      }),
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "content-scroll",
        },
        /*#__PURE__*/ React.createElement(
          "div",
          {
            className: "month-grid",
          },
          nepaliDate.BS_MONTHS_WITH_AD.map((entry, index) => {
            const isCurrent = index === currentMonth;
            return /*#__PURE__*/ React.createElement(
              "button",
              {
                key: index,
                onClick: () => onSelect(index),
                type: "button",
                className: clsx("month", isCurrent && "current"),
                "aria-label": `${entry.np} (${entry.ad})`,
                "aria-current": isCurrent ? "date" : undefined,
              },
              /*#__PURE__*/ React.createElement(
                "p",
                {
                  className: "np",
                },
                entry.np,
              ),
              /*#__PURE__*/ React.createElement(
                "p",
                {
                  className: "ad",
                },
                entry.ad,
              ),
            );
          }),
        ),
      ),
    );
  }
  function CalendarDays({
    onClickYear,
    nextDisabled,
    prevDisabled,
    onClickNext,
    onClickPrev,
    onSelectDate,
    monthAd,
    monthNp,
    yearNp,
    yearEn,
    yearAd,
    weeks,
    today,
    selectedADString,
    onClickToday,
  }) {
    return /*#__PURE__*/ React.createElement(
      "div",
      null,
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "days-header",
        },
        /*#__PURE__*/ React.createElement(
          "div",
          {
            className: "header-actions",
          },
          /*#__PURE__*/ React.createElement(
            "button",
            {
              type: "button",
              onClick: onClickPrev,
              disabled: prevDisabled,
              className: "month-button",
              "aria-label": "Previous month",
            },
            /*#__PURE__*/ React.createElement(
              "span",
              {
                className: "button-feedback",
              },
              /*#__PURE__*/ React.createElement(
                "svg",
                {
                  xmlns: "http://www.w3.org/2000/svg",
                  fill: "none",
                  viewBox: "0 0 24 24",
                  "strokeWidth": "1.5",
                  stroke: "currentColor",
                },
                /*#__PURE__*/ React.createElement("path", {
                  "stroke-linecap": "round",
                  "stroke-linejoin": "round",
                  d: "M15.75 19.5 8.25 12l7.5-7.5",
                }),
              ),
            ),
          ),
          /*#__PURE__*/ React.createElement(
            "div",
            {
              className: "year-wrapper",
            },
            /*#__PURE__*/ React.createElement(
              "button",
              {
                type: "button",
                onClick: onClickYear,
                className: "year-button",
                "aria-label": `Current year ${yearEn}, click to change`,
              },
              /*#__PURE__*/ React.createElement(
                "span",
                {
                  className: "bs",
                },
                yearNp,
              ),
              /*#__PURE__*/ React.createElement(
                "span",
                {
                  className: "ad",
                },
                "| ",
                yearAd,
              ),
              /*#__PURE__*/ React.createElement(
                "svg",
                {
                  xmlns: "http://www.w3.org/2000/svg",
                  fill: "none",
                  viewBox: "0 0 24 24",
                  strokeWidth: 1.5,
                  stroke: "currentColor",
                },
                /*#__PURE__*/ React.createElement("path", {
                  strokeLinecap: "round",
                  strokeLinejoin: "round",
                  d: "M8.25 15 12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9",
                }),
              ),
            ),
          ),
          /*#__PURE__*/ React.createElement(
            "button",
            {
              type: "button",
              onClick: onClickNext,
              disabled: nextDisabled,
              className: "month-button",
              "aria-label": "Next month",
            },
            /*#__PURE__*/ React.createElement(
              "span",
              {
                className: "button-feedback",
              },
              /*#__PURE__*/ React.createElement(
                "svg",
                {
                  xmlns: "http://www.w3.org/2000/svg",
                  fill: "none",
                  viewBox: "0 0 24 24",
                  "strokeWidth": "1.5",
                  stroke: "currentColor",
                },
                /*#__PURE__*/ React.createElement("path", {
                  "stroke-linecap": "round",
                  "stroke-linejoin": "round",
                  d: "m8.25 4.5 7.5 7.5-7.5 7.5",
                }),
              ),
            ),
          ),
        ),
        /*#__PURE__*/ React.createElement(
          "div",
          {
            className: "selected-month",
          },
          /*#__PURE__*/ React.createElement(
            "p",
            {
              className: "np",
            },
            monthNp,
          ),
          /*#__PURE__*/ React.createElement("p", null, monthAd),
        ),
      ),
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "week-days",
        },
        nepaliDate.WEEKDAY_SHORT_NE.map((day, index) =>
          /*#__PURE__*/ React.createElement(
            "span",
            {
              key: day,
              className: clsx("day", index === 6 && "holiday"),
              "aria-label": day,
            },
            day,
          ),
        ),
      ),
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "days-grid",
          role: "grid",
        },
        weeks.map((week, weekIndex) =>
          /*#__PURE__*/ React.createElement(
            React.Fragment,
            {
              key: `week-${weekIndex}`,
            },
            week.map((day, dayIndex) => {
              if (!day) {
                return /*#__PURE__*/ React.createElement("div", {
                  key: `day-${weekIndex}-${dayIndex}`,
                  className: "day empty",
                  role: "gridcell",
                });
              }
              const isToday =
                day.date.year === today.year &&
                day.date.monthIndex === today.monthIndex &&
                day.date.day === today.day;
              const isSelected =
                selectedADString ===
                day.date.format({
                  format: "YYYY-MM-DD",
                  calendar: "AD",
                });
              return /*#__PURE__*/ React.createElement(
                "button",
                {
                  key: `day-${weekIndex}-${dayIndex}`,
                  type: "button",
                  onClick: () =>
                    onSelectDate === null || onSelectDate === void 0
                      ? void 0
                      : onSelectDate(day.date),
                  className: clsx(
                    "day",
                    (dayIndex + 1) % 7 === 0 && "holiday",
                    isToday && "today",
                    isSelected && "selected",
                  ),
                  role: "gridcell",
                  "aria-label": `Nepali date ${day.date.format({
                    format: "YYYY-MM-DD",
                    calendar: "BS",
                  })}`,
                  "aria-current": isToday ? "date" : undefined,
                  "aria-selected": isSelected,
                },
                isToday &&
                  /*#__PURE__*/ React.createElement("span", {
                    className: "today-indicator",
                    "aria-hidden": "true",
                  }),
                day.np,
                /*#__PURE__*/ React.createElement(
                  "span",
                  {
                    className: "ad",
                    "aria-hidden": "true",
                  },
                  day.ad,
                ),
              );
            }),
          ),
        ),
      ),
      /*#__PURE__*/ React.createElement(
        "div",
        {
          className: "footer",
        },
        /*#__PURE__*/ React.createElement(
          "button",
          {
            onClick: onClickToday,
            type: "button",
            className: "today-button",
            "aria-label": "Go to today's date",
          },
          /*#__PURE__*/ React.createElement("span", null, "\u0906\u091C"),
        ),
      ),
    );
  }
  function ActionBar({ title, onBack }) {
    return /*#__PURE__*/ React.createElement(
      "div",
      {
        className: "picker-action-bar",
      },
      /*#__PURE__*/ React.createElement(
        "button",
        {
          onClick: onBack,
          type: "button",
          className: "back-button",
        },
        /*#__PURE__*/ React.createElement(
          "svg",
          {
            xmlns: "http://www.w3.org/2000/svg",
            fill: "none",
            viewBox: "0 0 24 24",
            "strokeWidth": "1.5",
            stroke: "currentColor",
          },
          /*#__PURE__*/ React.createElement("path", {
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            d: "M15.75 19.5 8.25 12l7.5-7.5",
          }),
        ),
        /*#__PURE__*/ React.createElement("span", null, title),
      ),
    );
  }

  const roots = new WeakMap();
  function render(el, props) {
    if (!el) return;
    let root = roots.get(el);
    if (!root) {
      root = client.createRoot(el);
      roots.set(el, root);
    }
    root.render(
      /*#__PURE__*/ React.createElement(
        NepaliCalendarView,
        Object.assign({}, props),
      ),
    );
  }

  function unmount(el) {
    if (!el) return;
    const root = roots.get(el);
    if (root) {
      root.unmount();
      roots.delete(el);
    }
  }

  exports.NepaliCalendarView = NepaliCalendarView;
  exports.render = render;
  exports.unmount = unmount;
});
