import frappe
from frappe import _
from frappe.utils import cint, flt

DEFAULT_CUSTOMER_TDS_RATE = 1.5


def _customer_tds_settings(company):
    """Return (rate, TDS Receivable Account) for one company."""
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    rate = settings.get("customer_tds_rate")
    account = next(
        (row.get("tds_receivable_account") for row in settings.get("vat_accounts") or [] if row.company == company),
        None,
    )
    return (DEFAULT_CUSTOMER_TDS_RATE if rate is None else flt(rate)), account


@frappe.whitelist()
def get_customer_tds_defaults(company: str | None = None, customer: str | None = None) -> dict:
    """Return one customer's TDS defaults, for the Payment Entry form."""
    rate, account = _customer_tds_settings(company)
    deducts = 0
    if customer:
        frappe.has_permission("Customer", "read", customer, throw=True)
        deducts = cint(frappe.db.get_value("Customer", customer, "deduct_tds_on_receipt"))
    return {"apply": deducts, "account": account, "rate": rate}


def allocate_with_tds(rows, pool, tds_by_invoice, precision=2):
    """Spread the cash ``pool`` over invoice rows in order, adding each invoice's withheld TDS.

    The withheld TDS settles part of an invoice without cash, so an invoice that receives
    any cash is allocated that cash plus its TDS. The TDS goes on the first such row of each
    invoice only. Returns one ``(allocated, tds)`` pair per row; cash left over stays unallocated.
    """
    result, applied = [], set()
    for row in rows:
        outstanding = flt(row.outstanding_amount, precision)
        tds = 0.0
        if row.reference_name not in applied:
            tds = min(flt(tds_by_invoice.get(row.reference_name), precision), outstanding)
        take = max(min(pool, flt(outstanding - tds, precision)), 0)
        if take <= 0:
            result.append((0.0, 0.0))
            continue
        if tds:
            applied.add(row.reference_name)
        pool = flt(pool - take, precision)
        result.append((flt(take + tds, precision), tds))
    return result


def _tds_by_invoice(doc, names, precision):
    """Return {invoice: (tds, conversion_rate)} for invoices whose TDS is still to be booked."""
    rate, _account = _customer_tds_settings(doc.company)
    booked = set(
        frappe.get_all(
            "Payment Entry Reference",
            filters={
                "reference_doctype": "Sales Invoice",
                "reference_name": ["in", names],
                "docstatus": 1,
                "parent": ["!=", doc.name or ""],
                "customer_tds_amount": [">", 0],
            },
            pluck="reference_name",
        )
    )
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={"name": ["in", names]},
        fields=["name", "is_return", "receive_without_tds", "taxable_amount", "conversion_rate"],
    )
    return {
        inv.name: (flt(flt(inv.taxable_amount) * rate / 100, precision), flt(inv.conversion_rate) or 1)
        for inv in invoices
        if not (inv.is_return or inv.receive_without_tds or inv.name in booked)
    }


def apply_customer_tds(doc, method=None):
    """Book the TDS a customer withheld as a Payment Entry deduction (before_validate).

    Runs before ERPNext's validate so its own totals and difference amount include the
    deduction. Only the first submitted receipt against an invoice books that invoice's TDS.
    """
    if doc.get("payment_type") != "Receive" or doc.get("party_type") != "Customer":
        return

    before = doc.get_doc_before_save()
    tds_accounts = {doc.get("tds_receivable_account"), before and before.get("tds_receivable_account")} - {None, ""}
    deductions = doc.get("deductions") or []
    kept = [d for d in deductions if d.account not in tds_accounts]
    removed = len(kept) != len(deductions)
    doc.set("deductions", kept)
    for idx, row in enumerate(kept, 1):
        row.idx = idx

    references = doc.get("references") or []
    for row in references:
        row.customer_tds_amount = 0
    doc.customer_tds_amount = 0
    rows = [r for r in references if r.reference_doctype == "Sales Invoice" and flt(r.outstanding_amount) > 0]
    apply = cint(doc.get("apply_customer_tds")) and doc.get("tds_receivable_account")
    if not rows or not (apply or removed):
        return

    precision = cint(doc.precision("allocated_amount", "references")) or 2
    tds_by_invoice = _tds_by_invoice(doc, list({r.reference_name for r in rows}), precision) if apply else {}

    row_ids = {id(r) for r in rows}
    exchange_rate = flt(doc.get("source_exchange_rate")) or 1
    pool = flt(doc.paid_amount) + sum(flt(d.amount) for d in kept if not d.get("is_exchange_gain_loss")) / exchange_rate
    pool -= sum(flt(r.allocated_amount) for r in references if id(r) not in row_ids)

    amounts = {name: tds for name, (tds, _rate) in tds_by_invoice.items()}
    total, invoices = 0.0, []
    for row, (allocated, tds) in zip(rows, allocate_with_tds(rows, flt(pool, precision), amounts, precision)):
        row.allocated_amount = allocated
        if tds:
            row.customer_tds_amount = flt(tds * tds_by_invoice[row.reference_name][1], precision)
            total += row.customer_tds_amount
            invoices.append(row.reference_name)

    doc.customer_tds_amount = flt(total, precision)
    if total:
        doc.append(
            "deductions",
            {
                "account": doc.tds_receivable_account,
                "cost_center": doc.get("cost_center") or frappe.get_cached_value("Company", doc.company, "cost_center"),
                "amount": doc.customer_tds_amount,
                "description": _("TDS withheld by customer on {0}").format(", ".join(invoices)),
            },
        )


@frappe.whitelist()
def calculate_customer_tds(doc: str | dict) -> dict:
    """Net the customer's withheld TDS off a draft Payment Entry's paid amount, for the form.

    Paid amount plus the TDS already netted off is what the receipt settles, so the TDS is
    handed back first and the new TDS taken off after: ticking Apply Customer TDS lowers the
    paid amount by the TDS, unticking restores it, and calling it again changes nothing.
    """
    doc = frappe.get_doc(frappe.parse_json(doc))
    doc.check_permission("create" if doc.is_new() else "write")
    exchange_rate = flt(doc.get("source_exchange_rate")) or 1
    precision = doc.precision("paid_amount")
    doc.paid_amount = flt(flt(doc.paid_amount) + flt(doc.customer_tds_amount) / exchange_rate, precision)
    apply_customer_tds(doc)
    doc.paid_amount = flt(flt(doc.paid_amount) - flt(doc.customer_tds_amount) / exchange_rate, precision)
    doc.set_amounts()
    return doc.as_dict()
