frappe.ui.form.on('Bulk Salary Structure Assignment', {
    refresh(frm) {
        NepaliFormDatePicker.init(frm, 'nepali_date', 'from_date');
    }
});
frappe.ui.form.on('Employee Attendance Tool', {
    refresh(frm) {
        NepaliFormDatePicker.init(frm, 'nepali_date', 'date');
    }
});
const NepaliFormDatePicker = {
    init(frm, bsField, adField) {
        const $input = $(frm.fields_dict[bsField].input);

        if ($input.hasClass('nepali-picker-initialized')) return;

        $input.addClass('nepali-picker-initialized');
        this.wrapInputWithIcon($input);

        $input.nepaliDatePicker({
            ndpYear: true,
            ndpMonth: true,
            ndpYearCount: 10,
            ndpFormat: 'YYYY-MM-DD',
            onChange: (e) => {
                const bsDate = e.bs;
                $input.val(bsDate);
                frappe.model.set_value(frm.doctype, frm.docname, bsField, bsDate);

                try {
                    const adDate = NepaliFunctions.BS2AD(bsDate, 'YYYY-MM-DD', 'YYYY-MM-DD');
                    frappe.model.set_value(frm.doctype, frm.docname, adField, adDate + ' 00:00:00');
                } catch (err) {
                    console.error('BS to AD conversion error:', err);
                }
            }
        });
        $input.on('change', function () {
            const entered = $(this).val().trim();
            if (/^\d{4}-\d{2}-\d{2}$/.test(entered)) {
                try {
                    const adDate = NepaliFunctions.BS2AD(entered, 'YYYY-MM-DD', 'YYYY-MM-DD');
                    frappe.model.set_value(frm.doctype, frm.docname, adField, adDate + ' 00:00:00');
                } catch (err) {
                    console.error('Invalid manual BS date:', err);
                    $(this).val('');
                }
            } else {
                $(this).val('');
            }
        });
    },

    wrapInputWithIcon($input) {
        if (!$input.parent().hasClass('date-picker-wrapper')) {
            $input.wrap('<div class="date-picker-wrapper" style="position:relative;"></div>');
        }

        if (!$input.parent().find('.nepali-calendar-icon').length) {
            const $icon = $('<i class="fa fa-calendar nepali-calendar-icon"></i>').css({
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                cursor: 'pointer',
                'z-index': 1
            }).on('click', function (e) {
                e.stopPropagation();
                $input.focus().trigger('click');
                if ($input.data('nepaliDatePicker')) {
                    $input.data('nepaliDatePicker').show();
                }
            });

            $input.parent().append($icon);
            $input.css('padding-right', '30px');
        }
    }
};