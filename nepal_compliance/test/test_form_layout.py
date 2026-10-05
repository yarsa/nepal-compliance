import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import form_layout
from nepal_compliance.form_layout import (
    ESSENTIALS_TAB,
    MORE_DETAILS_TAB,
    build_field_order,
    natural_order,
    rebuild_field_order,
    update_field_order,
)

SECTIONS = [
    ("party", "Customer", None, [["customer", "vat_number"], ["posting_date"]]),
    ("items", None, None, [["items"]]),
]
NATURAL = ["naming_series", "customer", "vat_number", "posting_date", "project", "items_section", "items", "taxes"]
LAYOUT_NAMES = {ESSENTIALS_TAB, "nc_ess_party_section", "nc_ess_party_col1", "nc_ess_items_section", MORE_DETAILS_TAB}


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


def moved(order, fieldname, after):
    """Return ``order`` with ``fieldname`` moved to just after ``after``, as Customize Form would."""
    order = [f for f in order if f != fieldname]
    order.insert(order.index(after) + 1, fieldname)
    return order


def tab_of(order):
    return order[: order.index(MORE_DETAILS_TAB)]


class TestUpdateFieldOrder(unittest.TestCase):
    def setUp(self):
        self.saved = build_field_order(NATURAL, SECTIONS)

    def test_nothing_changes_when_nothing_is_new(self):
        self.assertEqual(update_field_order(self.saved, NATURAL, LAYOUT_NAMES), self.saved)

    def test_field_moved_into_the_tab_stays(self):
        saved = moved(self.saved, "taxes", "items")
        self.assertIn("taxes", tab_of(update_field_order(saved, NATURAL, LAYOUT_NAMES)))

    def test_field_moved_out_of_the_tab_stays_out(self):
        saved = moved(self.saved, "vat_number", "naming_series")
        self.assertNotIn("vat_number", tab_of(update_field_order(saved, NATURAL, LAYOUT_NAMES)))

    def test_new_field_goes_to_more_details_even_beside_an_essential(self):
        natural = NATURAL[:2] + ["new_field"] + NATURAL[2:]
        order = update_field_order(self.saved, natural, LAYOUT_NAMES)
        self.assertNotIn("new_field", tab_of(order))
        self.assertEqual(order[order.index("naming_series") + 1], "new_field")

    def test_new_field_follows_its_more_details_neighbour(self):
        order = update_field_order(self.saved, NATURAL + ["new_field"], LAYOUT_NAMES)
        self.assertEqual(order[-2:], ["taxes", "new_field"])

    def test_field_removed_from_the_doctype_is_dropped(self):
        order = update_field_order(self.saved, [f for f in NATURAL if f != "project"], LAYOUT_NAMES)
        self.assertNotIn("project", order)

    def test_extra_from_the_settings_moves_in(self):
        order = update_field_order(self.saved, NATURAL, LAYOUT_NAMES, extras=["project"])
        self.assertEqual(order[order.index("posting_date") + 1], "project")

    def test_extra_taken_off_the_settings_moves_out(self):
        saved = build_field_order(NATURAL, SECTIONS, ["project"])
        order = update_field_order(saved, NATURAL, LAYOUT_NAMES, removed=["project"])
        self.assertNotIn("project", tab_of(order))
        self.assertEqual(order[order.index("naming_series") + 1], "project")

    def test_running_twice_changes_nothing_more(self):
        natural = NATURAL + ["new_field"]
        once = update_field_order(moved(self.saved, "taxes", "items"), natural, LAYOUT_NAMES, extras=["project"])
        self.assertEqual(update_field_order(once, natural, LAYOUT_NAMES, extras=["project"]), once)


class TestRebuildFieldOrder(unittest.TestCase):
    V1 = [("party", "Customer", None, [["customer"], ["posting_date"]]), ("totals", "Totals", None, [["grand_total"]])]
    V2 = [("party", "Customer", None, [["customer"], ["posting_date"]]), ("bill_summary", "Bill", None, [["total", "grand_total"]])]
    NATURAL = ["customer", "posting_date", "project", "total", "grand_total", "taxes"]

    def test_new_layout_is_built_and_user_moves_are_kept(self):
        saved = moved(build_field_order(self.NATURAL, self.V1), "taxes", "grand_total")
        order = rebuild_field_order(saved, self.NATURAL, self.V2, extras=["project"])
        self.assertEqual(
            tab_of(order),
            [ESSENTIALS_TAB, "nc_ess_party_section", "customer", "nc_ess_party_col1", "posting_date", "project",
             "taxes", "nc_ess_bill_summary_section", "total", "grand_total"],
        )

    def test_extra_next_to_a_bill_figure_goes_under_the_section_above(self):
        natural = ["customer", "posting_date", "items", "total", "taxes", "grand_total"]
        sections = [
            ("party", "Customer", None, [["customer"], ["posting_date"]]),
            ("items", None, None, [["items"]]),
            ("bill_summary", "Bill", None, [["discount"], ["total", "grand_total"]]),
        ]
        built = build_field_order(natural + ["discount"], sections, ["taxes"])
        self.assertEqual(built[built.index("items") + 1], "taxes")
        names = {ESSENTIALS_TAB, MORE_DETAILS_TAB, "nc_ess_party_section", "nc_ess_party_col1", "nc_ess_items_section",
                 "nc_ess_bill_summary_section", "nc_ess_bill_summary_col1"}
        saved = build_field_order(natural + ["discount"], sections)
        updated = update_field_order(saved, natural + ["discount"], names, extras=["taxes"])
        self.assertEqual(updated[updated.index("items") + 1], "taxes")
        self.assertEqual(updated[updated.index("nc_ess_bill_summary_col1") + 1 :][:2], ["total", "grand_total"])

    def test_a_field_taken_off_the_settings_is_not_kept(self):
        saved = build_field_order(self.NATURAL, self.V1, ["project"])
        self.assertNotIn("project", tab_of(rebuild_field_order(saved, self.NATURAL, self.V2, removed=["project"])))


class TestShowWhen(unittest.TestCase):
    def test_without_a_condition(self):
        self.assertEqual(form_layout.show_when(None, "vat_amount"), "eval:flt(doc.vat_amount)")

    def test_keeps_an_eval_condition(self):
        self.assertEqual(
            form_layout.show_when("eval: !doc.disable_rounded_total", "rounded_total"),
            "eval:(!doc.disable_rounded_total) && flt(doc.rounded_total)",
        )

    def test_turns_a_fieldname_condition_into_eval(self):
        self.assertEqual(
            form_layout.show_when("apply_customer_tds", "customer_tds_amount"),
            "eval:(doc.apply_customer_tds) && flt(doc.customer_tds_amount)",
        )

    def test_custom_condition_replaces_the_zero_check(self):
        self.assertEqual(
            form_layout.show_when(None, "grand_total", "flt(doc.grand_total) != flt(doc.summary_grand_total)"),
            "eval:flt(doc.grand_total) != flt(doc.summary_grand_total)",
        )


def bill_lines(doctype):
    """The figures column of a doctype's Bill Summary, in order."""
    return next(columns[1] for key, _label, _dep, columns in form_layout.ESSENTIALS[doctype] if key == "bill_summary")


class TestBillSummary(unittest.TestCase):
    def test_bill_summary_follows_the_items_table(self):
        for doctype in ("Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order"):
            keys = [key for key, _label, _dep, _columns in form_layout.ESSENTIALS[doctype]]
            with self.subTest(doctype=doctype):
                self.assertEqual(keys[keys.index("items") + 1], "bill_summary")
                self.assertEqual(keys[-1], "bill_summary")

    def test_invoice_lines_read_like_a_nepal_bill(self):
        self.assertEqual(
            bill_lines("Sales Invoice"),
            ["bill_subtotal", "excise_amount", "taxable_discount", "non_taxable_amount", "taxable_amount", "vat_amount",
             "summary_grand_total", "grand_total", "rounded_total"],
        )
        self.assertEqual(bill_lines("Purchase Invoice"), bill_lines("Sales Invoice"))
        self.assertNotIn("excise_amount", bill_lines("Sales Order"))
        self.assertEqual(
            bill_lines("Purchase Order"), ["total", "total_taxes_and_charges", "grand_total", "rounded_total"]
        )
        # ERPNext's own discount is an input beside the figures, never one of the bill's lines
        for doctype in ("Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order"):
            with self.subTest(doctype=doctype):
                self.assertNotIn("discount_amount", bill_lines(doctype))

    def test_only_licensed_excise_and_a_differing_grand_total_are_shown(self):
        conditions = form_layout.SHOW_WHEN["Sales Invoice"]
        self.assertIn("!(doc.items || []).some((d) => flt(d.excise_amount))", conditions["excise_amount"])
        self.assertEqual(conditions["grand_total"], "flt(doc.grand_total) != flt(doc.summary_grand_total)")
        self.assertIsNone(conditions["vat_amount"])

    def test_section_keys_are_unique(self):
        for doctype, sections in form_layout.ESSENTIALS.items():
            keys = [key for key, _label, _dep, _columns in sections]
            with self.subTest(doctype=doctype):
                self.assertEqual(len(keys), len(set(keys)))

    def test_every_shown_when_field_is_in_its_layout(self):
        for doctype, fields in form_layout.SHOW_WHEN.items():
            spec = {f for _k, _l, _d, columns in form_layout.ESSENTIALS[doctype] for column in columns for f in column}
            with self.subTest(doctype=doctype):
                self.assertLessEqual(set(fields), spec)


class TestPickRequiredFields(unittest.TestCase):
    def test_keeps_only_fields_a_user_must_enter(self):
        df = lambda **kw: frappe._dict({"read_only": 0, "default": None, **kw})
        reasons = {
            "branch": "Mandatory accounting dimension",
            "sales_person": "Required in Customize Form",
            "project": "Required custom field",
            "currency": "Required in Customize Form",
            "posted_by": "Required custom field",
            "gone": "Required custom field",
        }
        candidates = {"branch": "Branch", "sales_person": "Sales Person", "project": "Project", "currency": "Currency", "posted_by": "Posted By"}
        meta = {
            "branch": df(),
            "sales_person": df(),
            "project": df(),
            "currency": df(default="NPR"),
            "posted_by": df(read_only=1),
        }
        picked = form_layout.pick_required_fields(reasons, candidates, {"project"}, meta)
        self.assertEqual(
            picked,
            [
                {"fieldname": "branch", "label": "Branch", "reason": "Mandatory accounting dimension"},
                {"fieldname": "sales_person", "label": "Sales Person", "reason": "Required in Customize Form"},
            ],
        )


class TestExtraFieldOptions(unittest.TestCase):
    @patch("nepal_compliance.form_layout.frappe.has_permission", create=True)
    @patch("nepal_compliance.form_layout._mandatory_dimensions", return_value=["branch"])
    @patch("nepal_compliance.form_layout._required_fields")
    @patch("nepal_compliance.form_layout.get_extra_field_candidates")
    def test_required_fields_come_first_with_their_reason(self, candidates, required, _dimensions, _perm):
        candidates.return_value = {"project": "Project", "branch": "Branch", "amended_from": "Amended From"}
        required.return_value = [{"fieldname": "branch", "label": "Branch", "reason": "Mandatory accounting dimension"}]
        options = form_layout.get_extra_field_options("Sales Invoice")
        self.assertEqual([o["value"] for o in options], ["branch", "amended_from", "project"])
        self.assertEqual(options[0]["description"], "Required: Mandatory accounting dimension")
        self.assertIsNone(options[1]["description"])
        self.assertEqual(options[2]["label"], "Project (project)")


class TestExtraFieldCandidates(unittest.TestCase):
    @patch("nepal_compliance.form_layout.frappe.get_meta")
    def test_offers_only_fields_outside_the_tab(self, get_meta):
        field = lambda fieldname, fieldtype="Data", hidden=0: frappe._dict(
            fieldname=fieldname, fieldtype=fieldtype, label=fieldname.title(), hidden=hidden
        )
        get_meta.return_value = frappe._dict(
            fields=[
                field("customer"),
                field("project", "Link"),
                field("taxes", "Table"),
                field("items_section", "Section Break"),
                field("title", hidden=1),
                field(ESSENTIALS_TAB, "Tab Break"),
            ]
        )
        self.assertEqual(set(form_layout.get_extra_field_candidates("Sales Invoice")), {"project", "taxes"})

    def test_unsupported_doctype_offers_nothing(self):
        self.assertEqual(form_layout.get_extra_field_candidates("Journal Entry"), {})


if __name__ == "__main__":
    unittest.main()
