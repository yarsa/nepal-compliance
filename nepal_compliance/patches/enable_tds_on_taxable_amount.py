def execute():
    """Add TDS-on-taxable-amount option and default it on for existing categories."""
    from nepal_compliance.custom_field import create_custom_fields
    from nepal_compliance.tds_withholding import (
        enable_tds_on_taxable_amount_for_existing_categories,
        setup_tds_on_taxable_amount_permissions,
    )

    create_custom_fields(quiet=True)
    setup_tds_on_taxable_amount_permissions()
    enable_tds_on_taxable_amount_for_existing_categories()
