import frappe
from frappe import _
from frappe.utils import getdate, flt
from datetime import date

@frappe.whitelist()
def get_max_amount_eligible(employee, claim_date):
    if not employee:
        return 0

    try:
        emp = frappe.get_doc("Employee", employee)
    except frappe.DoesNotExistError:
        return 0

    if not emp.date_of_joining:
        return 0

    base_salary = flt(emp.revised_salary) if getattr(emp, 'revised_salary', None) else flt(emp.ctc)

    if not base_salary:
        return 0

    doj = getdate(emp.date_of_joining)
    claim_dt = getdate(claim_date) if claim_date else date.today()
    from dateutil.relativedelta import relativedelta

    rd = relativedelta(claim_dt, doj)
    months_worked = rd.years * 12 + rd.months

    if months_worked < 0:
        months_worked = 0

    if months_worked >= 12:
        return flt(base_salary * 0.6)
    else:
        per_month = flt((base_salary * 0.6) / 12.0)
        return flt(per_month * months_worked)