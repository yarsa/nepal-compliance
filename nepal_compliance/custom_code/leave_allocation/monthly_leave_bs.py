import frappe
from frappe import _
from frappe.utils import getdate
from hrms.hr.doctype.leave_allocation.leave_allocation import create_leave_ledger_entry

NEPALI_MONTHLY_LEAVES = {
    "Annual Sick Leave": 0.5,
    "Annual Home Leave": 1.0,
}

def get_active_leave_allocations(leave_type_name, as_of_date):
    return frappe.get_all("Leave Allocation", filters={
        "leave_type": leave_type_name,
        "from_date": ["<=", as_of_date],
        "to_date": [">=", as_of_date],
        "docstatus": 1
    }, fields=["name", "employee"])

def update_allocation(doc, amount_to_add):
    doc.total_leaves_allocated += amount_to_add

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

@frappe.whitelist()
def allocate_monthly_leave_bs(bs_year, bs_month, force=False):
    user_roles = frappe.get_roles(frappe.session.user)
    if "HR User" not in user_roles and "HR Manager" not in user_roles:
        frappe.throw(_("You are not authorized to perform leave allocation."))
    bs_year = int(bs_year)
    bs_month = int(bs_month)

    last_bs_year = int(frappe.db.get_single_value("Nepal Compliance Settings", "bs_year") or 0)
    last_bs_month = int(frappe.db.get_single_value("Nepal Compliance Settings", "bs_month") or 0)

    if bs_year == last_bs_year and bs_month == last_bs_month:
        frappe.throw(_("🚫 Leave already allocated for BS {0}-{1}.").format(bs_year, bs_month))

    allocated_count = 0
    ad_today = getdate()

    try:
        for leave_type_name, monthly_amount in NEPALI_MONTHLY_LEAVES.items():
            allocations = get_active_leave_allocations(leave_type_name, ad_today)
            for alloc in allocations:
                alloc_doc = frappe.get_doc("Leave Allocation", alloc.name)
                update_allocation(alloc_doc, monthly_amount)
                allocated_count += 1

        frappe.db.set_single_value("Nepal Compliance Settings", "bs_year", bs_year)
        frappe.db.set_single_value("Nepal Compliance Settings", "bs_month", bs_month)

        frappe.db.commit()
        frappe.msgprint(f"✅ Leave Allocation Done for BS {bs_year}-{bs_month}. Total: {allocated_count}")

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"[Nepal Compliance] Allocation failed for BS {bs_year}-{bs_month}: {str(e)}")
        frappe.throw(_("Leave allocation failed. Check error logs."))
