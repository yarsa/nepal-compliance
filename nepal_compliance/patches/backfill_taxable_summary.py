import frappe
from frappe import _
from frappe.utils import flt


def execute():
    """Freeze taxable summary values on existing submitted invoices (idempotent).

    Computes taxable_amount, non_taxable_amount, vat_amount and item_vat_detail
    with the same logic the validate hook uses, writes them directly, and adds
    a comment with the computed values on each updated invoice. Invoices whose
    company has no VAT account configured are left empty so reports keep using
    the live fallback and a later configuration can still fix them.

    Selection is keyed on item_vat_detail (not taxable_amount) so invoices
    created after the summary fields existed but before item_vat_detail was
    introduced are backfilled too.
    """
    from nepal_compliance.utils import set_taxable_amounts

    for doctype in ("Sales Invoice", "Purchase Invoice"):
        names = frappe.get_all(
            doctype,
            filters={"docstatus": 1, "item_vat_detail": ["is", "not set"]},
            pluck="name",
        )
        for count, name in enumerate(names, start=1):
            doc = frappe.get_doc(doctype, name)
            set_taxable_amounts(doc, None)
            if doc.get("taxable_amount") is None:
                continue

            frappe.db.set_value(
                doctype,
                name,
                {
                    "taxable_amount": doc.taxable_amount,
                    "non_taxable_amount": doc.non_taxable_amount,
                    "vat_amount": doc.vat_amount,
                    "summary_grand_total": doc.summary_grand_total,
                    "item_vat_detail": doc.item_vat_detail,
                },
                update_modified=False,
            )
            doc.add_comment(
                "Comment",
                _(
                    "Nepal Compliance: taxable summary computed for IRD reports. "
                    "Taxable: {0}, Non-Taxable: {1}, VAT: {2}"
                ).format(
                    flt(doc.taxable_amount, 2),
                    flt(doc.non_taxable_amount, 2),
                    flt(doc.vat_amount, 2),
                ),
            )

            if count % 100 == 0:
                frappe.db.commit()
