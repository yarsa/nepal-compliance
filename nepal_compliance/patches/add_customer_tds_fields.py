from nepal_compliance.custom_field import create_custom_fields


def execute():
    """Create the customer TDS receipt fields on existing sites (idempotent)."""
    create_custom_fields(quiet=True)
