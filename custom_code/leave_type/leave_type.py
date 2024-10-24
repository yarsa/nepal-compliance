import frappe 

def create_leave_type():
    
    #Home Leave 
    doc = frappe.new_doc("Leave Type")
    doc.leave_type_name = "Annual/Home Leave"
    doc.max_leave_allowed = "18"
    doc.applicable_after = "20"
    doc.max_continuous_days_allowed = ""
    doc.include_holiday = 1
    
    doc.is_earned_leave = 1
    doc.earned_leave_frequency = "Monthly"
    doc.allocate_on_day = "First Day"
    doc.rounding = "0.5"
    doc.save()

    #Sick Leave
    doc = frappe.new_doc("Leave Type")
    doc.leave_type_name = "Sick Leave Compliance"
    doc.max_leaves_allowed = "12"
    doc.applicable_after = "20"
    doc.max_continuous_days_allowed = "3"
    doc.is_carry_forward = 1
    doc.include_holiday = 1
    doc.maximum_carry_forwarded_leaves = "45"

    doc.allow_encashment = 1
    doc.max_encashable_leaves = "45"
    doc.earning_component = "Basic"
    doc.is_earned_leave = 1
    doc.earned_leave_frequency = "Monthly"
    doc.allocate_on_day = "Last Day"
    doc.rounding = "0.5"
    doc.save()


