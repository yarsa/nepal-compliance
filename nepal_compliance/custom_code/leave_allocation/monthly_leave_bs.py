import frappe
from frappe import _
from frappe.utils import getdate
from hrms.hr.doctype.leave_allocation.leave_allocation import create_leave_ledger_entry
from nepal_compliance.custom_code.leave_allocation.bs_leave_allocation import get_bs_today_date

NEPALI_MONTHLY_LEAVES = {
    "Annual Sick Leave": 0.5,
    "Annual Home Leave": 1.0,
}

def get_active_leave_allocations(leave_type_name, as_of_date):
    """Fetch all active leave allocations for a given leave type and date."""
    return frappe.get_all("Leave Allocation", filters={
        "leave_type": leave_type_name,
        "from_date": ["<=", as_of_date],
        "to_date": [">=", as_of_date],
        "docstatus": 1
    }, fields=["name", "employee"])

def update_allocation(doc, amount_to_add):
    """Update leave allocation with additional amount and create ledger entry."""
    doc.total_leaves_allocated += amount_to_add

    try:
        create_leave_ledger_entry(doc, {
            "employee": doc.employee,
            "leave_type": doc.leave_type,
            "from_date": doc.from_date,
            "to_date": doc.to_date,
            "leaves": amount_to_add,
            "transaction_name": doc.name,
            "transaction_type": "Leave Allocation",
            "doctype": "Leave Ledger Entry"
        })
        doc.save()
    except Exception as e:
        frappe.log_error(f"Failed to update allocation {doc.name}: {str(e)}")
        raise

@frappe.whitelist()
def allocate_monthly_leave_bs(force=False):
    """
    Allocate monthly leaves based on the Bikram Sambat (BS) calendar.
    
    Args:
        force (bool): Skip BS 1st-day check if True
    """
    bs_today = get_bs_today_date()

    user_roles = frappe.get_roles(frappe.session.user)
    if "HR User" not in user_roles and "HR Manager" not in user_roles:
        frappe.throw(_("You are not authorized to perform leave allocation."))

    if not force and bs_today.day != 1:
        frappe.msgprint(f"Today is not BS 1st Day: {bs_today}. Skipping allocation.")
        return

    allocation_key = f"bs_monthly_allocation_{bs_today.year}_{bs_today.month}"
    if frappe.cache().get_value(allocation_key):
        frappe.msgprint(_("Monthly allocation already completed for this BS month."))
        return

    ad_today = getdate()
    allocated_count = 0

    try:
        for leave_type_name, monthly_amount in NEPALI_MONTHLY_LEAVES.items():
            allocations = get_active_leave_allocations(leave_type_name, ad_today)
            for alloc in allocations:
                alloc_doc = frappe.get_doc("Leave Allocation", alloc.name)
                update_allocation(alloc_doc, monthly_amount)
                allocated_count += 1

                frappe.logger().info(
                    f"[Nepal Compliance] Added {monthly_amount} {leave_type_name} to {alloc_doc.employee} on BS {bs_today}"
                )

        frappe.cache().set_value(allocation_key, True)
        frappe.db.commit()
        frappe.msgprint(f"✅ Monthly BS Leave Allocation Completed. Updated {allocated_count} allocations.")

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Monthly BS leave allocation failed: {str(e)}")
        frappe.throw(_("Failed to complete monthly leave allocation. Please try again."))

def allocate_monthly_leave_bs_scheduled():
    """
    Scheduled task wrapper to call allocate_monthly_leave_bs() without user context.
    """
    try:
        # Run as system user
        frappe.set_user("Administrator")
        allocate_monthly_leave_bs(force=False)
        frappe.logger().info("[Nepal Compliance] Scheduled BS monthly leave allocation completed.")
    except Exception as e:
        frappe.log_error(f"[Nepal Compliance] Scheduled BS leave allocation failed: {str(e)}")
    finally:
        frappe.set_user("Guest")  # reset context
