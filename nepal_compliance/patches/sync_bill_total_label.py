def execute():
    """Sync Taxable Summary Bill Total label on existing Sales/Purchase Invoice fields."""
    from nepal_compliance.custom_field import create_custom_fields

    create_custom_fields(quiet=True)
