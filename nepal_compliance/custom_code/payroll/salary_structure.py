import frappe

def get_earnings(ssf_compliance=False):
    earnings = []
    earnings_components = [
        {"salary_component": "Basic Salary"},
        {"salary_component": "Other Allowance"},
        {"salary_component": "Overtime"},
        {"salary_component": "Gratuity"},
        {"salary_component": "Earning Adjustment"},
        {"salary_component": "Provident Fund Employer"}
    ]
    if ssf_compliance:
        earnings_components = [
            {"salary_component": "Basic Salary"},
            {"salary_component": "Other Allowance"},
            {"salary_component": "Employer's Contribution SSF"},
            {"salary_component": "Overtime"},
            {"salary_component": "Earning Adjustment"},
        ]
    
    for earning in earnings_components:
        formula = frappe.get_value("Salary Component", earning["salary_component"], "formula")
        amount_based_on_formula = frappe.get_value("Salary Component", earning["salary_component"], "amount_based_on_formula")
        abbr = frappe.get_value("Salary Component", earning["salary_component"], "salary_component_abbr")
        earnings.append(frappe.get_doc({
            "doctype": "Salary Detail",  
            "salary_component": earning["salary_component"],  
            "formula": formula, 
            "amount_based_on_formula": amount_based_on_formula,
            "abbr": abbr
        }))
    
    return earnings

def get_deductions(ssf_compliance=False, deduction_type="unmarried"):
    deductions = []
    deduction_components = []
    
    if ssf_compliance:
        if deduction_type == "unmarried":
            deduction_components = [
                "Income Tax Unmarried",
                "Employee's Contribution SSF",
                "Employer's Contribution SSF Deduction",
                "Insurance",
                "Leave and Late Deduction",
                "CIT", 
                "Deduction Adjustment"
        ]
        elif deduction_type == "married":
            deduction_components = [
                "Income Tax Married",
                "Employee's Contribution SSF",
                "Employer's Contribution SSF Deduction",
                "Insurance",
                "Leave and Late Deduction",
                "CIT", 
                "Deduction Adjustment"
        ]
    else:
        if deduction_type == "unmarried":
            deduction_components = [
                "Income Tax Unmarried",
                "Provident Fund Employee",
                "Insurance",
                "Leave and Late Deduction",
                "CIT", 
                "Gratuity Deduction",
                "Deduction Adjustment",
                "Provident Fund Employer Deduction"
            ]
        elif deduction_type == "married":
            deduction_components = [
                "Income Tax Married",
                "Provident Fund Employee",
                "Insurance",
                "Leave and Late Deduction",
                "CIT", 
                "Gratuity Deduction",
                "Deduction Adjustment",
                "Provident Fund Employer Deduction"
            ]

    for salary_component in deduction_components:
        formula = frappe.get_value("Salary Component", salary_component, "formula")
        amount_based_on_formula = frappe.get_value("Salary Component", salary_component, "amount_based_on_formula")
        abbr = frappe.get_value("Salary Component", salary_component, "salary_component_abbr")
        deductions.append(frappe.get_doc({
            "doctype": "Salary Detail", 
            "salary_component": salary_component,  
            "formula": formula, 
            "amount_based_on_formula": amount_based_on_formula,
            "abbr": abbr
        }))
    
    return deductions
    
@frappe.whitelist()
def create_salary_structures():
    companies = frappe.get_all("Company", fields=["name"])
    all_messages = []
    for company in companies:
        all_messages += create_salary_structure_for_company(company.name)
    return all_messages

def create_salary_structure_for_company(company_name):
    messages = []
    currency = frappe.get_value("Company", company_name, "default_currency") or "NPR"  

    salary_structure_unmarried_epf_name = f"Salary Structure Unmarried - EPF - {company_name}"
    salary_structure_married_epf_name = f"Salary Structure Married - EPF - {company_name}"
    salary_structure_unmarried_ssf_name = f"Salary Structure Unmarried - SSF - {company_name}"
    salary_structure_married_ssf_name = f"Salary Structure Married - SSF - {company_name}"

    def create_structure(name, ssf, deduction_type):
        if not frappe.db.exists("Salary Structure", {"company": company_name, "name": name}):
            doc = frappe.new_doc("Salary Structure")
            doc.name = name
            doc.company = company_name
            doc.currency = currency
            doc.payroll_frequency = "Monthly"
            doc.is_active = "Yes"
            doc.is_default = "No"

            for earning in get_earnings(ssf_compliance=ssf):
                doc.append("earnings", earning)
            for deduction in get_deductions(ssf_compliance=ssf, deduction_type=deduction_type):
                doc.append("deductions", deduction)

            doc.insert()
            messages.append(f"✔️ Salary Structure '{name}' created for company: {company_name}")
        else:
            messages.append(f"⚠️ Salary Structure '{name}' already exists for company: {company_name}")

    create_structure(f"Salary Structure Unmarried - EPF - {company_name}", ssf=False, deduction_type="unmarried")
    create_structure(f"Salary Structure Married - EPF - {company_name}", ssf=False, deduction_type="married")
    create_structure(f"Salary Structure Unmarried - SSF - {company_name}", ssf=True, deduction_type="unmarried")
    create_structure(f"Salary Structure Married - SSF - {company_name}", ssf=True, deduction_type="married")

    return messages

def assign_salary_structures_to_employees():
    companies = frappe.get_all("Company", fields=["name", "custom_type_of_company"])
    for company in companies:
        employees = frappe.get_all("Employee", filters={"company": company.name}, fields=["name", "marital_status"])
        for employee in employees:
            if company.custom_type_of_company == "SSF":
                if employee.marital_status == "Single":
                    salary_structure_name = f"Salary Structure Unmarried - SSF - {company.name}"
                elif employee.marital_status == "Married":
                    salary_structure_name = f"Salary Structure Married - SSF - {company.name}"
            elif company.custom_type_of_company == "EPF":
                if employee.marital_status == "Single":
                    salary_structure_name = f"Salary Structure Unmarried - EPF - {company.name}"
                elif employee.marital_status == "Married":
                    salary_structure_name = f"Salary Structure Married - EPF - {company.name}"

            if frappe.db.exists("Salary Structure", salary_structure_name):
                frappe.db.set_value("Employee", employee.name, "salary_structure", salary_structure_name)
            else:
                frappe.msgprint(f"Salary Structure '{salary_structure_name}' does not exist for company: {company.name}")
