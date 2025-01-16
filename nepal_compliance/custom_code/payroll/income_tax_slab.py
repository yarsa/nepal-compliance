import frappe
from frappe.utils import now_datetime 

def create_income_tax_slabs_for_all_companies():
    
    companies = frappe.get_all("Company", fields=["name", "default_currency"])
    
    for company in companies:
        fiscal_year = get_fiscal_year_for_company(company["name"])
        
        if fiscal_year:
            year_start_date = fiscal_year.year_start_date
            company_currency = company["default_currency"]
            nepali_date = fiscal_year.nepali_year_start_date
            create_income_tax_slab_for_company(company["name"], year_start_date, company_currency, nepali_date)
        else:
            frappe.msgprint(f"No fiscal year found for company: {company['name']}")

def get_fiscal_year_for_company(company_name):

    fiscal_years = frappe.get_all("Fiscal Year", filters={"company": company_name}, fields=["name", "year_start_date"])

    if fiscal_years:
        return frappe.get_doc("Fiscal Year", fiscal_years[0]["name"])

    return None

def create_income_tax_slab_for_company(company_name, year_start_date, company_currency, nepali_date):

    income_tax_slab_name = f"{company_name}-{nepali_date}"
    existing_slab = frappe.get_all("Income Tax Slab", filters={"name": income_tax_slab_name}, fields=["name"])
    
    if existing_slab:
        income_tax_slab = frappe.get_doc("Income Tax Slab", existing_slab[0]["name"])
    else:
        income_tax_slab = frappe.new_doc("Income Tax Slab")
        income_tax_slab.name = income_tax_slab_name
        income_tax_slab.company = company_name
        income_tax_slab.currency = company_currency
        income_tax_slab.effective_from = year_start_date
        income_tax_slab.nepali_date = nepali_date

    slabs = [{
        "from_amount": 0.00,  
        "to_amount": 1.00,  
        "percent_deduction": 0.00,  
        "condition": "" 
    }]

    for slab in slabs:
        existing_slab = next((s for s in income_tax_slab.slabs if 
                             s.from_amount == slab["from_amount"] and 
                             s.to_amount == slab["to_amount"] and
                             s.percent_deduction == slab["percent_deduction"] and
                             s.condition == slab["condition"]), None)

        if not existing_slab:
            income_tax_slab.append("slabs", {
                "from_amount": slab["from_amount"],
                "to_amount": slab["to_amount"],
                "percent_deduction": slab["percent_deduction"],
                "condition": slab["condition"],
            })
        else:
            frappe.msgprint(f"Slab already exists: {slab['from_amount']} - {slab['to_amount']}")

    income_tax_slab.save()
