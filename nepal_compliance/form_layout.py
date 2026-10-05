"""Nepal Essentials tab: the fields a user fills on a transaction, first, with the rest in More Details.

The layout is one ``field_order`` property setter per doctype plus the tab, section and
column break custom fields it places. It is built from ESSENTIALS the first time, then
updated from the saved order on every migrate and whenever the setting changes: fields
moved in or out with Customize Form stay where they are, and a field that an ERPNext update
adds lands in More Details, never in Nepal Essentials.
"""

ESSENTIALS_TAB = "nc_essentials_tab"
MORE_DETAILS_TAB = "nc_more_details_tab"

# (key, label, depends_on, columns). A column is a list of fieldnames; fields missing from
# a site's doctype are skipped. Payment Entry sections copy the depends_on of ERPNext's own.
_DISCOUNT = ("discount", "Discount", None, [["additional_discount_percentage"], ["discount_amount"]])
_TOTALS = ("totals", "Totals", None, [["grand_total", "in_words"], ["rounded_total", "disable_rounded_total"]])
_ITEMS = ("items", None, None, [["items"]])
_SUMMARY = (
    "summary",
    "Taxable Summary",
    None,
    [["taxable_amount", "excise_amount", "non_taxable_amount"], ["vat_amount", "summary_grand_total"]],
)

ESSENTIALS = {
    "Sales Invoice": [
        (
            "party",
            "Customer and Date",
            None,
            [
                ["customer", "customer_name", "vat_number", "company", "manual_invoice_no", "reason"],
                ["posting_date", "due_date", "attach_sales_invoice"],
            ],
        ),
        _ITEMS,
        _DISCOUNT,
        _SUMMARY,
        _TOTALS,
    ],
    "Purchase Invoice": [
        (
            "party",
            "Supplier and Date",
            None,
            [
                ["supplier", "supplier_name", "vat_number", "company"],
                ["posting_date", "due_date", "is_pan_or_abbreviated_bill", "reason"],
            ],
        ),
        ("bill", "Supplier Invoice", None, [["bill_no", "attach_purchase_invoice"], ["bill_date", "apply_tds"]]),
        _ITEMS,
        _DISCOUNT,
        _SUMMARY,
        _TOTALS,
    ],
    "Sales Order": [
        (
            "party",
            "Customer and Dates",
            None,
            [["customer", "customer_name", "company"], ["transaction_date", "delivery_date"]],
        ),
        _ITEMS,
        _DISCOUNT,
        ("summary", "Taxable Summary", None, [["taxable_amount", "non_taxable_amount"], ["vat_amount", "summary_grand_total"]]),
        _TOTALS,
    ],
    "Purchase Order": [
        (
            "party",
            "Supplier and Dates",
            None,
            [["supplier", "supplier_name", "company"], ["transaction_date", "schedule_date", "is_pan_or_abbreviated_bill"]],
        ),
        _ITEMS,
        _DISCOUNT,
        _TOTALS,
    ],
    "Payment Entry": [
        ("payment", "Payment", None, [["payment_type", "mode_of_payment"], ["posting_date", "company"]]),
        (
            "party",
            "Party",
            'eval:in_list(["Receive", "Pay"], doc.payment_type)',
            [["party_type", "party"], ["party_name"]],
        ),
        ("accounts", "Accounts", None, [["paid_from"], ["paid_to"]]),
        (
            "amount",
            "Amount",
            "eval:(doc.paid_to && doc.paid_from)",
            [["paid_amount"], ["write_off_short_payment", "short_payment_write_off_account"]],
        ),
        (
            "customer_tds",
            "Customer TDS",
            "eval:doc.payment_type == 'Receive' && doc.party_type == 'Customer'",
            [["apply_customer_tds", "tds_receivable_account"], ["customer_tds_amount"]],
        ),
        (
            "references",
            "Reference",
            "eval:(doc.party && doc.paid_from && doc.paid_to && doc.paid_amount && doc.received_amount)",
            [["get_outstanding_invoices", "references"]],
        ),
        (
            "allocation",
            None,
            None,
            [["total_allocated_amount"], ["unallocated_amount", "difference_amount", "write_off_difference_amount"]],
        ),
        ("deductions", "Deductions or Loss", "eval:(doc.paid_amount && doc.received_amount)", [["deductions"]]),
        ("transaction", "Transaction ID", None, [["reference_no"], ["reference_date"]]),
    ],
}

# read-only amounts hidden while they are 0
HIDE_WHEN_ZERO = {
    "Sales Invoice": ["taxable_amount", "excise_amount", "non_taxable_amount", "vat_amount", "summary_grand_total", "rounded_total"],
    "Purchase Invoice": ["taxable_amount", "excise_amount", "non_taxable_amount", "vat_amount", "summary_grand_total", "rounded_total"],
    "Sales Order": ["taxable_amount", "non_taxable_amount", "vat_amount", "summary_grand_total", "rounded_total"],
    "Purchase Order": ["rounded_total"],
    "Payment Entry": ["customer_tds_amount", "unallocated_amount", "difference_amount"],
}

# a Nepal bill shows the discount before VAT, so VAT is worked out on the discounted amount
DEFAULTS = {
    doctype: {"apply_discount_on": "Net Total"}
    for doctype in ("Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order")
}


def section_fieldname(key, column=0):
    return f"nc_ess_{key}_section" if not column else f"nc_ess_{key}_col{column}"


def layout_fields(doctype):
    """Return the tab, section and column break custom fields of one doctype's layout, in order."""
    fields = [{"fieldname": ESSENTIALS_TAB, "fieldtype": "Tab Break", "label": "Nepal Essentials"}]
    for key, label, depends_on, columns in ESSENTIALS[doctype]:
        fields.append(
            {"fieldname": section_fieldname(key), "fieldtype": "Section Break", "label": label, "depends_on": depends_on}
        )
        fields += [{"fieldname": section_fieldname(key, i), "fieldtype": "Column Break"} for i in range(1, len(columns))]
    fields.append({"fieldname": MORE_DETAILS_TAB, "fieldtype": "Tab Break", "label": "More Details"})
    return fields


def natural_order(standard, custom_fields):
    """Order fields the way Frappe does without a field_order property setter.

    ``custom_fields`` are ``(fieldname, insert_after)`` pairs in their idx order.
    """
    order = list(standard)
    after = {}
    for fieldname, insert_after in custom_fields:
        if insert_after:
            after.setdefault(insert_after, []).append(fieldname)
        else:
            order.insert(0, fieldname)
    placed = True
    while placed:
        placed = False
        for anchor in list(after):
            if anchor in order:
                index = order.index(anchor)
                for offset, fieldname in enumerate(after.pop(anchor), 1):
                    order.insert(index + offset, fieldname)
                placed = True
    for fieldnames in after.values():
        order.extend(fieldnames)
    return order


def build_field_order(natural, sections, extras=()):
    """Return the full field order: Nepal Essentials, then everything else in ``natural`` order.

    ``sections`` is the doctype's ESSENTIALS entry. Each extra field goes straight after the
    nearest field before it in ``natural`` that is already in Nepal Essentials.
    """
    ours = {ESSENTIALS_TAB, MORE_DETAILS_TAB}
    for key, _label, _depends_on, columns in sections:
        ours.add(section_fieldname(key))
        ours.update(section_fieldname(key, i) for i in range(1, len(columns)))
    natural = [f for f in natural if f not in ours]
    present = set(natural)
    layout = [[[f for f in column if f in present] for column in columns] for _key, _l, _d, columns in sections]
    placed = {f for columns in layout for column in columns for f in column}

    for extra in sorted({f for f in extras if f in present and f not in placed}, key=natural.index):
        before = next((f for f in reversed(natural[: natural.index(extra)]) if f in placed), None)
        column = next((c for columns in layout for c in columns if before in c), None)
        if column is None:
            layout[0][0].insert(0, extra)
        else:
            column.insert(column.index(before) + 1, extra)
        placed.add(extra)

    order = [ESSENTIALS_TAB]
    for (key, _label, _depends_on, _columns), columns in zip(sections, layout):
        order.append(section_fieldname(key))
        for i, column in enumerate(columns):
            if i:
                order.append(section_fieldname(key, i))
            order += column
    order.append(MORE_DETAILS_TAB)
    return order + [f for f in natural if f not in placed]


def update_field_order(saved, natural, layout_names, extras=(), removed=()):
    """Rebuild from the saved order, keeping whatever a user moved in or out with Customize Form.

    A field missing from ``saved`` is new since it was written, from an ERPNext update or a
    new custom field, and goes to More Details after the nearest field before it in
    ``natural`` that is there too. Extra fields from the settings are moved into Nepal
    Essentials, and ``removed`` ones (taken off the settings list) are moved back out.
    """
    current = set(natural) | set(layout_names)
    order = [f for f in saved if f in current]

    def in_tab(fieldname):
        return order.index(fieldname) < order.index(MORE_DETAILS_TAB)

    def place(fieldname, inside):
        earlier = natural[: natural.index(fieldname)] if fieldname in natural else []
        before = next(
            (f for f in reversed(earlier) if f in order and in_tab(f) == inside and f not in layout_names), None
        )
        if before:
            order.insert(order.index(before) + 1, fieldname)
        elif inside:
            first = order[1] if len(order) > 1 and order[1] in layout_names and order[1].endswith("_section") else ESSENTIALS_TAB
            order.insert(order.index(first) + 1, fieldname)
        else:
            order.insert(order.index(MORE_DETAILS_TAB) + 1, fieldname)

    for fieldname in natural:
        if fieldname not in order:
            place(fieldname, inside=False)
    for fieldname in removed:
        if fieldname in order and in_tab(fieldname) and fieldname not in extras:
            order.remove(fieldname)
            place(fieldname, inside=False)
    for fieldname in sorted({f for f in extras if f in natural}, key=natural.index):
        if not in_tab(fieldname):
            order.remove(fieldname)
            place(fieldname, inside=True)
    return order


def hide_when_zero(depends_on, fieldname):
    """Add 'and the amount is not 0' to a field's own depends_on."""
    condition = f"flt(doc.{fieldname})"
    if not depends_on:
        return f"eval:{condition}"
    expression = depends_on[5:].strip() if depends_on.startswith("eval:") else f"doc.{depends_on.strip()}"
    return f"eval:({expression}) && {condition}"
