from nepal_compliance.custom_field import create_custom_fields
from nepal_compliance.default_tax_template import set_default_purchase_tax_template


def execute():
    create_custom_fields(quiet=True)
    set_default_purchase_tax_template()
