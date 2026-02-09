import frappe
from frappe import _
from frappe.utils import getdate
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import LeavePolicyAssignment as BaseLeavePolicyAssignment
from hrms.hr.doctype.leave_allocation.leave_allocation import create_leave_ledger_entry
from typing import Optional, List, Union

class LeavePolicyAssignment(BaseLeavePolicyAssignment):

    def on_submit(self):
        super().on_submit()

        allocations = frappe.get_all("Leave Allocation", filters={
            "leave_policy_assignment": self.name,
            "docstatus": 1
        }, fields=["name", "leave_type", "total_leaves_allocated"])
        try:
            for alloc in allocations:
                leave_type = frappe.get_doc("Leave Type", alloc.leave_type)

                if not (leave_type.allocate_leave_on_start_of_bs_month and not leave_type.is_earned_leave):
                    continue
                monthly_amt = leave_type.bs_monthly_allocation_amount or 0
                max_allowed = leave_type.max_leaves_allowed or 0

                if monthly_amt <= 0 or max_allowed <= 0:
                    continue
                alloc_doc = frappe.get_doc("Leave Allocation", alloc.name)

                if alloc_doc.total_leaves_allocated > monthly_amt:
                    reduce_by = alloc_doc.total_leaves_allocated - monthly_amt

                    create_leave_ledger_entry(alloc_doc, {
                        "employee": alloc_doc.employee,
                        "leave_type": alloc_doc.leave_type,
                        "from_date": alloc_doc.from_date,
                        "to_date": alloc_doc.to_date,
                        "leaves": -reduce_by,
                        "transaction_name": alloc_doc.name,
                        "transaction_type": "Leave Allocation",
                        "doctype": "Leave Ledger Entry"
                        })

                    alloc_doc.db_set("total_leaves_allocated", monthly_amt, update_modified=False)
        except Exception as e:
            frappe.log_error(
                message=frappe.get_traceback(),
                title=f"LeavePolicyAssignment submit failed (LPA: {self.name})",
            )
            raise

def get_active_leave_allocations(leave_type_name, as_of_date):
    return frappe.get_all("Leave Allocation", filters={
        "leave_type": leave_type_name,
        "from_date": ["<=", as_of_date],
        "to_date": [">=", as_of_date],
        "docstatus": 1
    }, fields=["name", "employee"])


def update_allocation(doc, amount_to_add):
    leave_type_doc = frappe.get_doc("Leave Type", doc.leave_type)
    max_allowed = leave_type_doc.max_leaves_allowed or 0

    if max_allowed <= 0:
        frappe.msgprint(_("Skipping {0} allocation: max_leaves_allowed not set.").format(doc.leave_type))
        return False

    current_allocated = doc.total_leaves_allocated or 0

    if current_allocated >= max_allowed:
        frappe.msgprint(_("{0}: Max {1} days already allocated for {2}.").format(doc.leave_type, max_allowed, doc.employee))
        return False

    allowable_to_add = min(amount_to_add, max_allowed - current_allocated)
    if allowable_to_add <= 0:
        return False

    doc.total_leaves_allocated += allowable_to_add

    create_leave_ledger_entry(doc, {
        "employee": doc.employee,
        "leave_type": doc.leave_type,
        "from_date": doc.from_date,
        "to_date": doc.to_date,
        "leaves": allowable_to_add,
        "transaction_name": doc.name,
        "transaction_type": "Leave Allocation",
        "doctype": "Leave Ledger Entry"
    })

    doc.db_set("total_leaves_allocated", doc.total_leaves_allocated, update_modified=False)
    return True


@frappe.whitelist()
def get_bs_eligible_leave_types():

    if not frappe.has_permission("Leave Allocation", "read"):
        frappe.throw(_("You are not authorized to view leave allocation settings."))

    return frappe.get_all("Leave Type", filters={
        "allocate_leave_on_start_of_bs_month": 1
    }, fields=["name", "bs_monthly_allocation_amount"])


@frappe.whitelist()
# noqa: frappe-semgrep-rules.rules.security.missing-argument-type-hint
def allocate_monthly_leave_bs(bs_year: int, bs_month: int, leave_types: Optional[Union[str, List[str]]] = None, *, force: bool = False, silent: bool = False) -> dict:

    if isinstance(leave_types, str):
        import json
        leave_types = json.loads(leave_types)

    bs_year = int(bs_year)
    bs_month = int(bs_month)
    force = frappe.utils.cint(force)
    silent = frappe.utils.cint(silent)

    if not leave_types:
        return {"status": "skipped", "message": "No leave type provided"}

    last_bs_year = int(frappe.db.get_single_value("Nepal Compliance Settings", "bs_year") or 0)
    last_bs_month = int(frappe.db.get_single_value("Nepal Compliance Settings", "bs_month") or 0)

    already_done = (
        last_bs_year == bs_year
        and last_bs_month == bs_month
        )

    if already_done and not force and silent:
        frappe.logger().info(f"[BS] Skip: Allocation already done for {bs_year}-{bs_month}")
        return {"status": "skipped", "message": "Already allocated"}

    if already_done and not force and not silent:
        frappe.throw(_("Leave already allocated for BS {0}-{1}.").format(bs_year, bs_month))
    allocated_count = 0
    ad_today = getdate()

    try:
        for leave_type_name in leave_types:
            leave_type_doc = frappe.get_doc("Leave Type", leave_type_name)

            if not leave_type_doc.allocate_leave_on_start_of_bs_month:
                continue

            monthly_amount = leave_type_doc.bs_monthly_allocation_amount or 0
            if monthly_amount <= 0:
                continue

            allocations = get_active_leave_allocations(leave_type_name, ad_today)

            for alloc in allocations:
                alloc_doc = frappe.get_doc("Leave Allocation", alloc.name)
                if update_allocation(alloc_doc, monthly_amount):
                    allocated_count += 1

        frappe.db.set_single_value("Nepal Compliance Settings", "bs_year", bs_year)
        frappe.db.set_single_value("Nepal Compliance Settings", "bs_month", bs_month)
        frappe.db.commit()

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(str(e), "Leave Allocation Failure")
        if not silent:
            frappe.throw(_("An error occurred during leave allocation."))
        return {"status": "error", "error": str(e)}

    if not silent:
        frappe.msgprint(_("Leave Allocation for BS {0}-{1}. Total Allocations: {2}").format(bs_year, bs_month, allocated_count))

    return {"status": "success", "count": allocated_count}