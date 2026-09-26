import unittest
from unittest.mock import patch

import frappe

from nepal_compliance import customer_tds


class FakePaymentEntry(frappe._dict):
    def get_doc_before_save(self):
        return self.get("_before")

    def precision(self, fieldname, parentfield=None):
        return 2

    def set(self, key, value):
        self[key] = value

    def append(self, key, value):
        self.setdefault(key, []).append(frappe._dict(value))


def ref(name, outstanding, allocated=0):
    return frappe._dict(
        reference_doctype="Sales Invoice", reference_name=name, outstanding_amount=outstanding, allocated_amount=allocated
    )


def payment(paid, references, deductions=None, apply=1):
    return FakePaymentEntry(
        name="PE-1",
        company="ACME",
        cost_center="Main - A",
        payment_type="Receive",
        party_type="Customer",
        paid_amount=paid,
        apply_customer_tds=apply,
        tds_receivable_account="TDS Receivable - A",
        references=references,
        deductions=deductions or [],
    )


class TestAllocateWithTds(unittest.TestCase):
    def test_full_payment_settles_invoice(self):
        rows = [ref("SINV-1", 113000)]
        self.assertEqual(customer_tds.allocate_with_tds(rows, 111500, {"SINV-1": 1500}), [(113000, 1500)])

    def test_partial_payment_books_full_tds(self):
        rows = [ref("SINV-1", 113000)]
        self.assertEqual(customer_tds.allocate_with_tds(rows, 50000, {"SINV-1": 1500}), [(51500, 1500)])

    def test_fifo_across_invoices(self):
        rows = [ref("SINV-1", 11300), ref("SINV-2", 22600)]
        result = customer_tds.allocate_with_tds(rows, 20000, {"SINV-1": 150, "SINV-2": 300})
        self.assertEqual(result, [(11300, 150), (9150, 300)])

    def test_invoice_without_cash_gets_no_tds(self):
        rows = [ref("SINV-1", 11300), ref("SINV-2", 22600)]
        result = customer_tds.allocate_with_tds(rows, 11150, {"SINV-1": 150, "SINV-2": 300})
        self.assertEqual(result, [(11300, 150), (0.0, 0.0)])


class TestCustomerTdsSettings(unittest.TestCase):
    @patch("nepal_compliance.customer_tds.frappe.get_cached_doc")
    def test_empty_rate_falls_back_to_default(self, get_cached_doc):
        row = frappe._dict(company="ACME", tds_receivable_account="TDS Receivable - A")
        get_cached_doc.return_value = frappe._dict(customer_tds_rate=0.0, vat_accounts=[row])
        self.assertEqual(customer_tds._customer_tds_settings("ACME"), (1.5, "TDS Receivable - A"))


@patch("nepal_compliance.customer_tds._tds_by_invoice")
class TestApplyCustomerTds(unittest.TestCase):
    def test_adds_deduction_and_raises_allocation(self, tds_by_invoice):
        tds_by_invoice.return_value = {"SINV-1": (1500, 1)}
        doc = payment(50000, [ref("SINV-1", 113000, 50000)])
        customer_tds.apply_customer_tds(doc)
        self.assertEqual(doc.references[0].allocated_amount, 51500)
        self.assertEqual(doc.references[0].customer_tds_amount, 1500)
        self.assertEqual([(d.account, d.amount) for d in doc.deductions], [("TDS Receivable - A", 1500)])
        self.assertEqual(doc.customer_tds_amount, 1500)

    def test_second_receipt_books_no_tds(self, tds_by_invoice):
        tds_by_invoice.return_value = {}
        doc = payment(61500, [ref("SINV-1", 61500, 61500)])
        customer_tds.apply_customer_tds(doc)
        self.assertEqual(doc.references[0].allocated_amount, 61500)
        self.assertEqual(doc.deductions, [])

    def test_write_off_row_counts_towards_settlement(self, tds_by_invoice):
        tds_by_invoice.return_value = {"SINV-1": (1500.41, 1)}
        write_off = frappe._dict(account="Write Off - A", amount=0.10)
        doc = payment(111530, [ref("SINV-1", 113030.51)], [write_off])
        customer_tds.apply_customer_tds(doc)
        self.assertEqual(doc.references[0].allocated_amount, 113030.51)
        self.assertEqual([d.account for d in doc.deductions], ["Write Off - A", "TDS Receivable - A"])

    def test_running_twice_keeps_one_tds_row(self, tds_by_invoice):
        tds_by_invoice.return_value = {"SINV-1": (1500, 1)}
        doc = payment(111500, [ref("SINV-1", 113000)])
        customer_tds.apply_customer_tds(doc)
        customer_tds.apply_customer_tds(doc)
        self.assertEqual(len(doc.deductions), 1)
        self.assertEqual(doc.references[0].allocated_amount, 113000)

    def test_unticking_removes_tds_and_reallocates_cash(self, tds_by_invoice):
        tds_by_invoice.return_value = {"SINV-1": (1500, 1)}
        doc = payment(50000, [ref("SINV-1", 113000)])
        customer_tds.apply_customer_tds(doc)
        doc.apply_customer_tds = 0
        customer_tds.apply_customer_tds(doc)
        self.assertEqual(doc.deductions, [])
        self.assertEqual(doc.references[0].allocated_amount, 50000)
        self.assertEqual(doc.customer_tds_amount, 0)

    def test_ignores_supplier_payments(self, tds_by_invoice):
        doc = payment(50000, [ref("SINV-1", 113000, 50000)])
        doc.party_type = "Supplier"
        customer_tds.apply_customer_tds(doc)
        tds_by_invoice.assert_not_called()
        self.assertEqual(doc.references[0].allocated_amount, 50000)


if __name__ == "__main__":
    unittest.main()
