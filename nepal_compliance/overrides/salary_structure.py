import frappe
from frappe import _
from frappe.utils import cint, flt
from hrms.payroll.doctype.salary_structure.salary_structure import SalaryStructure as HRMSSalaryStructure

class CustomSalaryStructure(HRMSSalaryStructure):
    def validate_max_benefits_with_flexi(self):
        have_a_flexi = False
        if self.earnings:
            flexi_amount = 0
            for earning_component in self.earnings:
                if earning_component.is_flexible_benefit == 1:
                    have_a_flexi = True
                    max_of_component = frappe.db.get_value(
                        "Salary Component", earning_component.salary_component, "max_benefit_amount"
                    ) or 0
                    flexi_amount += max_of_component

            if have_a_flexi and flt(self.max_benefits) == 0:
                frappe.msgprint(_("Saved/Submitted Salary Structure with zero Max benefits amount."))

            if have_a_flexi and flexi_amount and flt(self.max_benefits) > flexi_amount:
                frappe.throw(
                    _(
                        "Total flexible benefit component amount {0} should not be less than max benefits {1}"
                    ).format(flexi_amount, self.max_benefits)
                )

        if not have_a_flexi and flt(self.max_benefits) > 0:
            frappe.throw(
                _("Salary Structure should have flexible benefit component(s) to dispense benefit amount")
            )