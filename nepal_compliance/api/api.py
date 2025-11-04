import frappe
from frappe import _
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
        attendance_doc_name = None
        employee_check_in.insert()
        frappe.db.commit()
        if log_type in ['Check In', 'Check Out']:
            attendance_doc = frappe.new_doc("Attendance")
            attendance_doc.employee = employee
            attendance_doc.status = status
            attendance_doc.shift = shift
            attendance_doc.attendance_date = attendance_date
            attendance_doc.docstatus = 1
            attendance_doc.insert()
            frappe.db.commit()
            attendance_doc_name = attendance_doc.name
        if attendance_doc_name:
            employee_check_in.db_set("attendance", attendance_doc_name)
    except Exception as e:
        print( f" {e} ")