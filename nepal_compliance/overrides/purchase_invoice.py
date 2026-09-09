from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.controllers.taxes_and_totals import (
    calculate_taxes_and_totals as ERPNextTaxesAndTotals,
)

from nepal_compliance.utils import (
    apply_pan_bill_vat_override,
    apply_taxable_amount_as_tds_base,
)


class NepalPurchaseTaxesAndTotals(ERPNextTaxesAndTotals):
    def update_item_tax_map(self):
        """Load normal item taxes, then suppress only configured VAT for PAN bills."""
        super().update_item_tax_map()
        apply_pan_bill_vat_override(self.doc)


class CustomPurchaseInvoice(PurchaseInvoice):
    def calculate_taxes_and_totals(self):
        NepalPurchaseTaxesAndTotals(self)

    def set_tax_withholding(self):
        """Use Taxable Amount as the TDS base when the withholding category requires it."""
        apply_taxable_amount_as_tds_base(self)
        super().set_tax_withholding()
        # ERPNext recalculates tax_withholding_net_total from all Apply TDS
        # items after inserting the Actual TDS row. Restore the configured
        # taxable base so the invoice records the amount actually used.
        apply_taxable_amount_as_tds_base(self)
