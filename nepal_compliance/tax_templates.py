# Copyright (c) 2026, Yarsa Labs Pvt. Ltd. and Contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from frappe.utils import flt

from nepal_compliance.utils import format_vat_rate

NEPAL_VAT_RATE = 13.0

TEMPLATE_DOCTYPES = {
    "sales": "Sales Taxes and Charges Template",
    "purchase": "Purchase Taxes and Charges Template",
}

# Every managed template variant. "Inclusive" means the item price already
# contains the tax.
VARIANTS = ("exclusive", "inclusive", "excise", "excise_inclusive")
EXCISE_VARIANTS = ("excise", "excise_inclusive")


def template_title(side, variant):
    """Return the stable title that marks a tax template as managed by this app."""
    label = "Sales" if side == "sales" else "Purchase"
    rate = format_vat_rate(NEPAL_VAT_RATE)
    if variant == "inclusive":
        return f"Nepal VAT {rate}% Inclusive ({label})"
    if variant == "excise":
        return f"Nepal Excise + VAT {rate}% ({label})"
    if variant == "excise_inclusive":
        return f"Nepal Excise + VAT {rate}% Inclusive ({label})"
    return f"Nepal VAT {rate}% ({label})"


def _vat_row(vat_account, inclusive=False, charge_type="On Net Total", row_id=None):
    row = {
        "charge_type": charge_type,
        "account_head": vat_account,
        "description": _("VAT {0}%").format(format_vat_rate(NEPAL_VAT_RATE)),
        "rate": NEPAL_VAT_RATE,
        "included_in_print_rate": 1 if inclusive else 0,
    }
    if row_id:
        row["row_id"] = row_id
    return row


def _template_rows(variant, vat_account, excise_account):
    if variant not in EXCISE_VARIANTS:
        return [_vat_row(vat_account, inclusive=variant == "inclusive")]

    # Excise first, then VAT on the excise-inclusive base. The excise rate is left
    # at zero because it varies by product; the user sets it on the template.
    # ERPNext requires every row above an inclusive On Previous Row Total row to
    # be inclusive too, so both rows share the flag.
    inclusive = variant == "excise_inclusive"
    return [
        {
            "charge_type": "On Net Total",
            "account_head": excise_account,
            "description": _("Excise Duty"),
            "rate": 0,
            "included_in_print_rate": 1 if inclusive else 0,
        },
        _vat_row(
            vat_account, inclusive=inclusive, charge_type="On Previous Row Total", row_id=1
        ),
    ]


def is_managed_template(doctype, name):
    """True when a template is one this app created, identified by its title."""
    title = frappe.get_cached_value(doctype, name, "title") or ""
    managed = {
        template_title(side, variant)
        for side in ("sales", "purchase")
        for variant in VARIANTS
    }
    return title in managed


def _repoint_managed_rows(template, variant, vat_account, excise_account):
    """Repair only the rows this app owns. Returns True when something changed.

    The managed VAT row is identified by its charge type and rate rather than by
    rate alone, so a second 13% row a user added does not block the repair or get
    mistaken for ours.
    """
    changed = False
    is_excise = variant in EXCISE_VARIANTS
    vat_charge_type = "On Previous Row Total" if is_excise else "On Net Total"
    vat_rows = [
        row
        for row in template.taxes
        if flt(row.rate) == NEPAL_VAT_RATE and row.charge_type == vat_charge_type
    ]
    if len(vat_rows) == 1 and vat_rows[0].account_head != vat_account:
        vat_rows[0].account_head = vat_account
        changed = True

    if is_excise and excise_account:
        excise_rows = [row for row in template.taxes if row.charge_type == "On Net Total"]
        if len(excise_rows) == 1 and excise_rows[0].account_head != excise_account:
            excise_rows[0].account_head = excise_account
            changed = True

    return changed


def get_or_create_nepal_tax_template(
    company, side, variant, vat_account, excise_account=None, create=True
):
    """Return the managed template for a company, side and variant, creating it if absent.

    With create=False a missing template is left missing and None is returned.

    An existing template is repaired conservatively: only the VAT row's account is
    repointed. Rates, extra rows and every other field stay as the user left them,
    matching sync_managed_vat_taxable_templates rather than the overwriting policy
    used for VAT-exempt Item Tax Templates.
    """
    doctype = TEMPLATE_DOCTYPES[side]
    title = template_title(side, variant)
    existing = frappe.get_all(
        doctype, filters={"company": company, "title": title}, pluck="name"
    )
    if existing:
        # Managed records owned by this app, so permissions are bypassed the same
        # way the managed Item Tax Template helpers in utils.py do.
        template = frappe.get_doc(doctype, existing[0])
        if _repoint_managed_rows(template, variant, vat_account, excise_account):
            template.save(ignore_permissions=True)
        return template.name
    if not create:
        return None

    template = frappe.get_doc(
        {
            "doctype": doctype,
            "title": title,
            "company": company,
            "taxes": _template_rows(variant, vat_account, excise_account),
        }
    ).insert(ignore_permissions=True)
    return template.name


def sync_nepal_tax_templates(
    company,
    sales_vat_account,
    purchase_vat_account,
    excise_account=None,
    variants=VARIANTS,
    create=False,
):
    """Repair the managed Nepal tax templates of one company. Idempotent.

    Only templates that already exist are touched unless create is set, which the
    Create Tax Templates button in Nepal Compliance Settings does. A side with no
    configured VAT account is skipped, as are the excise variants until an excise
    account is configured.
    """
    names = []
    for side, vat_account in (
        ("sales", sales_vat_account),
        ("purchase", purchase_vat_account),
    ):
        if not vat_account:
            continue
        for variant in variants:
            if variant in EXCISE_VARIANTS and not excise_account:
                continue
            name = get_or_create_nepal_tax_template(
                company, side, variant, vat_account, excise_account, create=create
            )
            if name:
                names.append(name)
    return names


def set_default_tax_template(company, side, template_name):
    """Mark one template as the company default, if it is not already.

    Saving with is_default set makes ERPNext clear the flag on every other template
    for the same company, so this replaces whatever default was in place.
    """
    if not template_name:
        return False

    doctype = TEMPLATE_DOCTYPES[side]
    template = frappe.get_doc(doctype, template_name)
    if template.is_default:
        return False
    if template.disabled:
        frappe.throw(
            _("Tax template {0} is disabled and cannot be made the default.").format(
                frappe.bold(template_name)
            ),
            title=_("Disabled Template"),
        )

    template.is_default = 1
    template.save(ignore_permissions=True)
    return True
