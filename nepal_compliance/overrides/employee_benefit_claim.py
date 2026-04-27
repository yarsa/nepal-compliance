import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate
from datetime import date
from hrms.hr.utils import validate_active_employee
from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import EmployeeBenefitClaim as HRMSEmployeeBenefitClaim
from nepal_compliance.api.employee_benefit_claim import get_max_amount_eligible

class CustomEmployeeBenefitClaim(HRMSEmployeeBenefitClaim):
    def validate(self):
        validate_active_employee(self.employee)

        if not getattr(self, "claim_festival_allowance", False):
            return super().validate()

        self.ensure_festival_allowance_not_already_claimed()

        max_benefits = get_max_amount_eligible(self.employee, self.claim_date)
        self.max_amount_eligible = max_benefits

        if not self.claimed_amount or flt(self.claimed_amount) == 0:
            self.claimed_amount = max_benefits

        payroll_period = get_payroll_period(
            self.claim_date,
            self.claim_date,
            frappe.db.get_value("Employee", self.employee, "company")
        )
        if not payroll_period:
            frappe.throw(
                _("{0} is not in a valid Payroll Period").format(
                    frappe.format(self.claim_date, dict(fieldtype="Date"))
                )
            )

        self.validate_max_benefit_for_component(payroll_period)
        self.validate_max_benefit_for_sal_struct(max_benefits)
        self.validate_benefit_claim_amount(max_benefits, payroll_period)

        if self.pay_against_benefit_claim:
            self.validate_non_pro_rata_benefit_claim(max_benefits, payroll_period)

    def ensure_festival_allowance_not_already_claimed(self):
        payroll_period = get_payroll_period(
            self.claim_date,
            self.claim_date,
            frappe.db.get_value("Employee", self.employee, "company")
        )

        if not payroll_period:
            frappe.throw(_("No payroll period found for the claim date."))

        existing = frappe.db.exists(
            "Employee Benefit Claim",
            {
            "employee": self.employee,
            "claim_festival_allowance": 1,
            "docstatus": ["!=", 2],
            "name": ["!=", self.name],
            "claim_date": ["between", [payroll_period.start_date, payroll_period.end_date]],
            },
        )

        if existing:
            frappe.throw(
                _("Festival allowance has already been claimed by employee {0} for this Payroll Period.").format(
                    self.employee,
                    formatdate(payroll_period.start_date),
                    formatdate(payroll_period.end_date),
                )
            )
