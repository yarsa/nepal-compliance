# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and Contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import flt

from nepal_compliance.tax_templates import get_item_rate_excise_account

INVOICE_DOCTYPES = ("Sales Invoice", "Purchase Invoice")
SUPPORTED_CHARGE_TYPES = ("Actual", "On Net Total", "On Item Quantity")
PREVIOUS_ROW_CHARGE_TYPES = ("On Previous Row Total", "On Previous Row Amount")


def _company_excise_config(company):
    """Return (excise_account, record_separately) for a company.

    A blank Excise Duty Account means no excise licence: excise on the managed
    templates' placeholder ledger is folded into the item rates.
    """
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    for row in settings.get("vat_accounts") or []:
        if row.company == company:
            if not row.get("excise_account"):
                return get_item_rate_excise_account(company), False
            return row.get("excise_account"), bool(row.get("record_excise_separately"))
    return None, True


def _line_base(item):
    """Pre-tax line value, from what the user entered rather than computed fields."""
    amount = flt(item.get("amount"))
    return amount or flt(item.get("rate")) * flt(item.get("qty"))


def _excise_total(rows, items, base):
    """Excise the rows describe.

    This runs on before_validate, ahead of ERPNext's own calculation, so
    tax_amount is not populated yet on a new document and the figure has to be
    derived from the charge type.
    """
    total = 0.0
    for tax in rows:
        charge_type = tax.get("charge_type")
        if charge_type not in SUPPORTED_CHARGE_TYPES:
            frappe.throw(
                _("Excise row {0} uses charge type {1}, which cannot be added to the item rates. Use Actual, On Net Total or On Item Quantity.").format(
                    tax.idx, frappe.bold(charge_type)
                ),
                title=_("Unsupported Excise Charge Type"),
            )
        if charge_type == "Actual":
            total += flt(tax.get("tax_amount"))
        elif charge_type == "On Net Total":
            total += base * flt(tax.get("rate")) / 100.0
        else:
            total += flt(tax.get("rate")) * sum(flt(item.get("qty")) for item in items)
    return flt(total, 2)


def _detach_rows_referencing_excise(doc, excise_rows):
    """Repoint rows that were charged on an excise row before it is removed.

    The managed Excise + VAT template stacks VAT as On Previous Row Total against
    the excise row. Once the excise is inside the item rates that row is gone, so
    a dependent row would point at nothing. On Net Total over the now
    excise-inclusive net gives the same figure.
    """
    excise_idx = {str(tax.idx) for tax in excise_rows}
    for tax in doc.get("taxes") or []:
        if tax in excise_rows:
            continue
        if tax.get("charge_type") in PREVIOUS_ROW_CHARGE_TYPES and str(
            tax.get("row_id") or ""
        ) in excise_idx:
            tax.charge_type = "On Net Total"
            tax.row_id = None


def fold_excise_into_item_rate(doc, method):
    """Move excise into the item rates when the company has no excise licence.

    ERPNext always posts a tax row to its own account_head: Sales Taxes and
    Charges has no category field at all, and a purchase Valuation row still
    credits the account head, reaching item cost only for stock items. Folding
    the excise into the rate is the one approach that behaves the same on both
    sides, and it also means a plain On Net Total VAT row charges VAT on the
    excise-inclusive base with no row chaining to maintain.

    Folding happens only while an excise row is present. The row is removed in
    the same pass, so re-saving cannot apply it twice.
    """
    if doc.doctype not in INVOICE_DOCTYPES:
        return

    excise_account, record_separately = _company_excise_config(doc.company)
    if not excise_account or record_separately:
        return

    excise_rows = [
        tax for tax in doc.get("taxes") or [] if tax.account_head == excise_account
    ]
    if not excise_rows:
        return
    if any(tax.get("included_in_print_rate") for tax in excise_rows):
        # The folding maths assumes the item price excludes excise.
        frappe.throw(
            _("Excise that is included in the item price cannot be added to the item rates. Turn on Record Excise Separately for Company {0}, or use a tax template whose price excludes tax.").format(
                frappe.bold(doc.company)
            ),
            title=_("Inclusive Excise Not Supported"),
        )

    items = list(doc.get("items") or [])
    base = sum(_line_base(item) for item in items)
    excise_total = _excise_total(excise_rows, items, base)
    if not excise_total:
        return
    if not base:
        frappe.throw(
            _("Excise cannot be added to the item rates because the items have no value."),
            title=_("Excise Not Distributable"),
        )

    remaining = excise_total
    for index, item in enumerate(items):
        share = remaining if index == len(items) - 1 else flt(
            excise_total * _line_base(item) / base, 2
        )
        remaining = flt(remaining - share, 2)
        qty = flt(item.get("qty"))
        if not qty:
            continue
        item.excise_amount = flt(item.get("excise_amount")) + share
        item.rate = flt(item.rate) + share / qty

    doc.excise_amount = flt(doc.get("excise_amount")) + excise_total
    _detach_rows_referencing_excise(doc, excise_rows)
    doc.set(
        "taxes",
        [tax for tax in doc.get("taxes") or [] if tax.account_head != excise_account],
    )
