function setup_nepali_date_fixer({ listview, doctype, ad_field, bs_field, label }) {
    const ad_fields = Array.isArray(ad_field) ? ad_field : [ad_field];
    const bs_fields = Array.isArray(bs_field) ? bs_field : [bs_field];

    if (ad_fields.length !== bs_fields.length) {
        frappe.msgprint(__("Field mapping mismatch between AD and BS fields."));
        return;
    }

    async function fetchAllRecordsBatch() {
        let all_docs = [];
        let limit_start = 0;
        const batch_size = 500;

        while (true) {
            const res = await frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype,
                    fields: ["name", ...ad_fields, ...bs_fields],
                    limit_start: limit_start,
                    limit_page_length: batch_size,
                    order_by: 'modified desc'
                }
            });

            const docs = res.message || [];
            all_docs = all_docs.concat(docs);

            if (docs.length < batch_size) {
                break;
            }
            limit_start += batch_size;
        }
        return all_docs;
    }

    fetchAllRecordsBatch().then(docs => {
        const has_missing_nepali_date = docs.some(doc =>
            ad_fields.some((ad, i) => doc[ad] && !doc[bs_fields[i]])
        );

        if (!has_missing_nepali_date) {
            console.log(`[Nepali Date Fixer] No missing BS dates found for ${doctype}`);
            return;
        }

        listview.page.add_inner_button(__(label || 'Bulk Update Nepali Dates'), async function () {
            const records = docs.filter(doc =>
                ad_fields.some((ad, i) => doc[ad] && !doc[bs_fields[i]])
            );

            frappe.confirm(
                __("Fix {0} missing Nepali Dates for <b>{1}</b>?", [records.length, doctype]),
                () => {
                    frappe.show_progress(__('Updating...'), 0, records.length);
                    let completed = 0;
                    let failed = [];

                    const updateNext = () => {
                        if (completed >= records.length) {
                            frappe.hide_progress();
                            if (failed.length > 0) {
                                frappe.msgprint(__("Updated {0} records. {1} failed: {2}", [
                                    completed - failed.length,
                                    failed.length,
                                    failed.join(", ")
                                ]));
                            } else {
                                frappe.msgprint(__('Nepali Dates updated successfully.'));
                            }
                            listview.refresh();
                            return;
                        }

                        const doc = records[completed];
                        const updates = {};

                        ad_fields.forEach((ad, i) => {
                            const bs = bs_fields[i];
                            if (doc[ad] && !doc[bs]) {
                                updates[bs] = NepaliFunctions.AD2BS(doc[ad], "YYYY-MM-DD", "YYYY-MM-DD");
                            }
                        });

                        frappe.db.set_value(doctype, doc.name, updates)
                            .then(() => {
                                completed++;
                                frappe.show_progress(__('Updating...'), completed, records.length);
                                updateNext();
                            })
                            .catch(err => {
                                console.error(err);
                                failed.push(doc.name);
                                completed++;
                                frappe.show_progress(__('Updating...'), completed, records.length);
                                updateNext();
                            });
                    };
                    updateNext();
                }
            );
        });
    });
}

["Sales Invoice"].forEach(doctype => {
    frappe.listview_settings[doctype] = Object.assign(
        frappe.listview_settings[doctype] || {},
        {
            onload(listview) {
                setup_nepali_date_fixer({
                    listview,
                    doctype,
                    ad_field: "posting_date",
                    bs_field: "nepali_date",
                    label: "Bulk Update Nepali Dates"
                });
            }
        }
    );
});