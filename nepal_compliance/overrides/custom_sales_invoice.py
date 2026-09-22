import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.controllers.taxes_and_totals import (
    calculate_taxes_and_totals as ERPNextTaxesAndTotals,
)

from nepal_compliance.utils import apply_nontaxable_item_vat_override


class NepalSalesTaxesAndTotals(ERPNextTaxesAndTotals):
    def update_item_tax_map(self):
        """Load normal item taxes, then suppress VAT on non-taxable items."""
        super().update_item_tax_map()
        apply_nontaxable_item_vat_override(self.doc)


class CustomSalesInvoice(SalesInvoice):
    def calculate_taxes_and_totals(self):
        NepalSalesTaxesAndTotals(self)

    def on_cancel(self):
        allowed_roles = ("Accounts Manager",)
        user_roles = frappe.get_roles(frappe.session.user)
        if not any(role in allowed_roles for role in user_roles):
            role_name = ", ".join(allowed_roles)
            frappe.throw(_("You cannot cancel <b>{0}</b>, Only allowed for <b>{1}</b>. Please create a Return / Credit Note instead.").format(self.name, role_name))

        super().on_cancel()
