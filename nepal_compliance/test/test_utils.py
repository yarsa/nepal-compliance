import unittest
from unittest.mock import patch

from nepal_compliance.utils import MAX_TAX_FORMULA_LENGTH, evaluate_tax_formula

# The default income tax slab formula that setup writes to the Income Tax
# salary component (see custom_code/payroll/salary_component.py). It is longer
# than 500 characters, so any length limit has to leave room for it.
DEFAULT_TAX_FORMULA = (
    "((((taxable_salary) * 12) * 0.01)/12) if ((taxable_salary) * 12) <= 1000000 "
    "else (((1000000 * 0.01) + (((taxable_salary) * 12) - 1000000) * 0.1)/12) "
    "if ((taxable_salary) * 12) <= 1500000 "
    "else (((1000000*0.01) + (500000*0.1) + (((taxable_salary)*12) - 1500000) * 0.2)/12) "
    "if ((taxable_salary)*12) <= 2500000 "
    "else (((1000000*0.01) + (500000*0.1) + (1000000*0.2) + ((taxable_salary)*12 - 2500000) *0.27)/12) "
    "if ((taxable_salary)*12)<=4000000 "
    "else (((1000000*0.01) + (500000*0.1) + (1000000*0.2) + (1500000*0.27) + ((taxable_salary)*12 - 4000000)*0.29)/12) "
    "if ((taxable_salary)*12)>4000000 else 0"
)


class TestEvaluateTaxFormula(unittest.TestCase):
    def test_valid_formula_is_evaluated(self):
        self.assertEqual(evaluate_tax_formula("taxable_salary * 0.1", 1000), 100.0)

    def test_default_slab_formula_is_accepted(self):
        self.assertGreater(len(DEFAULT_TAX_FORMULA), 500)
        # 150000 a month is 1800000 a year, which falls in the 20 percent slab.
        self.assertEqual(evaluate_tax_formula(DEFAULT_TAX_FORMULA, 150000), 10000.0)

    def assert_rejected_before_eval(self, formula, message):
        with patch("nepal_compliance.utils.safe_eval") as mock_safe_eval:
            with self.assertRaisesRegex(Exception, message):
                evaluate_tax_formula(formula, 1000)
        mock_safe_eval.assert_not_called()

    def test_rejects_power_operator(self):
        self.assert_rejected_before_eval("9**9**9", "not allowed")

    def test_rejects_shift_operator(self):
        self.assert_rejected_before_eval("1 << 9999999999", "not allowed")

    def test_rejects_tuple_allocation(self):
        self.assert_rejected_before_eval("(0,)*999999999", "not allowed")

    def test_rejects_list_allocation(self):
        self.assert_rejected_before_eval("[0]*999999999", "not allowed")

    def test_rejects_string_repetition(self):
        self.assert_rejected_before_eval("'a'*999999999", "not allowed")

    def test_rejects_attribute_access(self):
        self.assert_rejected_before_eval("taxable_salary.__class__", "not allowed")

    def test_rejects_function_call(self):
        self.assert_rejected_before_eval("max(taxable_salary, 0)", "not allowed")

    def test_rejects_overly_long_formula(self):
        formula = "1+" * MAX_TAX_FORMULA_LENGTH + "1"
        self.assert_rejected_before_eval(formula, "too long")

    def test_rejects_invalid_expression(self):
        self.assert_rejected_before_eval("taxable_salary *", "not a valid expression")

    def test_rejects_empty_formula(self):
        self.assert_rejected_before_eval("   ", "missing")


if __name__ == "__main__":
    unittest.main()
