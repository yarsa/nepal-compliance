import frappe
from migration.api import create_income_tax_slab

@frappe.whitelist()
def create_salary_component():
    company = frappe.get_all("Company", fields=["name"])
    salary_component_names = []  # List to hold created component names
    
    # //Basic Salary
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
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.amount_based_on_formula = 1
    doc.formula = "ctc * 0.083"
    doc.formula_read_only = 1
    # doc.amount = 50000
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    # doc.save()
    doc.save()
   

    # Grade Amount
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Grade Amount"
    doc.salary_component_abbr = "GA"
    doc.type = "Earning"
    doc.description = "Grade Amount Free Field"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()
    # frappe.db.commit()

    #PF_Employee (Earning)
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "PF_Employee (Earning)"
    doc.salary_component_abbr = "PFE_E"
    doc.type = "Earning"
    doc.description = "PF Based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "BASIC * 0.1"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #PF_Employee (Deduction)

    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "PF_Employee (Deduction)"
    doc.salary_component_abbr = "PFE_D"
    doc.type = "Deduction"
    doc.description = "PF Based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "BASIC * 0.1"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)
    doc.save()   

    #PF_Employeer
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "PF_Employeer"
    doc.salary_component_abbr = "PF_Employeer"
    doc.type = "Deduction"
    doc.description = "PF Based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "BASIC * 0.1"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save() 

    #Gratuity
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Gratuity"
    doc.salary_component_abbr = "Gr"
    doc.type = "Earning"
    doc.description = "Graturity Earning Based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "BASIC * .0833"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save() 

    #Gratuity Deduction 
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Gratuity Deduction"
    doc.salary_component_abbr = "Gr_D"
    doc.type = "Deduction"
    doc.description = "Graduity Deduction Based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "BASIC * .0833"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save() 

    #Other Allowance 
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Other Allowance"
    doc.salary_component_abbr = "OA"
    doc.type = "Earning"
    doc.description = "Other Allowance based on Formula"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "ctc-BASIC"
    doc.formula_read_only = 1
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Leave and Late Deduction
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Leave and Late Deduction"
    doc.salary_component_abbr = "LLD"
    doc.type = "Deduction"
    doc.description = "Leave and Late Deduction Free Field"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

#Leave and Late Deduction
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Leave and Late Deduction"
    doc.salary_component_abbr = "LLD"
    doc.type = "Deduction"
    doc.description = "Leave and Late Deduction Free Field"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    # Income Tax Unmarried
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Income Tax (Unmarried)"
    doc.salary_component_abbr = "IT_U"
    doc.type = 'Deduction'
    doc.description = "Income Tax as per Nepal law for Unmarried"
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.fromula = "((((Tax Salary) * 12) * 0.01)/12) if ((Tax Salary) * 12) <=500000 else (((500000 * 0.01) + (((Tax Salary) * 12) - 500000) * 0.1)/12) if ((Tax Salary) * 12) <= 700000 else (((500000*0.01) + (200000*0.1) + (((Tax Salary)*12) - 700000) * 0.2)/12) if ((Tax Salary)*12) <= 1000000 else (((500000*0.01) + (200000*0.1) + (300000*0.2) + ((Tax Salary)*12 - 1000000) *0.3)/12) if ((Tax Salary)*12)<=2000000 else (((500000*0.01) + (200000*0.1) + (300000*0.2) + (1000000*0.3) + ((Tax Salary)*12 - 2000000)*0.36)/12) if ((Tax Salary)*12)<=5000000 else (((500000*0.01) + (200000*0.1) + (300000*0.2) + (1000000*0.3) + (3000000*0.36) + ((Tax Salary)*12 - 5000000)*0.39)/12) if ((Tax Salary)*12)>5000000 else -1"
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Income Tax Married
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Income Tax (Married)"
    doc.salary_component_abbr = "IT_M"
    doc.type = "Deduction"
    doc.description = "Income Tax as per Nepal Law Couple"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Overtime
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Overtime"
    doc.salary_component_abbr = "OT"
    doc.type = "Earning"
    doc.description = "Overtime Free Field"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Insurance Premium
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Insurance Premium"
    doc.salary_component_abbr = "IP"
    doc.type = "Deduction"
    doc.description = "Insurance Prmium Deduction free field"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Loan and Advance
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Laon and Advance"
    doc.salary_component_abbr = "L&A"
    doc.type = "Deduction"
    doc.descriotion = "Loan and Advance Adjustment free field"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #CIT Deduction
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "CIT Deduction"
    doc.salary_component_abbr = "CIT"
    doc.type = "Deduction"
    doc.description = "CIT Deduction"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()

    #Dearness Allowance
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Dearness Allowance"
    doc.salary_component_abbr = "DA"
    doc.type = "Earning"
    doc.description = "Dearness Allowance"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 0
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()
    
    #SSF 
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = "Social Security Fund"
    doc.salary_component_abbr = "SSF"
    doc.type = "Deduction"
    doc.description = "SSF as per Nepal Law"
    doc.depends_on_payment_days = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.append("accounts", {
        "company" : company,
        "account" : "Salary - Y"
    })
    doc.condition = ""
    doc.amount_based_on_formula = 1
    doc.formula = "Basic * 0.31"
    doc.s_flexible_benefits = 0
    salary_component_names.append(doc.salary_component)  # Add to list
    doc.save()


        
    return salary_component_names  # Return the list of created component names


def install():
    create_salary_component()
    create_income_tax_slab()
