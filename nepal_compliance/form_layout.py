"""Nepal Essentials tab: the fields a user fills on a transaction, first, with the rest in More Details.

The layout is one ``field_order`` property setter per doctype plus the tab, section and
column break custom fields it places. It is built from ESSENTIALS the first time, then
updated from the saved order on every migrate and whenever the setting changes: fields
moved in or out with Customize Form stay where they are, and a field that an ERPNext update
adds lands in More Details, never in Nepal Essentials.
"""

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.utils import cint

ESSENTIALS_TAB = "nc_essentials_tab"
BILL_SUMMARY = "bill_summary"
MORE_DETAILS_TAB = "nc_more_details_tab"
BREAK_TYPES = ("Tab Break", "Section Break", "Column Break")
NOT_ADDABLE = BREAK_TYPES + ("HTML", "Fold", "Heading")

# (key, label, depends_on, columns). A column is a list of fieldnames; fields missing from
# a site's doctype are skipped. Payment Entry sections copy the depends_on of ERPNext's own.
_ITEMS = ("items", None, None, [["items"]])
# laid out like a Nepal bill: the figures in the order they are printed, the inputs beside them
_BILL_INPUTS = ["additional_discount_percentage", "discount_amount", "in_words", "disable_rounded_total"]
_BILL_TOTALS = ["summary_grand_total", "grand_total", "rounded_total"]
# Subtotal and Discount are the printed bill's: only a taxable item's discount is shown as Discount
_BILL = (BILL_SUMMARY, "Bill Summary", None, [_BILL_INPUTS, ["bill_subtotal", "excise_amount", "taxable_discount", "non_taxable_amount", "taxable_amount", "vat_amount"] + _BILL_TOTALS])

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
        _BILL,
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
        _BILL,
    ],
    "Sales Order": [
        (
            "party",
            "Customer and Dates",
            None,
            [["customer", "customer_name", "company"], ["transaction_date", "delivery_date"]],
        ),
        _ITEMS,
        (BILL_SUMMARY, "Bill Summary", None, [_BILL_INPUTS, ["bill_subtotal", "taxable_discount", "non_taxable_amount", "taxable_amount", "vat_amount"] + _BILL_TOTALS]),
    ],
    "Purchase Order": [
        (
            "party",
            "Supplier and Dates",
            None,
            [["supplier", "supplier_name", "company"], ["transaction_date", "schedule_date", "is_pan_or_abbreviated_bill"]],
        ),
        _ITEMS,
        (BILL_SUMMARY, "Bill Summary", None, [_BILL_INPUTS, ["total", "total_taxes_and_charges", "grand_total", "rounded_total"]]),
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

# read-only figures shown only when the condition holds, by default while they are not 0
_SHOWN_WHEN_SET = dict.fromkeys(["taxable_discount", "non_taxable_amount", "taxable_amount", "vat_amount", "summary_grand_total", "rounded_total"])
# ERPNext's Grand Total differs from the Bill Total by TDS withheld on a purchase
_GRAND_TOTAL = {"grand_total": "flt(doc.grand_total) != flt(doc.summary_grand_total)"}
# folded excise sits on the item rows and inside Subtotal, so only licensed excise gets a line
_EXCISE = {"excise_amount": "flt(doc.excise_amount) && !(doc.items || []).some((d) => flt(d.excise_amount))"}
SHOW_WHEN = {
    "Sales Invoice": {**_EXCISE, **_SHOWN_WHEN_SET, **_GRAND_TOTAL},
    "Purchase Invoice": {**_EXCISE, **_SHOWN_WHEN_SET, **_GRAND_TOTAL},
    "Sales Order": {**_SHOWN_WHEN_SET, **_GRAND_TOTAL},
    "Purchase Order": dict.fromkeys(["total_taxes_and_charges", "rounded_total"]),
    "Payment Entry": dict.fromkeys(["customer_tds_amount", "unallocated_amount", "difference_amount"]),
}

# a Nepal bill shows the discount before VAT, so VAT is worked out on the discounted amount
_BILL_DOCTYPES = ("Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order")
DEFAULTS = {doctype: {"apply_discount_on": "Net Total"} for doctype in _BILL_DOCTYPES}
# the wording of a Nepal bill; the VAT line is labelled with its rate by bill_summary.js
LABELS = {
    doctype: {"discount_amount": "Discount Amount", "additional_discount_percentage": "Discount %"}
    for doctype in _BILL_DOCTYPES
}
# raised whenever ESSENTIALS changes, so a site built from an older layout is rebuilt at migrate
LAYOUT_VERSION = 3


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
    bill = next((i for i, section in enumerate(sections) if section[0] == BILL_SUMMARY), None)

    for extra in sorted({f for f in extras if f in present and f not in placed}, key=natural.index):
        before = next((f for f in reversed(natural[: natural.index(extra)]) if f in placed), None)
        column = next((c for columns in layout for c in columns if before in c), None)
        if column is None:
            layout[0][0].insert(0, extra)
        elif bill and column is layout[bill][-1]:
            # the bill's figures stay as printed; anything else goes under the section above
            layout[bill - 1][-1].append(extra)
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

    def in_bill_figures(fieldname):
        """Whether ``fieldname`` is in the Bill Summary's last column, which keeps its printed order."""
        breaks = [i for i, f in enumerate(order) if f in layout_names]
        starts = [i for i in breaks if order[i].startswith(f"nc_ess_{BILL_SUMMARY}_col")]
        if not starts:
            return False
        end = next((i for i in breaks if i > starts[-1]), len(order))
        return starts[-1] < order.index(fieldname) < end

    def place(fieldname, inside):
        earlier = natural[: natural.index(fieldname)] if fieldname in natural else []
        before = next(
            (f for f in reversed(earlier) if f in order and in_tab(f) == inside and f not in layout_names), None
        )
        if before and inside and in_bill_figures(before):
            order.insert(order.index(section_fieldname(BILL_SUMMARY)), fieldname)
        elif before:
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


def rebuild_field_order(saved, natural, sections, extras=(), removed=()):
    """Build from a newer ESSENTIALS, keeping the fields a user had moved into the tab."""
    built_in = {f for _key, _label, _depends_on, columns in sections for column in columns for f in column}
    tab = saved[saved.index(ESSENTIALS_TAB) : saved.index(MORE_DETAILS_TAB)]
    kept = [f for f in tab if f in natural and f not in built_in and f not in removed]
    return build_field_order(natural, sections, list(extras) + kept)


def show_when(depends_on, fieldname, condition=None):
    """Add ``condition``, by default 'and the amount is not 0', to a field's own depends_on."""
    condition = condition or f"flt(doc.{fieldname})"
    if not depends_on:
        return f"eval:{condition}"
    expression = depends_on[5:].strip() if depends_on.startswith("eval:") else f"doc.{depends_on.strip()}"
    return f"eval:({expression}) && {condition}"


def get_extra_field_candidates(doctype):
    """Return {fieldname: label} of the fields a site may add to Nepal Essentials."""
    if doctype not in ESSENTIALS:
        return {}
    taken = {f for _key, _label, _depends_on, columns in ESSENTIALS[doctype] for column in columns for f in column}
    taken |= {f["fieldname"] for f in layout_fields(doctype)}
    return {
        df.fieldname: _(df.label or df.fieldname)
        for df in frappe.get_meta(doctype).fields
        if df.fieldname not in taken and df.fieldtype not in NOT_ADDABLE and not df.hidden
    }


@frappe.whitelist()
def get_extra_field_options(doctype: str) -> list:
    """Return the fields a site may add to Nepal Essentials, required ones first, for the settings form."""
    frappe.has_permission("Nepal Compliance Settings", "write", throw=True)
    required = {f["fieldname"]: f["reason"] for f in _required_fields(doctype, _mandatory_dimensions(), set())}
    options = [
        {"value": f, "label": f"{label} ({f})", "description": _("Required: {0}").format(required[f]) if f in required else None}
        for f, label in get_extra_field_candidates(doctype).items()
    ]
    return sorted(options, key=lambda option: (option["value"] not in required, option["label"]))


def pick_required_fields(reasons, candidates, in_tab, meta_fields):
    """Keep the required fields a user must enter that are not in Nepal Essentials yet.

    ``reasons`` maps a fieldname to why it is required, ``candidates`` is
    get_extra_field_candidates() and ``meta_fields`` maps a fieldname to its docfield.
    A read-only field or one with a default is filled without the user.
    """
    return [
        {"fieldname": fieldname, "label": candidates[fieldname], "reason": reason}
        for fieldname, reason in reasons.items()
        if fieldname in candidates
        and fieldname not in in_tab
        and not meta_fields[fieldname].read_only
        and not meta_fields[fieldname].default
    ]


@frappe.whitelist()
def get_required_fields() -> list:
    """Return the fields this site made required that are not in Nepal Essentials, for the settings form.

    ERPNext's own required fields are left out: it fills them itself (series, currency,
    price list, party account, exchange rates).
    """
    frappe.has_permission("Nepal Compliance Settings", "write", throw=True)
    settings = frappe.get_single("Nepal Compliance Settings")
    extras = {}
    for row in settings.get("essentials_extra_fields") or []:
        extras.setdefault(row.document_type, []).append(row.fieldname)

    dimensions = _mandatory_dimensions()
    return [
        dict(field, doctype=doctype, dimension=field["fieldname"] in dimensions)
        for doctype in ESSENTIALS
        for field in _required_fields(doctype, dimensions, _tab_fields(doctype, extras.get(doctype, [])))
    ]


def _mandatory_dimensions():
    """Fieldnames of the enabled accounting dimensions that are mandatory for some company."""
    mandatory = frappe.get_all(
        "Accounting Dimension Detail",
        filters={"parenttype": "Accounting Dimension"},
        or_filters={"mandatory_for_bs": 1, "mandatory_for_pl": 1},
        pluck="parent",
    )
    if not mandatory:
        return []
    return frappe.get_all("Accounting Dimension", filters={"name": ["in", mandatory], "disabled": 0}, pluck="fieldname")


def _required_fields(doctype, dimensions, in_tab):
    """The fields this site made required on ``doctype`` that a user must enter, outside ``in_tab``."""
    reasons = dict.fromkeys(dimensions, _("Mandatory accounting dimension"))
    for fieldname in frappe.get_all("Custom Field", filters={"dt": doctype, "reqd": 1}, pluck="fieldname"):
        reasons.setdefault(fieldname, _("Required custom field"))
    for fieldname in frappe.get_all(
        "Property Setter", filters={"doc_type": doctype, "property": "reqd", "value": "1"}, pluck="field_name"
    ):
        reasons.setdefault(fieldname, _("Required in Customize Form"))
    meta_fields = {df.fieldname: df for df in frappe.get_meta(doctype).fields}
    return pick_required_fields(reasons, get_extra_field_candidates(doctype), in_tab, meta_fields)


def apply_form_layout(settings=None, removed=None):
    """Build, update or remove the Nepal Essentials tab on every supported doctype (after_migrate).

    ``removed`` maps a doctype to the extra fields just taken off the settings list.
    """
    settings = settings or frappe.get_single("Nepal Compliance Settings")
    enabled = cint(settings.get("use_nepal_essentials_tab"))
    extras = {}
    for row in settings.get("essentials_extra_fields") or []:
        extras.setdefault(row.document_type, []).append(row.fieldname)

    # a site built from an older ESSENTIALS is rebuilt from the current one, once
    upgrade = cint(settings.get("essentials_layout_version")) < LAYOUT_VERSION
    for doctype in ESSENTIALS:
        if enabled:
            _apply(doctype, extras.get(doctype, []), (removed or {}).get(doctype, []), upgrade)
        elif frappe.db.exists("Custom Field", f"{doctype}-{ESSENTIALS_TAB}"):
            # only undo a layout this app built; never touch a site's own Customize Form order
            _remove(doctype)
        frappe.clear_cache(doctype=doctype)
    if enabled and upgrade:
        frappe.db.set_single_value("Nepal Compliance Settings", "essentials_layout_version", LAYOUT_VERSION)


def _apply(doctype, extras, removed=(), upgrade=False):
    ours = layout_fields(doctype)
    names = {f["fieldname"] for f in ours}
    standard = frappe.get_all(
        "DocField",
        filters={"parent": doctype, "parenttype": "DocType", "parentfield": "fields"},
        order_by="idx asc",
        pluck="fieldname",
    )
    rows = frappe.get_all("Custom Field", filters={"dt": doctype}, fields=["fieldname", "insert_after"], order_by="idx asc")
    # breaks of a section a later version of this layout dropped would otherwise land anywhere
    stale = [row.fieldname for row in rows if row.fieldname.startswith("nc_ess_") and row.fieldname not in names]
    if stale:
        frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": ["in", stale]})
    custom = [(row.fieldname, row.insert_after) for row in rows if row.fieldname not in names and row.fieldname not in stale]
    natural = natural_order(standard, custom)
    existing = {row.fieldname for row in rows if row.fieldname in names}
    saved = _saved_order(doctype)
    # built from ESSENTIALS the first time, or again when the saved order or a tab is gone
    fresh = not (saved and {ESSENTIALS_TAB, MORE_DETAILS_TAB} <= set(saved) & existing)
    if fresh:
        order = build_field_order(natural, ESSENTIALS[doctype], extras)
    elif upgrade:
        order = rebuild_field_order(saved, natural, ESSENTIALS[doctype], extras, removed)
    else:
        order = update_field_order(saved, natural, names, extras, removed)
    rebuilt = fresh or upgrade

    # after a build only missing breaks are created, so a renamed tab or section keeps its name;
    # insert_after keeps them in place even before the field_order property setter lands
    to_save = [f for f in ours if rebuilt or (f["fieldname"] in order and f["fieldname"] not in existing)]
    for field in to_save:
        field["insert_after"] = order[order.index(field["fieldname"]) - 1] if order[0] != field["fieldname"] else None
    _save_layout_fields(doctype, to_save)

    _set_property(doctype, None, "field_order", frappe.as_json(order, indent=None))
    # likewise a depends_on, default or label changed with Customize Form is left as the user set it
    for fieldname, condition in SHOW_WHEN[doctype].items():
        if fieldname in order and (rebuilt or not _has_property(doctype, fieldname, "depends_on")):
            depends_on = show_when(_original(doctype, fieldname, "depends_on"), fieldname, condition)
            _set_property(doctype, fieldname, "depends_on", depends_on)
    for prop, values in (("default", DEFAULTS), ("label", LABELS)):
        for fieldname, value in values.get(doctype, {}).items():
            if fieldname in order and (rebuilt or not _has_property(doctype, fieldname, prop)):
                _set_property(doctype, fieldname, prop, value)


def _remove(doctype):
    delete_property_setter(doctype, "field_order")
    for fieldname in SHOW_WHEN[doctype]:
        delete_property_setter(doctype, "depends_on", fieldname)
    for prop, values in (("default", DEFAULTS), ("label", LABELS)):
        for fieldname in values.get(doctype, {}):
            delete_property_setter(doctype, prop, fieldname)
    # deleted directly: Custom Field's on_trash lets only Administrator delete fields it owns,
    # and a Settings writer turns the tab off. The breaks have no database column.
    names = [f["fieldname"] for f in layout_fields(doctype)]
    frappe.db.delete("Property Setter", {"doc_type": doctype, "field_name": ["in", names]})
    frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": ["in", names]})


def _save_layout_fields(doctype, fields):
    """Create or update the layout's break fields without a permission check or schema sync."""
    frappe.flags.in_create_custom_fields = True
    try:
        for field in fields:
            name = f"{doctype}-{field['fieldname']}"
            if frappe.db.exists("Custom Field", name):
                doc = frappe.get_doc("Custom Field", name)
                if all((doc.get(key) or None) == (value or None) for key, value in field.items()):
                    continue
                doc.update(field)
            else:
                doc = frappe.get_doc({"doctype": "Custom Field", "dt": doctype, "is_system_generated": 1, **field})
            doc.flags.ignore_permissions = True
            doc.flags.ignore_validate = True
            doc.save()
    finally:
        frappe.flags.in_create_custom_fields = False


def _saved_order(doctype):
    """The doctype's saved field_order, whether this app or Customize Form wrote it last."""
    value = frappe.db.get_value(
        "Property Setter", {"doc_type": doctype, "property": "field_order", "doctype_or_field": "DocType"}, "value"
    )
    order = frappe.parse_json(value) if value else None
    return order if isinstance(order, list) else None


def _tab_fields(doctype, extras):
    """The fields in a doctype's Nepal Essentials tab now, or the ones it will get once built."""
    saved = _saved_order(doctype)
    if saved and ESSENTIALS_TAB in saved and MORE_DETAILS_TAB in saved:
        return set(saved[saved.index(ESSENTIALS_TAB) : saved.index(MORE_DETAILS_TAB)])
    return {f for _key, _label, _depends_on, columns in ESSENTIALS[doctype] for column in columns for f in column} | set(extras)


def _has_property(doctype, fieldname, prop):
    return bool(frappe.db.exists("Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": prop}))


def _original(doctype, fieldname, prop):
    """A field's own value for ``prop``, ignoring property setters (including ours)."""
    value = frappe.db.get_value("DocField", {"parent": doctype, "parenttype": "DocType", "fieldname": fieldname}, prop)
    if value is None:
        value = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, prop)
    return value


def _set_property(doctype, fieldname, prop, value):
    """Create or update one property setter, skipping the write when it already holds ``value``."""
    filters = {"doc_type": doctype, "property": prop}
    filters.update({"field_name": fieldname} if fieldname else {"doctype_or_field": "DocType"})
    if frappe.db.get_value("Property Setter", filters, "value") == value:
        return
    make_property_setter(
        doctype,
        fieldname,
        prop,
        value,
        "Code" if prop == "depends_on" else "Data" if prop == "field_order" else "Text",
        for_doctype=not fieldname,
        validate_fields_for_doctype=False,
    )
