import frappe # type: ignore
from frappe import _ # type: ignore
# import logging
# from typing import Dict 

@frappe.whitelist(allow_guest=False) 
def get_all_employees():
    employees = frappe.get_all('Employee', fields=['name', 'employee_name', 'department','designation', 'status'])
    return employees
    
# Biometric 
@frappe.whitelist(allow_guest=True) 
def attendance(employee, status, shift, attendance_date, log_type, datetime, late_entry=None, early_exit=None):
    try:
        employee_check_in = frappe.new_doc("Employee Checkin")
        employee_check_in.employee = employee
        employee_check_in.log_type = log_type
        employee_check_in.datetime = datetime
        employee_check_in.attendance = attendance.name
        employee_check_in.insert()
        frappe.db.commit()
    if log_type in ['Check In', 'Check Out']: 
        attendance = frappe.new_doc("Attendance")
        attendance.employee = employee
        attendance.status = status
        attendance.shift = shift
        attendance.attendance_date = attendance_date
        attendance.docstatus = 1
        attendance.insert()
        frappe.db.commit()
    except Exception as e:
        print( f" {e} ")


company = frappe.get_all("Company", fields=["name"])
@frappe.whitelist()
def create_income_tax_slab():
    doc = frappe.new_doc("Income Tax Slab")
    doc.name = "Ignore Slab Test"
    doc.disabled = 0
    doc.effective_from = "2025-07-16"
    doc.company = company
    doc.currency = "NPR"
    doc.standard_tax_exemption_amount = ""
    doc.allow_tax_exemption = 0
    doc.append("slabs", {
        "from_amount" : "Rs 0.00",
        "to_amount" : "Rs 1.00",
        "percent_deduction" : "0%",
        "condition" : ""
    })
    # doc.Docstatus = 1
    doc.save()
    doc.reload()
    doc.submit()
