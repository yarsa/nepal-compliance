// Copyright (c) 2025, Yarsa Labs Pvt. Ltd. and contributors
// For license information, please see LICENSE at the root of this repository

frappe.ui.form.on('IRD Certification', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        frappe.call({
            method: 'nepal_compliance.setup.install.check_test_data_status',
            args: { docname: frm.doc.name },
            callback: function(r) {
                if (!r.message) return;

                const { masters_created, transactions_created } = r.message;

                if (!masters_created) {
                    frm.add_custom_button(__('Generate Test Masters'), function() {
                        frappe.call({
                            method: 'nepal_compliance.setup.install.generate_test_masters',
                            args: { docname: frm.doc.name },
                            freeze: true,
                            freeze_message: __('Generating Test Masters...'),
                            callback: function(res) {
                                if (!res.exc) frm.reload_doc();
                            }
                        });
                    });
                }

                else if (!transactions_created) {
                    frm.add_custom_button(__('Generate Test Data'), function() {
                        frappe.call({
                            method: 'nepal_compliance.setup.install.generate_test_transactions',
                            args: { docname: frm.doc.name },
                            freeze: true,
                            freeze_message: __('Generating Test Transactions...'),
                            callback: function(res) {
                                if (!res.exc) frm.reload_doc();
                            }
                        });
                    });
                }

                else if (masters_created && transactions_created) {
                    frm.add_custom_button(__('Clear Test Data'), function() {
                        frappe.confirm(
                            __('Are you sure you want to delete all test masters and transactions?'),
                            function() {
                                frappe.call({
                                    method: 'nepal_compliance.setup.uninstall.clear_test_data',
                                    args: { docname: frm.doc.name },
                                    freeze: true,
                                    freeze_message: __('Clearing Test Data...'),
                                    callback: function(res) {
                                        if (!res.exc) {
                                            frappe.msgprint(__('Test data cleared successfully.'));
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        );
                    }, __('Actions')).addClass('btn-danger');
                }
            }
        });
        const checklist = [
            "स्थायी लेखा नम्बरः",
            "अनूसूचि ३ अनुसारको निवेदन",
            "अनूसूचि २",
            "स्थायी लेखा नम्बर प्रमाणपत्रको प्रतिलिपी",
            "कम्पनी वा फर्म दर्ता प्रमाणपत्रको प्रतिलिपी",
            "कर चुक्ता प्रमाणपत्रको प्रतिलिपी",
            "Pen Drive मा सफ्टवेयरको आधिकारीक सेटअप फाइल",
            "Tax Invoice / Invoice",
            "बीजकको Reprint गरिएको प्रति",
            "VAT Sales Register / Sales Report",
            "Stock Report",
            "Credit / Debit Note प्रति",
            "रद्ध बीजकको प्रति",
            "रद्ध पछि Stock Report",
            "Audit Trial Report",
            "CBMS Test Server Materialized View Report",
            "अनूसूचि ७",
            "Data Backup व्यवस्था",
            "Data Edit/Delete व्यवस्था (screenshot सहित)",
            "User Manual",
            "System Architecture Design",
            "Software Provider को PAN र Tax Clearance",
            "Software बिक्री बिल प्रति",
            "पछिल्लो बिक्री विजक प्रति",
            "AnyDesk Number"
        ];

        const wrapper = frm.fields_dict.list_of_required_documents_for_ird_approval.$wrapper;
        wrapper.empty();

        frappe.db.get_list("File", {
            filters: {
                attached_to_doctype: "IRD Certification",
                attached_to_name: frm.doc.name
            },
            fields: ["name", "file_name", "file_url", "attached_to_field", "creation"],
            order_by: "creation desc"
        }).then(files => {
            const fileMap = {};
            (files || []).forEach(f => {
                if (f.attached_to_field && f.attached_to_field.startsWith("checklist_")) {
                    const idx = parseInt(f.attached_to_field.split("_")[1]);
                    if (!fileMap[idx]) fileMap[idx] = f;
                }
            });

            let html = `
                <div style="padding:4px;">
                    <table class="table table-bordered table-condensed" style="font-size:13px;">
                        <thead>
                            <tr>
                                <th style="width:40px;">#</th>
                                <th>Document Name</th>
                                <th style="width:200px;">File</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            checklist.forEach((label, i) => {
                const existingFile = fileMap[i];
                const fileCell = existingFile
                    ? `
                        <a href="${existingFile.file_url}" target="_blank" class="btn btn-xs btn-success">View</a>
                        <button class="btn btn-xs btn-warning reupload-btn" data-index="${i}" style="margin-left:5px;">Replace</button>
                    `
                    : `<button class="btn btn-xs btn-default upload-btn" data-index="${i}">Upload</button>`;

                html += `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${frappe.utils.escape_html(label)}</td>
                        <td id="file-cell-${i}" style="white-space:nowrap;">${fileCell}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                    <div style="margin-top:10px;">
                        <button class="btn btn-primary btn-sm" id="download_all_btn"> Download Files (ZIP)</button>
                        <button class="btn btn-primary btn-sm" id="combine_pdf_btn" style="margin-left:8px;"> Download Files (PDF)</button>
                    </div>
                </div>
            `;

            wrapper.html(html);

            function openUploader(idx, $cell) {
                new frappe.ui.FileUploader({
                    doctype: "IRD Certification",
                    docname: frm.doc.name,
                    folder: "Home/Attachments",
                    restrictions: {
                        max_file_size: 25 * 1024 * 1024,
                        allowed_file_types: [".pdf", ".jpg", ".jpeg", ".png"]
                    },
                    on_success(file) {
                        frappe.show_alert({ message: __("File uploaded successfully."), indicator: "green" });

                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "File",
                                name: file.name,
                                fieldname: { attached_to_field: `checklist_${idx}` }
                            },
                            callback: () => {
                                frappe.db.get_list("File", {
                                    filters: {
                                        attached_to_doctype: "IRD Certification",
                                        attached_to_name: frm.doc.name,
                                        attached_to_field: `checklist_${idx}`,
                                        name: ["!=", file.name]
                                    },
                                    fields: ["name"]
                                }).then(oldFiles => {
                                    oldFiles.forEach(f =>
                                        frappe.call({
                                            method: "frappe.client.delete",
                                            args: { doctype: "File", name: f.name },
                                            error: () => {
                                                console.error(`Failed to delete old file: ${f.name}`, r);
                                            }
                                        })
                                    );
                                });
                            }
                        });

                        const viewBtn = `<a href="${file.file_url}" target="_blank" class="btn btn-xs btn-success">View</a>`;
                        const replaceBtn = `<button class="btn btn-xs btn-warning reupload-btn" data-index="${idx}" style="margin-left:5px;">Replace</button>`;
                        $cell.html(viewBtn + replaceBtn);
                    }
                });
            }
            wrapper.on("click", ".upload-btn, .reupload-btn", function () {
            const idx = $(this).data("index");
            const $cell = wrapper.find(`#file-cell-${idx}`);
            openUploader(idx, $cell);
            });

            function triggerDownload(url) {
                frappe.show_alert({ message: __("Preparing your file..."), indicator: "blue" });
                fetch(url, { method: "GET", credentials: "include" })
                    .then(r => r.blob().then(blob => [r, blob]))
                    .then(([response, blob]) => {
                        const link = document.createElement("a");
                        const contentDisp = response.headers.get("Content-Disposition");
                        let filename = "download";
                        if (contentDisp && contentDisp.includes("filename=")) {
                            filename = contentDisp.split("filename=")[1].replace(/"/g, "");
                        }
                        const blobUrl = URL.createObjectURL(blob);
                        link.href = blobUrl;
                        link.download = filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(blobUrl);
                    })
                    .catch((error) => {
                        console.error("Download error:", error);
                        frappe.msgprint(__("Error downloading file. Please try again."));
                    })
            }

            wrapper.find("#download_all_btn").on("click", function () {
                const url = frappe.urllib.get_full_url(
                    `/api/method/nepal_compliance.nepal_compliance.doctype.ird_certification.ird_certification.download_all_ird_files_stream?docname=${encodeURIComponent(frm.doc.name)}`
                );
                triggerDownload(url);
            });

            wrapper.find("#combine_pdf_btn").on("click", function () {
                const url = frappe.urllib.get_full_url(
                    `/api/method/nepal_compliance.nepal_compliance.doctype.ird_certification.ird_certification.generate_combined_ird_pdf_stream?docname=${encodeURIComponent(frm.doc.name)}`
                );
                triggerDownload(url);
            });
        });
    }
});