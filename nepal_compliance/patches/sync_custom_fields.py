def execute():
    """Re-sync Nepal Compliance custom fields on existing sites.

    custom_fields_patches already ran on older sites, so fields added later
    (taxable summary, item_vat_detail, etc.) are never created. Call create
    again before patches that query those columns.
    """
    from nepal_compliance.custom_field import create_custom_fields

    create_custom_fields(quiet=True)
