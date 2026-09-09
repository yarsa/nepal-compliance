def execute():
    """Create the invoice country snapshot fields on existing sites."""
    from nepal_compliance.custom_field import create_custom_fields

    create_custom_fields(quiet=True)
