import frappe
from frappe import _
from frappe.utils import getdate, flt
from datetime import date
from typing import Union, Optional

@frappe.whitelist()
def get_max_amount_eligible(employee: str, claim_date: Optional[Union[str, date]]) -> float:
    if not employee:
        return 0.0

    try:
        emp = frappe.get_doc("Employee", employee)
    except frappe.DoesNotExistError:
        return 0.0

    if not emp.date_of_joining:
        return 0.0

    base_salary = flt(emp.revised_salary) if getattr(emp, 'revised_salary', None) else flt(emp.ctc) #revised salary or ctc
    if not base_salary:
        return 0.0

    # Fetch the latest active Salary Structure Assignment as of the claim date
    # and use its `base` (per-employee override) as the eligibility floor.
    # Get active salary structure assignment  
    salary_structure_assignments = frappe.db.get_all(  
        "Salary Structure Assignment",  
        filters={  
            "employee": employee,  
            "docstatus": 1,  
            "from_date": ["<=", claim_date]  
        },  
        fields=["salary_structure", "from_date", "base"],  
        order_by="from_date desc",  
        limit=1  
    )  
      
    if not salary_structure_assignments:  
        return 0.0
        
    base_salary_sal_str = flt(salary_structure_assignments[0].base)
    
    doj = getdate(emp.date_of_joining)
    claim_dt = getdate(claim_date) if claim_date else date.today()
    from dateutil.relativedelta import relativedelta

    rd = relativedelta(claim_dt, doj)
    months_worked = rd.years * 12 + rd.months

    if months_worked < 0:
        months_worked = 0

    if months_worked >= 12:
        return flt(max(base_salary * 0.6, base_salary_sal_str))
    else:
        per_month = flt(max((base_salary * 0.6), base_salary_sal_str) / 12.0)
        return flt(per_month * months_worked)
