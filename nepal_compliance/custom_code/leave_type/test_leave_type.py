import unittest
from unittest.mock import patch, MagicMock, ANY

# Import the module under test using the correct path
from nepal_compliance.custom_code.leave_type import leave_type

class TestLeaveType(unittest.TestCase):

    def setUp(self):
        # Create a mock document that behaves like a Frappe document
        self.mock_doc = MagicMock()
        self.mock_doc.save = MagicMock()

    # Test check_if_leave_type_exists
    @patch("nepal_compliance.custom_code.leave_type.leave_type.frappe.db.exists")
    def test_check_if_leave_type_exists_true(self, mock_exists):
        # Simulate leave type exists
        mock_exists.return_value = True
        result = leave_type.check_if_leave_type_exists("Annual Home Leave")
        self.assertTrue(result)
        mock_exists.assert_called_once_with("Leave Type", {"leave_type_name": "Annual Home Leave"})

    @patch("nepal_compliance.custom_code.leave_type.leave_type.frappe.db.exists")
    def test_check_if_leave_type_exists_false(self, mock_exists):
        # Simulate leave type does not exist
        mock_exists.return_value = None
        result = leave_type.check_if_leave_type_exists("Nonexistent Leave")
        self.assertIsNone(result)
        mock_exists.assert_called_once_with("Leave Type", {"leave_type_name": "Nonexistent Leave"})

    # Test create_leave_type
    @patch("nepal_compliance.custom_code.leave_type.leave_type.frappe.new_doc")
    def test_create_leave_type_sets_fields_and_saves(self, mock_new_doc):
        mock_new_doc.return_value = self.mock_doc

        doc = leave_type.create_leave_type(
            leave_type_name="Test Leave",
            max_leaves_allowed=10,
            applicable_after=30
        )
        mock_new_doc.assert_called_once_with("Leave Type")

        # Check fields are set
        self.assertEqual(self.mock_doc.leave_type_name, "Test Leave")
        self.assertEqual(self.mock_doc.max_leaves_allowed, 10)
        self.assertEqual(self.mock_doc.applicable_after, 30)

        # Ensure save was called
        self.mock_doc.save.assert_called_once()
        self.assertEqual(doc, self.mock_doc)

    # Test setup_default_leave_types
    @patch("nepal_compliance.custom_code.leave_type.leave_type.create_leave_type")
    @patch("nepal_compliance.custom_code.leave_type.leave_type.check_if_leave_type_exists")
    @patch("nepal_compliance.custom_code.leave_type.leave_type.frappe.msgprint")
    def test_setup_default_leave_types_creates_new(self, mock_msg, mock_exists, mock_create):
        # Simulate leave types do not exist
        mock_exists.return_value = None

        leave_type.setup_default_leave_types()

        # Ensure create_leave_type called for both default leave types
        self.assertEqual(mock_create.call_count, 2)
        # Check only the arguments actually passed
        mock_create.assert_any_call(
            leave_type_name="Annual Home Leave",
            max_leaves_allowed="18",
            applicable_after="20",
            allocate_on_day="First Day"
        )
        mock_create.assert_any_call(
            leave_type_name="Annual Sick Leave",
            max_leaves_allowed="12",
            applicable_after="20",
            max_continuous_days_allowed="3",
            is_carry_forward=1,
            maximum_carry_forwarded_leaves="45",
            allow_encashment=1,
            max_encashable_leaves="45",
            earning_component="Basic Salary",
            allocate_on_day="Last Day"
        )

        # Ensure msgprint called for both creations
        self.assertEqual(mock_msg.call_count, 2)
        mock_msg.assert_any_call("Created new leave type: Annual Home Leave")
        mock_msg.assert_any_call("Created new leave type: Annual Sick Leave")

    @patch("nepal_compliance.custom_code.leave_type.leave_type.create_leave_type")
    @patch("nepal_compliance.custom_code.leave_type.leave_type.check_if_leave_type_exists")
    @patch("nepal_compliance.custom_code.leave_type.leave_type.frappe.msgprint")
    def test_setup_default_leave_types_skips_existing(self, mock_msg, mock_exists, mock_create):
        # Simulate leave types already exist
        mock_exists.return_value = True

        leave_type.setup_default_leave_types()

        # create_leave_type should NOT be called
        mock_create.assert_not_called()
        # msgprint should show skipping messages
        mock_msg.assert_any_call("Leave type Annual Home Leave already exists, skipping creation")
        mock_msg.assert_any_call("Leave type Annual Sick Leave already exists, skipping creation")

if __name__ == "__main__":
    unittest.main()
