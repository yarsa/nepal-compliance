'''
import frappe
from typing import List, Dict, Any, Optional

def create_base_doc(
    name: str,
    abbr: str,
    doc_type: str,
    description: str,
    company: str,
    formula: Optional[str] = None,
    amount_based_on_formula: bool = False
) -> frappe.Document:
    doc = frappe.new_doc("Salary Component")
    doc.salary_component = name
    doc.salary_component_abbr = abbr
    doc.type = doc_type
    doc.description = description
    doc.depends_on_payment_days = 0
    doc.is_tax_applicable = 0
    doc.deduction_full_tax_on_selected_payroll_date = 0
    doc.round_to_the_nearest_integer = 0
    doc.statistical_component = 0
    doc.do_not_include_in_total = 0
    doc.remove_if_zero_valued = 1
    doc.disabled = 0
    doc.condition = ""
    doc.s_flexible_benefits = 0
    
    doc.append("accounts", {
        "company": company,
        "account": "Salary - Y"
    })
    
    if formula:
        doc.amount_based_on_formula = 1
        doc.formula = formula
        doc.formula_read_only = 1
    else:
        doc.amount_based_on_formula = amount_based_on_formula
        
    return doc

def get_income_tax_formula(is_unmarried: bool = True) -> str:
    if not is_unmarried:
        return ""
        
    tax_formula = """((((taxable_salary) * 12) * 0.01)/12) if ((taxable_salary) * 12) <=500000 
    else (((500000 * 0.01) + (((taxable_salary) * 12) - 500000) * 0.1)/12) if ((taxable_salary) * 12) <= 700000 
    else (((500000*0.01) + (200000*0.1) + (((taxable_salary)*12) - 700000) * 0.2)/12) if ((taxable_salary)*12) <= 1000000 
    else (((500000*0.01) + (200000*0.1) + (300000*0.2) + ((taxable_salary)*12 - 1000000) *0.3)/12) if ((taxable_salary)*12)<=2000000 
    else (((500000*0.01) + (200000*0.1) + (300000*0.2) + (1000000*0.3) + ((taxable_salary)*12 - 2000000)*0.36)/12) if ((taxable_salary)*12)<=5000000 
    else (((500000*0.01) + (200000*0.1) + (300000*0.2) + (1000000*0.3) + (3000000*0.36) + ((taxable_salary)*12 - 5000000)*0.39)/12) if ((taxable_salary)*12)>5000000 
    else -1""".replace('\n', ' ').strip()
    return tax_formula

def get_salary_components_config() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Basic Salary",
            "abbr": "BASIC",
            "type": "Earning",
            "description": "Basic salary component",
            "formula": "revised_salary * 0.083"
        },
        {
            "name": "Grade Amount",
            "abbr": "GA",
            "type": "Earning",
            "description": "Grade Amount Free Field"
        },
        {
            "name": "PF_Employee (Earning)",
            "abbr": "PFE_E",
            "type": "Earning",
            "description": "PF Based on Formula",
            "formula": "BASIC * 0.1"
        },
        {
            "name": "PF_Employee (Deduction)",
            "abbr": "PFE_D",
            "type": "Deduction",
            "description": "PF Based on Formula",
            "formula": "BASIC * 0.1"
        },
        {
            "name": "PF_Employer",
            "abbr": "PF_Employer",
            "type": "Deduction",
            "description": "PF Based on Formula",
            "formula": "BASIC * 0.1"
        },
        {
            "name": "Gratuity",
            "abbr": "Gr",
            "type": "Earning",
            "description": "Graturity Earning Based on Formula",
            "formula": "BASIC * .0833"
        },
        {
            "name": "Gratuity Deduction",
            "abbr": "Gr_D",
            "type": "Deduction",
            "description": "Graduity Deduction Based on Formula",
            "formula": "BASIC * .0833"
        },
        {
            "name": "Other Allowance",
            "abbr": "OA",
            "type": "Earning",
            "description": "Other Allowance based on Formula",
            "formula": "revised_salary-BASIC"
        },
        {
            "name": "Leave and Late Deduction",
            "abbr": "LLD",
            "type": "Deduction",
            "description": "Leave and Late Deduction Free Field"
        },
        {
            "name": "Income Tax (Married)",
            "abbr": "IT_M",
            "type": "Deduction",
            "description": "Income Tax as per Nepal Law Couple"
        },
        {
            "name": "Overtime",
            "abbr": "OT",
            "type": "Earning",
            "description": "Overtime Free Field"
        },
        {
            "name": "Insurance Premium",
            "abbr": "IP",
            "type": "Deduction",
            "description": "Insurance Premium Deduction free field"
        },
        {
            "name": "Loan and Advance",
            "abbr": "L&A",
            "type": "Deduction",
            "description": "Loan and Advance Adjustment free field"
        },
        {
            "name": "CIT Deduction",
            "abbr": "CIT",
            "type": "Deduction",
            "description": "CIT Deduction"
        },
        {
            "name": "Dearness Allowance",
            "abbr": "DA",
            "type": "Earning",
            "description": "Dearness Allowance"
        },
        {
            "name": "Social Security Fund",
            "abbr": "SSF",
            "type": "Deduction",
            "description": "SSF as per Nepal Law",
            "formula": "Basic * 0.31"
        }
    ]

@frappe.whitelist()
def create_salary_component() -> List[str]:
    try:
        companies = frappe.get_all("Company", fields=["name"])
        if not companies:
            frappe.throw("No company records found")
            
        company = companies[0].name
        salary_component_names = []
        
        # Create regular components
        components_config = get_salary_components_config()
        for config in components_config:
            doc = create_base_doc(
                name=config["name"],
                abbr=config["abbr"],
                doc_type=config["type"],
                description=config["description"],
                company=company,
                formula=config.get("formula")
            )
            doc.save()
            salary_component_names.append(doc.salary_component)

        tax_doc = create_base_doc(
            name="Income Tax (Unmarried)",
            abbr="IT_U",
            doc_type="Deduction",
            description="Income Tax as per Nepal law for Unmarried",
            company=company,
            formula=get_income_tax_formula(is_unmarried=True),
            amount_based_on_formula=True
        )
        tax_doc.save()
        salary_component_names.append(tax_doc.salary_component)
        
        frappe.db.commit()
        return salary_component_names
        
    except Exception as e:
        frappe.log_error(f"Error creating salary components: {str(e)}")
        frappe.throw(f"Failed to create salary components: {str(e)}")
        
'''