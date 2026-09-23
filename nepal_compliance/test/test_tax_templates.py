import unittest

from nepal_compliance import tax_templates


class TestNepalTaxTemplateVariants(unittest.TestCase):
    def test_every_variant_has_a_distinct_title(self):
        titles = {
            tax_templates.template_title(side, variant)
            for side in ("sales", "purchase")
            for variant in tax_templates.VARIANTS
        }
        self.assertEqual(len(titles), 8)
        self.assertIn("Nepal Excise + VAT 13% Inclusive (Sales)", titles)

    def test_vat_only_variants(self):
        exclusive = tax_templates._template_rows("exclusive", "VAT", None)
        inclusive = tax_templates._template_rows("inclusive", "VAT", None)
        self.assertEqual([row["included_in_print_rate"] for row in exclusive], [0])
        self.assertEqual([row["included_in_print_rate"] for row in inclusive], [1])

    def test_excise_variants_stack_vat_on_the_excise_row(self):
        for variant, flag in (("excise", 0), ("excise_inclusive", 1)):
            excise, vat = tax_templates._template_rows(variant, "VAT", "Excise")
            self.assertEqual(excise["account_head"], "Excise")
            self.assertEqual(vat["charge_type"], "On Previous Row Total")
            self.assertEqual(vat["row_id"], 1)
            # ERPNext rejects an inclusive VAT row above a non-inclusive one.
            self.assertEqual(excise["included_in_print_rate"], flag)
            self.assertEqual(vat["included_in_print_rate"], flag)


if __name__ == "__main__":
    unittest.main()
