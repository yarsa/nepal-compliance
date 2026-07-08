import frappe
from erpnext.accounts.utils import get_fiscal_year

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
    try:
        fy = get_fiscal_year(frappe.utils.today(), company=company_name, as_dict=True)
        return frappe.get_doc("Fiscal Year", fy.name) if fy else None
    except frappe.exceptions.ValidationError:
        return None

def create_income_tax_slab_for_company(company_name, year_start_date, company_currency, nepali_date):

    income_tax_slab_name = f"{company_name} - Income Tax Slab"
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

    # Nepal income tax slabs (single set, identical for married and unmarried).
    # condition is None on every slab so the brackets apply regardless of marital status.
    slabs = [{
        "from_amount": 0,
        "to_amount": 1000000,
        "percent_deduction": 1,
        "condition": None
    },
    {
        "from_amount": 1000001,
        "to_amount": 1500000,
        "percent_deduction": 10,
        "condition": None
    },
    {
        "from_amount": 1500001,
        "to_amount": 2500000,
        "percent_deduction": 20,
        "condition": None
    },
    {
        "from_amount": 2500001,
        "to_amount": 4000000,
        "percent_deduction": 27,
        "condition": None
    },
    {
        "from_amount": 4000001,
        "to_amount": 0,
        "percent_deduction": 29,
        "condition": None
    }
    ]

    income_tax_slab.set("slabs", [])
    for slab in slabs:
        income_tax_slab.append("slabs", {
            "from_amount": slab["from_amount"],
            "to_amount": slab["to_amount"],
            "percent_deduction": slab["percent_deduction"],
            "condition": slab["condition"],
        })

    income_tax_slab.save(ignore_permissions=True)
