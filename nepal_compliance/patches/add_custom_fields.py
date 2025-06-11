import frappe

def execute():
    from nepal_compliance.custom_field import create_custom_fields
    create_custom_fields()
