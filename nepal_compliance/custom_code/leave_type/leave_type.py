import frappe

def check_if_leave_type_exists(leave_type_name):
    return frappe.db.exists("Leave Type", {"leave_type_name": leave_type_name})

def create_leave_type(leave_type_name, max_leaves_allowed, applicable_after, 
                     max_continuous_days_allowed=None, is_earned_leave=1,
                     earned_leave_frequency="Monthly", allocate_on_day="First Day",
                     rounding="0.5", is_carry_forward=0, include_holiday=1,
                     allow_encashment=0, maximum_carry_forwarded_leaves=None,
                     max_encashable_leaves=None, earning_component=None):

    doc = frappe.new_doc("Leave Type")
    doc.leave_type_name = leave_type_name
    doc.max_leaves_allowed = max_leaves_allowed
    doc.applicable_after = applicable_after
    doc.max_continuous_days_allowed = max_continuous_days_allowed
    doc.is_earned_leave = is_earned_leave
    doc.earned_leave_frequency = earned_leave_frequency
    doc.allocate_on_day = allocate_on_day
    doc.rounding = rounding
    doc.include_holiday = include_holiday
    doc.is_carry_forward = is_carry_forward

    if is_carry_forward:
        doc.maximum_carry_forwarded_leaves = maximum_carry_forwarded_leaves
    
    if allow_encashment:
        doc.allow_encashment = allow_encashment
        doc.max_encashable_leaves = max_encashable_leaves
    
    if earning_component:
        doc.earning_component = earning_component
    
    doc.save()
    return doc

def setup_default_leave_types():
    leave_types = [
        {
            # Home Leave
            "leave_type_name": "Annual Home Leave",
            "max_leaves_allowed": "18",
            "applicable_after": "20",
            "allocate_on_day": "First Day"
        },
        {
            # Sick Leave
            "leave_type_name": "Annual Sick Leave",
            "max_leaves_allowed": "12",
            "applicable_after": "20",
            "max_continuous_days_allowed": "3",
            "is_carry_forward": 1,
            "maximum_carry_forwarded_leaves": "45",
            "allow_encashment": 1,
            "max_encashable_leaves": "45",
            "earning_component": "Basic Salary",
            "allocate_on_day": "Last Day"
        }
    ]

    for leave_type in leave_types:
        if not check_if_leave_type_exists(leave_type["leave_type_name"]):
            create_leave_type(**leave_type)
            frappe.msgprint(f"Created new leave type: {leave_type['leave_type_name']}")
        else:
            frappe.msgprint(f"Leave type {leave_type['leave_type_name']} already exists, skipping creation")