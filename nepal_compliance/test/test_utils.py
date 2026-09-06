import unittest

from nepal_compliance.utils import evaluate_tax_formula


class TestEvaluateTaxFormula(unittest.TestCase):
    def test_valid_formula_is_evaluated(self):
        self.assertEqual(evaluate_tax_formula("taxable_salary * 0.1", 1000), 100.0)

    def test_rejects_power_operator(self):
        # 9**9**9 would hang the worker if it reached safe_eval.
        with self.assertRaises(Exception):
            evaluate_tax_formula("9**9**9", 1000)

    def test_rejects_list_allocation(self):
        # [0]*999999999 would exhaust memory if it reached safe_eval.
        with self.assertRaises(Exception):
            evaluate_tax_formula("[0]*999999999", 1000)

    def test_rejects_overly_long_formula(self):
        with self.assertRaises(Exception):
            evaluate_tax_formula("1+" * 400, 1000)

    def test_rejects_empty_formula(self):
        with self.assertRaises(Exception):
            evaluate_tax_formula("   ", 1000)


if __name__ == "__main__":
    unittest.main()
