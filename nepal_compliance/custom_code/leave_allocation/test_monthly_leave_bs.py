import unittest
from types import SimpleNamespace
from unittest.mock import patch
from datetime import date

# Import the module under test
from nepal_compliance.custom_code.leave_allocation.monthly_leave_bs import allocate_monthly_leave_bs

class TestMonthlyLeaveBS(unittest.TestCase):

    def setUp(self):
        # Mock Leave Type document
        self.leave_type_doc = SimpleNamespace(
            name="Casual Leave",
            allocate_leave_on_start_of_bs_month=True,
            bs_monthly_allocation_amount=2,
            max_leaves_allowed=5,
            is_earned_leave=False
        )

        # Mock Leave Allocation document
        self.alloc_doc = SimpleNamespace(
            name="ALLOC-001",
            leave_type="Casual Leave",
            employee="EMP-001",
            from_date=date(2026, 2, 1),
            to_date=date(2026, 2, 28),
            total_leaves_allocated=1
        )
        self.alloc_doc.db_set = lambda field, value, update_modified=False: setattr(self.alloc_doc, field, value)

    # Patch frappe functions
    def patch_frappe(self):
        return patch.multiple(
            "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs",
            frappe=SimpleNamespace(
                get_doc=self.mock_get_doc,
                get_all=self.mock_get_all,
                db=SimpleNamespace(
                    set_single_value=lambda doctype, field, val: None,
                    commit=lambda: None,
                    rollback=lambda: None,
                    get_single_value=lambda doctype, field: 0
                ),
                log_error=lambda msg, title="": None,
                msgprint=lambda msg: None,
                has_permission=lambda doctype, perm: True,
                utils=SimpleNamespace(cint=lambda x: int(x)),
                logger=lambda *a, **kw: SimpleNamespace(
                    info=lambda *a, **kw: None,
                    warning=lambda *a, **kw: None,
                    error=lambda *a, **kw: None,
                    debug=lambda *a, **kw: None,
                    exception=lambda *a, **kw: None,
                ),
                throw=lambda exc=Exception, title=None, **kwargs: (_ for _ in ()).throw(exc(msg)),
            )
        )

    # Mock implementations
    def mock_get_doc(self, doctype, name=None, **kwargs):
        if doctype == "Leave Type":
            return self.leave_type_doc
        elif doctype == "Leave Allocation":
            return self.alloc_doc
        return None

    def mock_get_all(self, doctype, filters=None, pluck=None, fields=None):
        if doctype == "Leave Type":
            return ["Casual Leave"]
        elif doctype == "Leave Allocation":
            if pluck == "name":
                return ["ALLOC-001"]
            return [SimpleNamespace(name="ALLOC-001")]
        return []

    # Test cases
    def test_allocation_success(self):
        """Test normal allocation."""
        with self.patch_frappe():
            with patch(
                "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.create_leave_ledger_entry",
                lambda doc, args: None
            ):
                result = allocate_monthly_leave_bs(2080, 2, ["Casual Leave"], force=True, silent=True)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["count"], 1)

    def test_skip_if_already_allocated_and_silent(self):
        """Should skip allocation if already allocated and silent=True."""
        with self.patch_frappe():
            # Patch get_single_value to simulate last allocation same as current
            with patch("nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.frappe.db.get_single_value",
                       side_effect=[2080, 2]):
                result = allocate_monthly_leave_bs(2080, 2, ["Casual Leave"], force=False, silent=True)
                self.assertEqual(result["status"], "skipped")

    def test_throw_if_already_allocated_not_silent(self):
        """Should throw if already allocated, not silent, and not force."""
        with self.patch_frappe():
            with patch("nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.frappe.db.get_single_value",
                       side_effect=[2080, 2]):
                with self.assertRaises(Exception):
                    allocate_monthly_leave_bs(2080, 2, ["Casual Leave"], force=False, silent=False)

    def test_skip_if_no_leave_types(self):
        """Should skip if leave_types is empty"""
        with self.patch_frappe():
            result = allocate_monthly_leave_bs(2080, 2, leave_types=None, force=True, silent=True)
            self.assertEqual(result["status"], "skipped")

    def test_handles_exceptions_and_returns_error(self):
        """Should catch exceptions and return error without raising."""
        def raise_exception(*args, **kwargs):
            raise Exception("DB failure")

        with self.patch_frappe():
            # Patch create_leave_ledger_entry to raise exception
            with patch("nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.create_leave_ledger_entry",
                       side_effect=raise_exception):
                result = allocate_monthly_leave_bs(2080, 2, ["Casual Leave"], force=True, silent=True)
                self.assertEqual(result["status"], "error")
                self.assertIn("DB failure", result["error"])

if __name__ == "__main__":
    unittest.main()
