frappe.ui.form.on('Holiday List', {
    refresh: function(frm) {
        updateAllNepaliDates(frm);
        setTimeout(initNepaliPicker, 500);
    },
    get_weekly_off_dates: function(frm) {
        frm.call('get_weekly_off_dates').then(() => updateAllNepaliDates(frm));
    }
});

frappe.ui.form.on('Holiday', {

    holiday_date: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.holiday_date) {
            frappe.model.set_value(cdt, cdn, 'nepali_date_holiday',
                NepaliFunctions.AD2BS(row.holiday_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
        }
    },

    nepali_date_holiday: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.nepali_date_holiday) {
            frappe.model.set_value(cdt, cdn, 'holiday_date',
                NepaliFunctions.BS2AD(row.nepali_date_holiday, "YYYY-MM-DD", "YYYY-MM-DD"));
        }
    },

    holidays_add: function(frm, cdt, cdn) {
        updateAllNepaliDates(frm);
        setTimeout(initNepaliPicker, 500);
    },

    form_render: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let grid_row = frm.fields_dict.holidays_sections.grid.grid_rows_by_docname[cdn];

        if (grid_row?.grid_form) {
            let field = grid_row.grid_form.fields_dict['nepali_date_holiday'];
            if (field?.$input && !field.$input.data('has-nepali-datepicker')) {
                add_nepali_date_picker({
                    fields_dict: {
                        'nepali_date_holiday': { input: field.$input[0] }
                    },
                    doctype: cdt,
                    docname: cdn
                }, 'nepali_date_holiday', 'holiday_date');
                
                field.$input.data('has-nepali-datepicker', true);
            }
        }
        setTimeout(initNepaliPicker, 500);
    }
});

function updateAllNepaliDates(frm) {
    if (frm.doc.holidays?.length) {
        frm.doc.holidays.forEach(holiday => {
            if (holiday.holiday_date && !holiday.nepali_date_holiday) {
                frappe.model.set_value('Holiday', holiday.name, 'nepali_date_holiday',
                    NepaliFunctions.AD2BS(holiday.holiday_date.split(" ")[0], "YYYY-MM-DD", "YYYY-MM-DD"));
            }
        });
        frm.refresh_field('holidays');
    }
}
 
function initNepaliPicker() {
    $('input[data-fieldname="nepali_date_holiday"]:not(.ndp-initialized)').each(function() {
        let $input = $(this);
        if ($input.hasClass('ndp-initialized')) return;
        
        try {
            $input.addClass('ndp-initialized')
                .nepaliDatePicker({
                    ndpYear: true,
                    ndpMonth: true,
                    ndpYearCount: 100,
                    onChange: function(e) {
                        $input.val(e.bs).trigger('change');
                    }
                });

            let $parent = $input.parent().css('position', 'relative');
            $parent.find('.nepali-calendar-icon').remove();

            let $icon = $('<i>')
                .addClass('fa fa-calendar nepali-calendar-icon')
                .css({
                    'position': 'absolute',
                    'right': '10px',
                    'top': '50%',
                    'transform': 'translateY(-50%)',
                    'cursor': 'pointer',
                    'z-index': '1000',
                    'font-size': '16px',
                    'color': '#555'
                });

            $parent.append($icon);
            $input.css('padding-right', '30px');
 
            function showPicker() {
                if ($input.data('nepaliDatePicker')) {
                    setTimeout(() => $input.data('nepaliDatePicker').show(), 100);
                }
            }
            $input.off('click.ndp focus.ndp')
                .on('click.ndp focus.ndp', showPicker)
                .on('focus.ndp', function() {
                    if (!$input.data('had-focus')) {
                        $input.data('had-focus', true);
                        showPicker();
                    }
                });
            $icon.on('click.ndp', function(e) {
                e.stopPropagation();
                e.preventDefault();
                $input.focus();
                showPicker();
            });
        } catch (e) {
            console.error("Error initializing picker:", e);
        }
    });
}

$(document)
    .on('focus', 'input[data-fieldname="nepali_date_holiday"]:not(.ndp-initialized)', initNepaliPicker)
    .on('grid-row-render frappe.ui.Dialog:shown', () => setTimeout(initNepaliPicker, 500))
    .on('click', '.grid-row', () => setTimeout(initNepaliPicker, 500));