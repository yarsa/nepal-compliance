def execute():
    """Create Nepal Compliance property setters on existing sites (idempotent)."""
    from nepal_compliance.property_setter import create_property_setters

    create_property_setters()
