import frappe

def execute():
    """
    Triggers the creation of custom fields for Nepal compliance.
    
    This function imports and invokes the `create_custom_fields` routine to set up or update custom fields as required by the compliance module.
    """
    from nepal_compliance.custom_field import create_custom_fields
    create_custom_fields()
