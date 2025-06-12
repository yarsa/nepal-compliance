import frappe
from nepal_compliance.utils import evaluate_tax_formula
from frappe.utils import flt

def execute(doc, method):
    if doc.payroll_entry:
        update_tax_and_submit(doc)

def update_tax_and_submit(doc):
    selected_earning_components = [
        "Basic Salary", "Other Allowance", "Grade Amount", "Blog Allowance", "Earning Adjustment",
        "Overtime", "Gratuity", "Provident Fund Employer", "Employer's Contribution SSF"
    ]

    deduction_components = [
        "Provident Fund Employee", "Insurance", "Leave and Late Deduction", "CIT", "Previous Month Adjustment Deduction",
        "Gratuity Deduction", "Employee's Contribution SSF", "Employer's Contribution SSF Deduction",
        "Deduction Adjustment", "Provident Fund Employer Deduction"
    ]

    total_earnings = sum(flt(e.amount) for e in doc.earnings if e.salary_component in selected_earning_components)
    total_deductions = sum(flt(d.amount) for d in doc.deductions if d.salary_component in deduction_components)
    taxable_salary = flt(total_earnings) - flt(total_deductions)
    doc.taxable_salary = taxable_salary

    exists = any(d.salary_component in ["Income Tax Unmarried", "Income Tax Married"] for d in doc.deductions)
    if not exists:
        structure = frappe.get_value("Salary Structure Assignment", {
            "employee": doc.employee,
            "docstatus": 1
        }, "salary_structure")

        if structure:
            structure_doc = frappe.get_doc("Salary Structure", structure)
            tax_components = [d for d in structure_doc.deductions
                              if d.salary_component in ["Income Tax Unmarried", "Income Tax Married"]]
            for comp in tax_components:
                if comp.formula:
                    tax_amount = evaluate_tax_formula(comp.formula, taxable_salary)
                    doc.append("deductions", {
                        "salary_component": comp.salary_component,
                        "amount": tax_amount,
                        "formula": comp.formula,
                        "amount_based_on_formula": 1,
                        "taxable_salary": taxable_salary
                    })

    doc.save(ignore_permissions=True)

