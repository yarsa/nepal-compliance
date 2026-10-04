import unittest

from nepal_compliance import form_layout
from nepal_compliance.form_layout import (
    ESSENTIALS_TAB,
    MORE_DETAILS_TAB,
    build_field_order,
    natural_order,
)

SECTIONS = [
    ("party", "Customer", None, [["customer", "vat_number"], ["posting_date"]]),
    ("items", None, None, [["items"]]),
]
NATURAL = ["naming_series", "customer", "vat_number", "posting_date", "project", "items_section", "items", "taxes"]


class TestNaturalOrder(unittest.TestCase):
    def test_custom_fields_follow_their_insert_after(self):
        order = natural_order(["a", "b"], [("x", "a"), ("y", "x"), ("top", None), ("lost", "gone")])
        self.assertEqual(order, ["top", "a", "x", "y", "b", "lost"])

    def test_fields_after_one_anchor_keep_their_idx_order(self):
        self.assertEqual(natural_order(["a", "b"], [("x", "a"), ("y", "a")]), ["a", "x", "y", "b"])


class TestBuildFieldOrder(unittest.TestCase):
    def test_essentials_first_then_everything_else_in_order(self):
        self.assertEqual(
            build_field_order(NATURAL, SECTIONS),
            [
                ESSENTIALS_TAB,
                "nc_ess_party_section", "customer", "vat_number", "nc_ess_party_col1", "posting_date",
                "nc_ess_items_section", "items",
                MORE_DETAILS_TAB,
                "naming_series", "project", "items_section", "taxes",
            ],
        )

    def test_missing_fields_are_skipped(self):
        order = build_field_order([f for f in NATURAL if f != "vat_number"], SECTIONS)
        self.assertNotIn("vat_number", order)
        self.assertEqual(order[:4], [ESSENTIALS_TAB, "nc_ess_party_section", "customer", "nc_ess_party_col1"])

    def test_previous_layout_fields_in_the_natural_order_are_ignored(self):
        natural = [ESSENTIALS_TAB, "nc_ess_party_section"] + NATURAL + [MORE_DETAILS_TAB]
        self.assertEqual(build_field_order(natural, SECTIONS), build_field_order(NATURAL, SECTIONS))

    def test_extra_field_follows_the_essential_before_it(self):
        order = build_field_order(NATURAL, SECTIONS, ["project"])
        self.assertEqual(order[4:7], ["nc_ess_party_col1", "posting_date", "project"])
        self.assertEqual(order.count("project"), 1)

    def test_extra_field_before_every_essential_goes_first(self):
        order = build_field_order(NATURAL, SECTIONS, ["naming_series"])
        self.assertEqual(order[1:3], ["nc_ess_party_section", "naming_series"])

    def test_unknown_and_already_essential_extras_are_ignored(self):
        self.assertEqual(build_field_order(NATURAL, SECTIONS, ["gone", "customer"]), build_field_order(NATURAL, SECTIONS))

    def test_every_doctype_keeps_each_field_exactly_once(self):
        for doctype, sections in form_layout.ESSENTIALS.items():
            spec = [f for _key, _label, _dep, columns in sections for column in columns for f in column]
            natural = ["naming_series"] + spec + ["remarks"]
            order = build_field_order(natural, sections)
            ours = [f["fieldname"] for f in form_layout.layout_fields(doctype)]
            with self.subTest(doctype=doctype):
                self.assertEqual(sorted(order), sorted(natural + ours))
                self.assertEqual(order[0], ESSENTIALS_TAB)
                self.assertLess(order.index(spec[-1]), order.index(MORE_DETAILS_TAB))


if __name__ == "__main__":
    unittest.main()
