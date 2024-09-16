import frappe

@frappe.whitelist()
def create_salary_component():
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Basic Salary"
    doc.salary_component_abbr = "BASIC"
    doc.type = "Earning"
    doc.description = "Basic salary component"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.condition = ""
    ctc_records = frappe.get_all('Employee', fields=['ctc'])
    ctc = ctc_records[0].ctc if ctc_records else 0 
    if doc.amount_based_on_formula == 1:
        doc.formula = ctc * 0.083
    # doc.amount = 50000
    doc.s_flexible_benefits = 0
    doc.insert()
    frappe.db.commit()  
