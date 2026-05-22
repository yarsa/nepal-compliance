import frappe, traceback
from frappe import _
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from hrms.payroll.doctype.salary_slip.salary_slip import make_loan_repayment_entry
from frappe.utils import cint, flt
from typing import Optional
from frappe.model.document import Document

class CustomSalarySlip(SalarySlip):
    def on_submit(self):
        if self.net_pay < 0:
            frappe.msgprint(_("Warning: Submitted salary slip with negative Net Pay."))

        self.set_status()
        self.update_status(self.name)

        make_loan_repayment_entry(self)

        if not frappe.flags.via_payroll_entry and not frappe.flags.in_patch:
            email_salary_slip = cint(frappe.db.get_single_value("Payroll Settings", "email_salary_slip_to_employee"))
            if email_salary_slip:
                self.email_salary_slip()

        self.update_payment_status_for_gratuity_and_leave_encashment()

    def compute_taxable_earnings_for_year(self):
        """Wire up include_in_taxable_salary into the tax base.

        Components flagged with include_in_taxable_salary=1 are added to
        unclaimed_taxable_benefits and total_taxable_earnings so they flow
        into both CTC and the slab tax engine. Skipped when an active
        Employee Benefit Application exists for the period.
        """
        super().compute_taxable_earnings_for_year()

        payroll_period = getattr(self, "payroll_period", None)
        if payroll_period:
            payroll_period_name = getattr(payroll_period, "name", payroll_period)
            has_app = frappe.db.exists(
                "Employee Benefit Application",
                {
                    "employee": self.employee,
                    "payroll_period": payroll_period_name,
                    "docstatus": 1,
                },
            )
            if has_app:
                return

        candidate_components = {
             e.salary_component
             for e in self.earnings
             if e.is_tax_applicable and e.is_flexible_benefit and e.amount and e.salary_component
         }
        if not candidate_components:
            return

        included = {
            row.name
            for row in frappe.get_all(
                "Salary Component",
                filters={"name": ("in", list(candidate_components))},
                fields=["name", "include_in_taxable_salary"],
            )
            if cint(row.include_in_taxable_salary)
        }

        extra = 0.0
        for earning in self.earnings:
            if (
                earning.is_tax_applicable
                and earning.is_flexible_benefit
                and earning.salary_component in included
            ):
                extra += flt(earning.amount)

        if extra:
            self.unclaimed_taxable_benefits = flt(getattr(self, "unclaimed_taxable_benefits", 0)) + extra
            self.total_taxable_earnings = flt(getattr(self, "total_taxable_earnings", 0)) + extra
            self.total_taxable_earnings_without_full_tax_addl_components = (
                flt(getattr(self, "total_taxable_earnings_without_full_tax_addl_components", 0)) + extra
            )
    def get_taxable_earnings_for_prev_period(self, start_date, end_date, allow_tax_exemption=False):
        """Include prior-period flex-benefit earnings flagged with
        include_in_taxable_salary=1 in previous_taxable_earnings.

        Vanilla hrms's get_salary_slip_details filters previous-period
        earnings with is_flexible_benefit=0, so flex amounts paid in
        earlier slips of the same payroll period are invisible to the
        current slip's tax base. This means a festival paid in Asoj
        affects only the Asoj slip's tax; subsequent slips (Kartik
        onwards) see annual income without the festival and recompute
        tax against the pre-festival amount, clawing back the marginal
        tax that was correctly deducted in Asoj.

        This override adds prior-period flex-benefit earnings (filtered
        by include_in_taxable_salary=1 on the Salary Component) to the
        taxable_earnings figure returned by the parent. Combined with the
        compute_taxable_earnings_for_year override, the festival amount
        contributes to annual taxable across every slip in the period,
        not just the festival month.
        """
        taxable_earnings, exempted_amount = super().get_taxable_earnings_for_prev_period(
            start_date, end_date, allow_tax_exemption
        )

        # Find prior-period flex-benefit components that are flagged
        # for inclusion in taxable salary.
        flagged_components = frappe.db.sql_list("""
            SELECT name FROM `tabSalary Component`
            WHERE include_in_taxable_salary = 1
              AND is_flexible_benefit = 1
              AND is_tax_applicable = 1
        """)
        if not flagged_components:
            return taxable_earnings, exempted_amount

        flex_taxable = 0.0
        for component in flagged_components:
            flex_taxable += flt(self.get_salary_slip_details(
                start_date, end_date,
                parentfield="earnings",
                salary_component=component,
                is_tax_applicable=1,
                is_flexible_benefit=1,
            ))

        return taxable_earnings + flex_taxable, exempted_amount

from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from hrms.payroll.doctype.payroll_entry.payroll_entry import (
    show_payroll_submission_status
)
from hrms.payroll.doctype.salary_withholding.salary_withholding import link_bank_entry_in_salary_withholdings

class CustomPayrollEntry(PayrollEntry):
    @frappe.whitelist()
    def submit_salary_slips(self):
        self.check_permission("write")
        salary_slips = self.get_sal_slip_list(ss_status=0)
        
        if len(salary_slips) > 30 or frappe.flags.enqueue_payroll_entry:
            self.db_set("status", "Queued")
            frappe.enqueue(
                submit_salary_slips_for_employees,
                timeout=3000,
                payroll_entry=self,
                salary_slips=salary_slips,
                publish_progress=False,
                )
            frappe.msgprint(
                _("Salary Slip submission is queued. It may take a few minutes"),
                alert=True,
                indicator="blue",
                )
        else:
            self.submit_salary_slips_for_employees(salary_slips, publish_progress=False)

    def submit_salary_slips_for_employees(self, salary_slips, publish_progress=True):
        submitted = []
        unsubmitted = []
        frappe.flags.via_payroll_entry = True
        count = 0

        for entry in salary_slips:
            try:
                salary_slip = frappe.get_doc("Salary Slip", entry[0])
                salary_slip.submit()
                submitted.append(salary_slip)
            except Exception as e:
                frappe.log_error(
                    title=f"Failed to submit {entry[0]}",
                    message=traceback.format_exc()
                )
                unsubmitted.append(entry[0])

            count += 1
            if publish_progress:
                frappe.publish_progress(
                    count * 100 / len(salary_slips),
                    title=_("Submitting Salary Slips...")
                )

        if submitted:
            try:
                self.make_accrual_jv_entry(submitted)
                self.email_salary_slip(submitted)
                self.db_set({
                    "salary_slips_submitted": 1,
                    "status": "Submitted",
                    "error_message": ""
                })
            except Exception as e:
                frappe.log_error(
                    title="Error in accrual/email step",
                    message=traceback.format_exc()
                )

        show_payroll_submission_status(submitted, unsubmitted, self)
        frappe.flags.via_payroll_entry = False

    @frappe.whitelist()
    def make_bank_entry(self, for_withheld_salaries: bool = False) -> Optional[Document]:
        self.check_permission("write")
        self.employee_based_payroll_payable_entries = {}
        employee_wise_accounting_enabled = frappe.db.get_single_value(
        "Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
    )

        salary_slip_total = 0
        salary_details = self.get_salary_slip_details(for_withheld_salaries)

        for sd in salary_details:
            if not sd.salary_component:
                continue

            if sd.parentfield == "earnings":
                result = frappe.db.get_value(
                "Salary Component",
                sd.salary_component,
                (
                    "is_flexible_benefit",
                    "only_tax_impact",
                    "create_separate_payment_entry_against_benefit_claim",
                    "statistical_component",
                ),
                cache=True,
            )

                if result:
                    is_flexible_benefit, only_tax_impact, create_separate_je, statistical_component = result
                else:
                    is_flexible_benefit = only_tax_impact = create_separate_je = statistical_component = 0

                if only_tax_impact != 1 and statistical_component != 1:
                    if is_flexible_benefit == 1 and create_separate_je == 1:
                        self.set_accounting_entries_for_bank_entry(
                        sd.amount, sd.salary_component
                    )
                    else:
                        if employee_wise_accounting_enabled:
                            self.set_employee_based_payroll_payable_entries(
                            "earnings",
                            sd.employee,
                            sd.amount,
                            sd.salary_structure,
                        )
                    salary_slip_total += sd.amount

            elif sd.parentfield == "deductions":
                statistical_component = frappe.db.get_value(
                "Salary Component",
                sd.salary_component,
                "statistical_component",
                cache=True,
            ) or 0

                if not statistical_component:
                    if employee_wise_accounting_enabled:
                        self.set_employee_based_payroll_payable_entries(
                        "deductions",
                        sd.employee,
                        sd.amount,
                        sd.salary_structure,
                    )
                    salary_slip_total -= sd.amount

        total_loan_repayment = self.process_loan_repayments_for_bank_entry(salary_details) or 0
        salary_slip_total -= total_loan_repayment

        bank_entry = None
        if salary_slip_total != 0:
            remark = "withheld salaries" if for_withheld_salaries else "salaries"
            bank_entry = self.set_accounting_entries_for_bank_entry(
 		   salary_slip_total, remark, employee_wise_accounting_enabled
	    )
            if for_withheld_salaries:
                link_bank_entry_in_salary_withholdings(salary_details, bank_entry.name)

        else:
            frappe.msgprint(_("Total Net Pay is zero; Bank Entry will not be created."))

        return bank_entry
