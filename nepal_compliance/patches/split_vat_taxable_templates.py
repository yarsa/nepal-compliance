import frappe

from nepal_compliance.utils import (
    _legacy_vat_template_rate,
    get_configured_vat_accounts,
    get_or_create_vat_taxable_template,
)


def execute():
    """Split eligible shared VAT templates by transaction side and rate."""
    configured = get_configured_vat_accounts()
    legacy_targets = {}

    for company, accounts in configured.items():
        names = frappe.get_all(
            "Item Tax Template",
            filters={"company": company},
            pluck="name",
        )
        for name in names:
            rate = _legacy_vat_template_rate(name, company, accounts)
            if rate is None:
                continue
            targets = []
            for side in ("sales", "purchase"):
                account = accounts.get(side)
                if account:
                    targets.append(
                        get_or_create_vat_taxable_template(
                            company, account, side, rate
                        )
                    )
            if targets:
                legacy_targets[name] = targets

    if not legacy_targets:
        return

    source_rows = frappe.get_all(
        "Item Tax",
        filters={"item_tax_template": ["in", list(legacy_targets)]},
        fields=[
            "parent",
            "parenttype",
            "parentfield",
            "item_tax_template",
            "tax_category",
            "valid_from",
            "minimum_net_rate",
            "maximum_net_rate",
        ],
        limit_page_length=0,
    )
    for source in source_rows:
        parent = frappe.get_doc(source.parenttype, source.parent)
        for target in legacy_targets[source.item_tax_template]:
            duplicate = next(
                (
                    row
                    for row in parent.get(source.parentfield) or []
                    if row.item_tax_template == target
                    and row.tax_category == source.tax_category
                    and row.valid_from == source.valid_from
                    and row.minimum_net_rate == source.minimum_net_rate
                    and row.maximum_net_rate == source.maximum_net_rate
                ),
                None,
            )
            if duplicate:
                continue
            child = parent.append(
                source.parentfield,
                {
                    "item_tax_template": target,
                    "tax_category": source.tax_category,
                    "valid_from": source.valid_from,
                    "minimum_net_rate": source.minimum_net_rate,
                    "maximum_net_rate": source.maximum_net_rate,
                },
            )
            child.db_insert()
