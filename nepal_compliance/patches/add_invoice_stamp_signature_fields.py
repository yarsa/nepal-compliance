from nepal_compliance.custom_field import create_custom_fields


def execute():
    """Create the company stamp, user signature and Signed By fields on existing sites (idempotent)."""
    create_custom_fields(quiet=True)
