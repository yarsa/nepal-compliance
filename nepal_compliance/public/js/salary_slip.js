let savedComponents = null;
let isProcessing = false;
let isEndDateChange = false;
 
function captureCurrentState(frm) {
    const state = {
        earnings: [],
        deductions: []
    };
    
    try {
        if (frm.doc.earnings) {
            frm.doc.earnings.forEach(row => {
                state.earnings.push({
                    salary_component: row.salary_component,
                    amount: row.amount,
                    default_amount: row.default_amount,
                    additional_amount: row.additional_amount,
                    depends_on_payment_days: row.depends_on_payment_days,
                    parentfield: row.parentfield,
                    doctype: row.doctype,
                    parenttype: row.parenttype,
                    idx: row.idx
                });
            });
        }
        
        if (frm.doc.deductions) {
            frm.doc.deductions.forEach(row => {
                state.deductions.push({
                    salary_component: row.salary_component,
                    amount: row.amount,
                    default_amount: row.default_amount,
                    additional_amount: row.additional_amount,
                    depends_on_payment_days: row.depends_on_payment_days,
                    parentfield: row.parentfield,
                    doctype: row.doctype,
                    parenttype: row.parenttype,
                    idx: row.idx
                });
            });
        }
        
        return state;
    } catch (error) {
        return null;
    }
}
 
function restoreComponents(frm) {
    if (!savedComponents) return;
    
    frappe.after_ajax(() => {
        try {
            const currentEarnings = new Map(
                frm.doc.earnings.map(row => [row.salary_component, row])
            );
            const currentDeductions = new Map(
                frm.doc.deductions.map(row => [row.salary_component, row])
            );
            
            let restoredCount = 0;
            
            savedComponents.earnings.forEach(savedRow => {
                const existing = currentEarnings.get(savedRow.salary_component);
                if (!existing) {
                    const child = frm.add_child('earnings');
                    Object.assign(child, savedRow);
                    restoredCount++;
                } else {
                    existing.additional_amount = savedRow.additional_amount;
                    existing.amount = flt(existing.default_amount) + flt(existing.additional_amount);
                    restoredCount++;
                }
            });
            
            savedComponents.deductions.forEach(savedRow => {
                const existing = currentDeductions.get(savedRow.salary_component);
                if (!existing) {
                    const child = frm.add_child('deductions');
                    Object.assign(child, savedRow);
                    restoredCount++;
                } else {
                    existing.additional_amount = savedRow.additional_amount;
                    existing.amount = flt(existing.default_amount) + flt(existing.additional_amount);
                    restoredCount++;
                }
            });
            
            if (restoredCount > 0) {
                frm.refresh_field('earnings');
                frm.refresh_field('deductions');
                calculate_selected_earnings(frm);
            }
            
            if (!isEndDateChange) {
                savedComponents = null;
            }
        } catch (error) {
            frappe.show_alert({
                message: __('Error restoring components. Please refresh the page.'),
                indicator: 'red'
            });
        }
    });
}
 
const originalEndDateMethod = frappe.call;
frappe.call = function(opts) {
    if (opts.method === 'hrms.payroll.doctype.payroll_entry.payroll_entry.get_end_date' && !isProcessing) {
        isProcessing = true;
        isEndDateChange = true;
        try {
            if (frm) {
                savedComponents = captureCurrentState(frm);
            } else {
                console.log('No current form found for capture');
            }
            const originalSuccess = opts.callback;
            const originalError = opts.error;
            opts.callback = function(r) {
                try {
                    if (originalSuccess) {
                        originalSuccess(r);
                    }
                    if (savedComponents && frm) {
                        console.log('Starting restore process with:', {
                            hasEarnings: savedComponents.earnings?.length || 0,
                            hasDeductions: savedComponents.deductions?.length || 0,
                            currentEarnings: frm.doc.earnings?.length || 0,
                            currentDeductions: frm.doc.deductions?.length || 0
                        });
                        setTimeout(() => {
                            restoreComponents(frm);
                        }, 1000);
                    } else {
                        console.log('Restore skipped:', {
                            hasSavedComponents: !!savedComponents,
                            hasCurrentForm: !!frm
                        });
                    }
                } finally {
                    isProcessing = false;
                    isEndDateChange = false;
                }
            };
            opts.error = function(err) {
                try {
                    if (originalError) {
                        originalError(err);
                    }
                } finally {
                    isProcessing = false;
                    isEndDateChange = false;
                    savedComponents = null;
                }
            };
        } catch (error) {
            isProcessing = false;
            isEndDateChange = false;
            savedComponents = null;
        }
    }
    return originalEndDateMethod.apply(this, arguments);
};
 
let manualDateChange = false;
frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        frm.set_df_property('nepali_start_date', 'hidden', 1);
        frm.set_df_property('nepali_end_date', 'hidden', 1);
 
        if (!isEndDateChange) {
            calculate_selected_earnings(frm);
        }
    },
    employee: function(frm) {
        try {
            if (!frm.doc.employee || !frm.doc.__islocal) return;
            const setupSalaryStructure = () => {
                return new Promise((resolve) => {
                    frappe.call({
                        method: 'frappe.client.get_value',
                        args: {
                            doctype: 'Salary Structure Assignment',
                            filters: { employee: frm.doc.employee, docstatus: 1 },
                            fieldname: ['salary_structure']
                        },
                        callback: r => {
                            if (!r.message?.salary_structure) {
                                resolve();
                                return;
                            }
                            
                            frappe.call({
                                method: 'frappe.client.get',
                                args: {
                                    doctype: 'Salary Structure',
                                    name: r.message.salary_structure
                                },
                                callback: r => {
                                    if (!r.message) {
                                        resolve();
                                        return;
                                    }
                                    calculate_selected_earnings(frm);
                                    const currentTaxableSalary = frm.doc.taxable_salary || 0;
                                    const taxComponents = (r.message.deductions || [])
                                        .filter(c => ['Income Tax Unmarried', 'Income Tax Married'].includes(c.salary_component));
                                    const processComponents = async () => {
                                        for (const component of taxComponents) {
                                            const exists = frm.doc.deductions?.some(d =>
                                                d.salary_component === component.salary_component
                                            );
                                            if (!exists && component.formula) {
                                                await addTaxComponent(component, currentTaxableSalary);
                                            }
                                        }
                                    };
                                    processComponents().then(resolve);
                                }
                            });
                        }
                    });
                });
            };

            const addTaxComponent = (component, taxableSalary) => {
                return new Promise((resolve) => {
                    const child = frm.add_child('deductions');
                    child.salary_component = component.salary_component;
                    child.amount_based_on_formula = 1;
                    child.formula = component.formula;
                    
                    frappe.call({
                        method: 'nepal_compliance.utils.evaluate_tax_formula',
                        args: {
                            formula: component.formula,
                            taxable_salary: taxableSalary
                        },
                        callback: (result) => {
                            if (result.message !== undefined) {
                                frappe.model.set_value(child.doctype, child.name, 'taxable_salary', taxableSalary)
                                    .then(() => frappe.model.set_value(child.doctype, child.name, 'amount', result.message))
                                    .then(() => frm.refresh_field('deductions'))
                                    .then(resolve);
                            } else {
                                resolve();
                            }
                        }
                    });
                });
            };

            const processDateTriggers = async () => {
                if (frm.doc.start_date) {
                    await new Promise(resolve => {
                        frm.trigger('start_date');
                        setTimeout(resolve, 300); 
                    });
                }
                
                if (frm.doc.end_date) {
                    await new Promise(resolve => {
                        frm.trigger('end_date');
                        setTimeout(resolve, 300); 
                    });
                }
            };

            processDateTriggers()
                .then(() => setupSalaryStructure())
                .catch(error => {
                    frappe.msgprint(__('Error processing salary components'));
                });
    
        } catch (error) {
            frappe.msgprint(__('Error adding tax components'));
        }
    },
 
    start_date(frm) {
        if (frm.doc.start_date) {
            const nepaliStartDate = NepaliFunctions.AD2BS(frm.doc.start_date, "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, "nepali_start_date", nepaliStartDate);
            frm.refresh_field('nepali_start_date');
        }
    },
 
    end_date(frm) {
        if (frm.doc.end_date) {
            const nepaliEndDate = NepaliFunctions.AD2BS(frm.doc.end_date, "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, "nepali_end_date", nepaliEndDate);
            frm.refresh_field('nepali_end_date');
        }
    },
    nepali_start_date(frm) {
        if (frm.doc.nepali_start_date) {
            const startDate = NepaliFunctions.BS2AD(frm.doc.nepali_start_date, "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, "start_date", startDate);
            frm.refresh_field('start_date');
        }
    },
    nepali_end_date(frm) {
        if (frm.doc.nepali_end_date) {
            const endDate = NepaliFunctions.BS2AD(frm.doc.nepali_end_date, "YYYY-MM-DD", "YYYY-MM-DD");
            frappe.model.set_value(frm.doctype, frm.docname, "end_date", endDate);
            frm.refresh_field('end_date');
        }
    },
    validate: function(frm) {
        if (isEndDateChange && savedComponents) {
            restoreComponents(frm);
        }
    },

    before_save: function(frm) {
        if (!isEndDateChange) {
            savedComponents = null;
        }
    }
});
 
frappe.ui.form.on('Salary Detail', {
    amount: function(frm) {
        calculate_selected_earnings(frm);
    },
    salary_component: function(frm) {
        calculate_selected_earnings(frm);
    },
    earnings_remove: function(frm) {
        calculate_selected_earnings(frm);
    },
    deductions_remove: function(frm) {
        calculate_selected_earnings(frm);
    }
});
 
let calculationCounter = 0;
function calculate_selected_earnings(frm) {
    let total_selected_earnings = 0;
    let total_deductions = 0;
    
    const selected_components = [
        "Basic Salary", "Other Allowance", "Grade Amount", "Blog Allowance", "Earning Adjustment","Overtime", "Gratuity", 
        "Provident Fund Employer", "Employer's Contribution SSF", 
    ];
    
    const deduction_components = [
        "Provident Fund Employee", "Insurance", "Leave and Late Deduction", "CIT", "Previous Month Adjustment Deduction",
        "Gratuity Deduction", "Employee's Contribution SSF", "Employer's Contribution SSF Deduction",
        "Deduction Adjustment", "Provident Fund Employer Deduction"
    ];
    
    frm.doc.earnings.forEach(function(row) {
        if (selected_components.includes(row.salary_component)) {
            total_selected_earnings += flt(row.amount || 0);
        }
    });
    
    frm.doc.deductions.forEach(function(row) {
        if (deduction_components.includes(row.salary_component)) {
            total_deductions += flt(row.amount || 0);
        }
    });
    
    let taxable_salary = flt(total_selected_earnings) - flt(total_deductions);
    frm.set_value('taxable_salary', taxable_salary);
}
