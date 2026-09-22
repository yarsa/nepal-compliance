from nepal_compliance.custom_field import create_custom_fields


def execute():
    """Create the Sales Order taxable summary fields (idempotent)."""
    create_custom_fields(quiet=True)
