import json
import frappe
from frappe import _
from frappe.utils import flt, get_link_to_form
from frappe.utils.safe_exec import safe_eval
from frappe.model.naming import make_autoname
from typing import Union

def prevent_invoice_deletion(doc, method):
    if (doc.docstatus == 1):
        frappe.throw(_(f"Deletion of {doc.name} is not allowed due to compliance rule."))

def custom_autoname(doc, method):
    try:
        full_series = doc.naming_series
        if not full_series:
            naming_field = frappe.get_meta(doc.doctype).get_field("naming_series")
            if naming_field and naming_field.options:
                options = [opt.strip() for opt in naming_field.options.split("\n") if opt.strip()]
                if options:
                    full_series = options[0]
                else:
                    frappe.throw(_("No valid naming series found for {0}").format(doc.doctype))
            else:
                frappe.throw(_("No naming series found for {0}").format(doc.doctype))
        max_attempts = 50
        for attempt in range(max_attempts):
            proposed_name = make_autoname(full_series, doc=doc)
            if not proposed_name:
                frappe.throw(_("Failed to generate name using series {0}").format(full_series))
             
            if not frappe.db.exists(doc.doctype, proposed_name):
                doc.name = proposed_name
                return

        frappe.throw(_("Could not generate unique name after {0} attempts").format(max_attempts))
    except Exception as e:
        frappe.log_error(f"Custom autoname error: {str(e)}")
        raise

@frappe.whitelist()
def evaluate_tax_formula(formula: str, taxable_salary: Union[str, float]) -> float:
    try:
        taxable_salary = flt(taxable_salary)
        context = {
            'taxable_salary': taxable_salary,
            'if': lambda x, y, z: y if x else z
        }

        # Formula is evaluated using frappe safe_eval
        # nosemgrep: frappe-semgrep-rules.rules.security.frappe-codeinjection-eval
        result = safe_eval(formula, {"__builtins__": {}}, context)
        return flt(result)
    except Exception as e:
        frappe.throw(_("Invalid tax formula: {0}. Payroll calculation stopped. Please fix the formula.").format(str(e)))

def set_vat_numbers(doc, method):
    if doc.get("__islocal") and doc.is_opening == "Yes":
        if doc.doctype == "Purchase Invoice":
            if doc.supplier and not doc.vat_number:
                try:
                    supplier_vat = frappe.db.get_value("Supplier", doc.supplier, "supplier_vat_number")
                    if supplier_vat:
                        doc.vat_number = supplier_vat
                except Exception as e:
                    frappe.log_error(f"Error fetching supplier VAT: {str(e)}")
            if doc.company and not doc.customer_vat_number:
                try:
                    company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                    if company_vat:
                        doc.customer_vat_number = company_vat
                except Exception as e:
                    frappe.log_error(f"Error fetching company VAT: {str(e)}")
        elif doc.doctype == "Sales Invoice":
            if doc.customer and not doc.vat_number:
                customer_vat = frappe.db.get_value("Customer", doc.customer, "customer_vat_number")
                if customer_vat:
                    doc.vat_number = customer_vat
            if doc.company and not doc.supplier_vat_number:
                company_vat = frappe.db.get_value("Company", doc.company, "company_vat_number")
                if company_vat:
                    doc.supplier_vat_number = company_vat

def load_nepali_date(doc, method):
    if not hasattr(doc, "nepali_date"):
        return

    ad_field = "posting_date" if hasattr(doc, "posting_date") else (
        "transaction_date" if hasattr(doc, "transaction_date") else None
    )
    if not ad_field:
        return

    ad_value = doc.get(ad_field)
    if not ad_value:
        doc.nepali_date = None
        return

    from nepal_compliance.nepali_date_utils.utils import bs_date, nepal_compliance_enabled

    if not nepal_compliance_enabled():
        return

    bs = bs_date(ad_value)
    # bs_date() returns the input unchanged when conversion is skipped or fails;
    # only store the result when it actually differs from the AD value.
    if bs and str(bs).strip() != str(ad_value).strip():
        doc.nepali_date = str(bs).strip()

def bill_no_required(doc, method):
    if doc.doctype != "Purchase Invoice":
        return
    
    if not doc.get("bill_no") or not str(doc.bill_no).strip():
        frappe.throw(_("<b>Supplier Invoice No</b> is mandatory before submitting a Purchase Invoice. This is required for auditing."))

def check_app_permission():
    if frappe.session.user == "Administrator":
        return True

    if frappe.has_permission("Nepal Compliance Settings", ptype="read"):
        return True

    return False

def apply_pan_bill_vat_override(doc):
    """Set configured VAT to zero for a PAN/abbreviated Purchase Invoice."""
    if doc.doctype != "Purchase Invoice" or not doc.get(
        "is_pan_or_abbreviated_bill"
    ):
        return

    accounts = get_configured_vat_accounts().get(doc.company, {})
    vat_account = accounts.get("purchase")
    if not vat_account:
        frappe.throw(
            _(
                "Purchase VAT Account is required in Nepal Compliance Settings "
                "before a PAN/Abbreviated Bill can suppress VAT."
            ),
            title=_("Purchase VAT Account Not Configured"),
        )

    configured_vat_accounts = {
        account for account in accounts.values() if account
    }
    for item in doc.get("items") or []:
        detail = _parse_item_tax_rate(item.get("item_tax_rate"))
        for account in configured_vat_accounts:
            detail.pop(account, None)
        detail[vat_account] = 0
        item.item_tax_rate = json.dumps(detail)


@frappe.whitelist()

def get_purchase_invoice_requirements() -> dict:
    """Return submit-time purchase requirements used by the form UI."""
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    return {
        "bill_date": int(bool(settings.get("require_supplier_bill_date"))),
        "attachment": int(bool(settings.get("require_purchase_invoice_attachment"))),
    }

def parse_item_vat_entry(value):
    """Return (rate, amount) from stored or ERPNext item_wise_tax_detail values.

    Accepts [rate, amount], a dict with tax_rate/tax_amount, or a bare amount
    (legacy item_vat_detail JSON written before rates were stored).
    """
    if value is None:
        return 0.0, 0.0
    if isinstance(value, dict):
        rate = value.get("tax_rate")
        if rate is None:
            rate = value.get("rate")
        amount = value.get("tax_amount")
        if amount is None:
            amount = value.get("amount")
        return flt(rate), flt(amount)
    if isinstance(value, (list, tuple)):
        rate = flt(value[0]) if len(value) > 0 else 0.0
        amount = flt(value[1]) if len(value) > 1 else 0.0
        return rate, amount
    return 0.0, flt(value)

def accumulate_item_vat(item_vat, item_key, rate, amount):
    """Add a VAT row contribution, blending rates when the same item is taxed twice."""
    prev_rate, prev_amount = parse_item_vat_entry(item_vat.get(item_key))
    amount = flt(amount)
    rate = flt(rate)
    total_amount = prev_amount + amount
    if prev_amount and prev_rate and rate and abs(prev_rate - rate) > 1e-9:
        prev_base = prev_amount / (prev_rate / 100.0)
        new_base = amount / (rate / 100.0)
        total_base = prev_base + new_base
        blended = (total_amount / total_base * 100.0) if total_base else rate
        item_vat[item_key] = [blended, total_amount]
    else:
        item_vat[item_key] = [rate or prev_rate, total_amount]

def add_item_wise_vat(item_vat, item_wise_tax_detail):
    """Merge one tax row's item_wise_tax_detail into the per-item VAT map."""
    detail = item_wise_tax_detail
    if isinstance(detail, str):
        try:
            detail = json.loads(detail)
        except (TypeError, ValueError):
            detail = {}
    for item_key, rate_amount in (detail or {}).items():
        rate, amount = parse_item_vat_entry(rate_amount)
        accumulate_item_vat(item_vat, item_key, rate, amount)

def taxable_base_from_vat(vat_amount, rate, net_amount):
    """Amount VAT was charged on (net + prior rows such as excise/duty).

    Falls back to net_amount when rate is 0 (manually booked VAT, zero-rated).
    """
    if flt(rate):
        # round() matches Frappe's default banker's rounding and does not
        # depend on System Settings (flt(x, 2) can collapse to 0 without them).
        return round(flt(vat_amount) / (flt(rate) / 100.0), 2)
    return flt(net_amount)

def item_taxable_amount(item, row_vat, item_vat_map):
    """Taxable base for one item row: VAT ÷ rate, falling back to net amount."""
    key = item.get("item_code") or item.get("item_name")
    rate, _amount = parse_item_vat_entry(item_vat_map.get(key))
    return taxable_base_from_vat(row_vat, rate, item.get("net_amount"))

def tax_row_amount(tax):
    """Tax amount after discount when set, else tax_amount."""
    return flt(
        tax.tax_amount_after_discount_amount
        if tax.tax_amount_after_discount_amount is not None
        else tax.tax_amount
    )

PREVIOUS_ROW_VAT_CHARGE_TYPES = ("On Previous Row Total", "On Previous Row Amount")


def vat_charged_on_added_taxes(doc, vat_account=None):
    """True when VAT is calculated on a previous tax row (duty, excise, etc.).

    Item-net × 13% is not the VAT base in that stack, so Taxable Summary
    Refresh must not rewrite these invoices from the itemwise check.
    """
    if doc.doctype not in ("Sales Invoice", "Purchase Invoice"):
        return False
    if not vat_account:
        side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
        vat_account = get_configured_vat_accounts().get(doc.company, {}).get(side)
    if not vat_account:
        return False
    return any(
        tax.account_head == vat_account
        and tax.charge_type in PREVIOUS_ROW_VAT_CHARGE_TYPES
        for tax in (doc.get("taxes") or [])
    )

VAT_EXEMPT_TEMPLATE_TITLE = "VAT Exempt"

def get_configured_vat_accounts():
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    accounts = {}
    for row in settings.get("vat_accounts") or []:
        if row.company:
            accounts[row.company] = {
                "sales": row.sales_vat_account,
                "purchase": row.purchase_vat_account,
            }
    return accounts

def get_or_create_vat_exempt_template(company, vat_account, side):
    """Return the side-specific 0% VAT-exempt template, creating it if needed."""
    title = vat_exempt_template_title(side)
    existing = frappe.get_all(
        "Item Tax Template",
        filters={"company": company, "title": title},
        pluck="name",
    )
    if existing:
        template = frappe.get_doc("Item Tax Template", existing[0])
        if (
            len(template.taxes) != 1
            or template.taxes[0].tax_type != vat_account
            or flt(template.taxes[0].tax_rate) != 0
        ):
            template.taxes = [{"tax_type": vat_account, "tax_rate": 0}]
            template.save(ignore_permissions=True)
        return template.name

    template = frappe.get_doc({
        "doctype": "Item Tax Template",
        "title": title,
        "company": company,
        "taxes": [{"tax_type": vat_account, "tax_rate": 0}],
    }).insert(ignore_permissions=True)
    return template.name

def apply_vat_exemption_for_nontaxable_items(doc, method):
    flagged = [item for item in doc.get("items") or [] if item.get("is_nontaxable_item")]
    if not flagged:
        return

    side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
    vat_account = get_configured_vat_accounts().get(doc.company, {}).get(side)
    if not vat_account:
        frappe.msgprint(
            _("Some items are marked as non-taxable, but no {0} VAT account is configured for company {1}. VAT will still be charged on them. Please set the account under {2}.").format(
                _("Sales") if side == "sales" else _("Purchase"),
                frappe.bold(doc.company),
                get_link_to_form("Nepal Compliance Settings", "Nepal Compliance Settings", _("Nepal Compliance Settings > IRD VAT Accounts")),
            ),
            indicator="orange",
            alert=True,
        )
        return

    if not any(tax.account_head == vat_account for tax in doc.get("taxes") or []):
        return

    template_name = get_or_create_vat_exempt_template(doc.company, vat_account, side)
    for item in flagged:
        item.item_tax_template = template_name
        item.item_tax_rate = json.dumps({vat_account: 0})

@frappe.whitelist()
def is_purchase_invoice_attachment_required() -> int:
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    return int(bool(settings.get("require_purchase_invoice_attachment")))

def require_purchase_invoice_attachment(doc, method):
    if doc.doctype != "Purchase Invoice":
        return

    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    if not settings.get("require_purchase_invoice_attachment"):
        return

    if not doc.get("attach_purchase_invoice"):
        frappe.throw(_("<b>Attach Purchase Invoice</b> is mandatory before submitting a Purchase Invoice. Please attach the supplier's invoice document."))

def validate_duplicate_bill_no(doc, method):
    if doc.doctype != "Purchase Invoice":
        return

    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    if not settings.get("enable_duplicate_bill_no_check"):
        return

    if not doc.bill_no or not doc.supplier:
        return

    normalized_bill_no = str(doc.bill_no).strip().lstrip("0") or "0"

    fiscal_year = None
    if doc.posting_date:
        fiscal_year = frappe.db.get_value(
            "Fiscal Year",
            {
                "year_start_date": ["<=", doc.posting_date],
                "year_end_date": [">=", doc.posting_date]
            },
            ["name", "year_start_date", "year_end_date"],
            as_dict=True
        )
    if not fiscal_year:
        return

    invoices = frappe.get_all(
        "Purchase Invoice",
        filters={
            "supplier": doc.supplier,
            "docstatus": ["<", 2],
            "name": ["!=", doc.name],
            "posting_date": ["between", [fiscal_year.year_start_date, fiscal_year.year_end_date]]
        },
        fields=["name", "bill_no"]
    )

    for inv in invoices:
        existing_bill = (str(inv.bill_no or "").strip().lstrip("0") or "0")
        if existing_bill.lower() == normalized_bill_no.lower():
            supplier_name = frappe.db.get_value("Supplier", doc.supplier, "supplier_name") or doc.supplier
            invoice_link = get_link_to_form("Purchase Invoice", inv.name)
            frappe.msgprint(
                _("<b>Duplicate Bill No Detected.</b><br><br>Supplier: {0}<br>Bill No: {1}<br>Fiscal Year: {2}<br><br>Existing Invoice: {3}<br><small>Click the invoice link above to view the existing record.</small>").format(
                    f"{supplier_name} ({doc.supplier})",
                    doc.bill_no,
                    fiscal_year.name,
                    invoice_link
                ),
                indicator="red",
                alert=True,
                title=_("Duplicate Bill Number")
            )
            frappe.throw(
                _("Duplicate Bill Number '{0}' not allowed for supplier '{1}' in fiscal year '{2}'. Please check invoice {3}.").format(
                    doc.bill_no, supplier_name, fiscal_year.name, inv.name
                )
            )

def set_taxable_amounts(doc, method, consider_is_non_taxable_item=False):
    """Set IRD taxable summary fields and return an optional VAT calculation check.

    The normal document-event path keeps the historical item-wise VAT
    classification. The settings recompute can instead classify items solely
    from the item's Is Non-Taxable Item flag.
    """
    side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
    vat_account = get_configured_vat_accounts().get(doc.company, {}).get(side)

    item_vat = {}
    vat_amount = 0.0
    if vat_account:
        for tax in doc.get("taxes") or []:
            if tax.account_head != vat_account:
                continue
            vat_amount += tax_row_amount(tax)
            add_item_wise_vat(item_vat, tax.item_wise_tax_detail)

    items = list(doc.get("items") or [])
    row_vat = distribute_item_vat(items, item_vat)
    include_added_taxes = vat_charged_on_added_taxes(doc, vat_account)

    taxable_amount = non_taxable_amount = 0.0
    force_all_non_taxable = bool(
        doc.get("is_pan_or_abbreviated_bill")
        or (
            doc.doctype == "Purchase Invoice"
            and (not doc.get("taxes") or not flt(vat_amount))
        )
    )
    for item, item_row_vat in zip(items, row_vat, strict=True):
        amt = flt(item.get("net_amount"))
        if consider_is_non_taxable_item:
            is_non_taxable = bool(
                force_all_non_taxable or item.get("is_nontaxable_item")
            )
        else:
            item_key = item.get("item_code") or item.get("item_name")
            is_non_taxable = bool(
                item.get("is_nontaxable_item")
                or not flt(parse_item_vat_entry(item_vat.get(item_key))[1])
            )
        if is_non_taxable:
            non_taxable_amount += amt
        elif include_added_taxes:
            # VAT was charged on net + prior rows (duty/excise). Use VAT ÷ rate
            # so expected VAT is 13% of that same base.
            taxable_amount += item_taxable_amount(item, item_row_vat, item_vat)
        else:
            taxable_amount += amt

    doc.taxable_amount = taxable_amount
    doc.non_taxable_amount = non_taxable_amount
    doc.vat_amount = vat_amount
    # Bill Total is grand_total plus TDS: ERPNext deducts TDS from grand_total,
    # IRD wants the billed value (net + VAT) before withholding.
    set_bill_total(doc, vat_account)

    if not consider_is_non_taxable_item:
        return None

    expected_vat = flt(taxable_amount * 0.13, 2)
    recorded_vat = flt(vat_amount, 2)
    difference = flt(recorded_vat - expected_vat, 2)
    return {
        "expected_vat": expected_vat,
        "recorded_vat": recorded_vat,
        "vat_difference": difference,
        "has_vat_mismatch": abs(difference) >= 0.01,
        "vat_on_added_taxes": include_added_taxes,
    }

def get_vat_breakup(invoice_doctype, invoice_company_map):
    """
    Return per-invoice VAT amounts from the invoice's taxes table, considering only
    the tax rows whose account head matches the VAT account configured for the
    invoice's company in Nepal Compliance Settings.

    Returns {invoice_name: {"item_vat": {item_code: amount}, "total_vat": float,
    "configured": bool}}.
    """
    if not invoice_company_map:
        return {}

    is_sales = invoice_doctype == "Sales Invoice"
    side = "sales" if is_sales else "purchase"
    taxes_doctype = "Sales Taxes and Charges" if is_sales else "Purchase Taxes and Charges"

    configured = get_configured_vat_accounts()
    result = {
        name: {
            "item_vat": {},
            "total_vat": 0.0,
            "configured": bool(configured.get(company, {}).get(side)),
        }
        for name, company in invoice_company_map.items()
    }
    missing = sorted({c for c in invoice_company_map.values() if c and not configured.get(c, {}).get(side)})
    if missing:
        frappe.msgprint(
            _("VAT account is not configured for the following companies: {0}. VAT amounts will be shown as 0 in this report. Please set the {1} VAT Account under {2}.").format(
                ", ".join(frappe.bold(c) for c in missing),
                _("Sales") if is_sales else _("Purchase"),
                get_link_to_form("Nepal Compliance Settings", "Nepal Compliance Settings", _("Nepal Compliance Settings > IRD VAT Accounts")),
            ),
            indicator="orange",
            alert=True,
        )

    tax_rows = frappe.get_all(
        taxes_doctype,
        filters={"parent": ["in", list(invoice_company_map)], "parenttype": invoice_doctype},
        fields=["parent", "account_head", "tax_amount", "tax_amount_after_discount_amount", "item_wise_tax_detail"],
    )

    for row in tax_rows:
        vat_account = configured.get(invoice_company_map.get(row.parent), {}).get(side)
        if not vat_account or row.account_head != vat_account:
            continue

        entry = result[row.parent]
        entry["total_vat"] += flt(
            row.tax_amount_after_discount_amount
            if row.tax_amount_after_discount_amount is not None
            else row.tax_amount
        )
        try:
            detail = json.loads(row.item_wise_tax_detail) if row.item_wise_tax_detail else {}
        except (TypeError, ValueError):
            detail = {}
        for item_key, rate_amount in detail.items():
            if isinstance(rate_amount, (list, tuple)) and len(rate_amount) > 1:
                entry["item_vat"][item_key] = entry["item_vat"].get(item_key, 0.0) + flt(rate_amount[1])

    return result

def distribute_item_vat(items, item_vat_map):
    """
    Split item_code-level VAT (from item_wise_tax_detail) across individual item
    rows, proportionally to each row's net_amount. The last row of each item code
    takes the residual so the distributed amounts always sum back to the map total.

    Returns a list of VAT amounts aligned with `items` by index.
    """
    groups = {}
    for idx, item in enumerate(items):
        key = item.get("item_code") or item.get("item_name")
        groups.setdefault(key, []).append(idx)

    row_vat = [0.0] * len(items)
    for key, idxs in groups.items():
        total_vat = parse_item_vat_entry(item_vat_map.get(key))[1]
        total_net = sum(flt(items[i].get("net_amount")) for i in idxs)
        allocated = 0.0
        for pos, i in enumerate(idxs):
            if pos == len(idxs) - 1:
                share = total_vat - allocated
            else:
                share = (total_vat * flt(items[i].get("net_amount")) / total_net) if total_net else 0.0
            row_vat[i] = share
            allocated += share

    return row_vat

VAT_TAXABLE_TEMPLATE_TITLE = "Nepal Tax"

def vat_exempt_template_title(side):
    """Return the stable side-specific title for a VAT-exempt template."""
    return f"{VAT_EXEMPT_TEMPLATE_TITLE} ({'Sales' if side == 'sales' else 'Purchase'})"


def format_vat_rate(rate):
    """Return a stable compact rate string for Item Tax Template titles."""
    value = flt(rate)
    return f"{value:.6f}".rstrip("0").rstrip(".")

def vat_taxable_template_title(side, rate):
    """Return the stable side-and-rate-specific taxable VAT template title."""
    label = "Sales" if side == "sales" else "Purchase"
    return f"{VAT_TAXABLE_TEMPLATE_TITLE} ({label} - {format_vat_rate(rate)}%)"

def get_or_create_vat_taxable_template(company, vat_account, side, rate):
    """Return a side-and-rate-specific VAT template without changing its rate."""
    rate = flt(rate)
    if rate <= 0:
        frappe.throw(_("Taxable VAT rate must be greater than zero."))

    title = vat_taxable_template_title(side, rate)
    existing = frappe.get_all(
        "Item Tax Template",
        filters={"company": company, "title": title},
        pluck="name",
    )
    taxes = [{"tax_type": vat_account, "tax_rate": rate}]
    if existing:
        template = frappe.get_doc("Item Tax Template", existing[0])
        if len(template.taxes) != 1 or flt(template.taxes[0].tax_rate) != rate:
            frappe.throw(
                _("Item Tax Template {0} does not match its VAT rate {1}%.").format(
                    frappe.bold(template.name), format_vat_rate(rate)
                )
            )
        if template.taxes[0].tax_type != vat_account:
            template.taxes[0].tax_type = vat_account
            template.save(ignore_permissions=True)
        return template.name

    template = frappe.get_doc(
        {
            "doctype": "Item Tax Template",
            "title": title,
            "company": company,
            "taxes": taxes,
        }
    ).insert(ignore_permissions=True)
    return template.name

def _parse_item_tax_rate(value):
    """Return an item tax-rate dict without discarding unrelated tax entries."""
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}

def _managed_taxable_template_side(title):
    """Return sales/purchase for a managed rate-specific template title."""
    title = title or ""
    if title.startswith(f"{VAT_TAXABLE_TEMPLATE_TITLE} (Sales - "):
        return "sales"
    if title.startswith(f"{VAT_TAXABLE_TEMPLATE_TITLE} (Purchase - "):
        return "purchase"
    return None

def sync_managed_vat_taxable_templates(company, vat_account, side):
    """Repoint managed templates to a VAT account while preserving every rate."""
    prefix = f"{VAT_TAXABLE_TEMPLATE_TITLE} ({'Sales' if side == 'sales' else 'Purchase'} - "
    names = frappe.get_all(
        "Item Tax Template",
        filters={"company": company, "title": ["like", f"{prefix}%"]},
        pluck="name",
    )
    for name in names:
        template = frappe.get_doc("Item Tax Template", name)
        if len(template.taxes) != 1 or flt(template.taxes[0].tax_rate) <= 0:
            continue
        if template.taxes[0].tax_type != vat_account:
            template.taxes[0].tax_type = vat_account
            template.save(ignore_permissions=True)

def _legacy_vat_template_rate(template_name, company, vat_accounts):
    """Return the positive VAT rate for an eligible shared legacy template."""
    if not template_name:
        return None
    template = frappe.get_cached_doc("Item Tax Template", template_name)
    if template.company != company or _managed_taxable_template_side(template.title):
        return None
    if not (template.title or "").startswith(VAT_TAXABLE_TEMPLATE_TITLE):
        return None

    configured = {account for account in vat_accounts.values() if account}
    matching = [
        row for row in template.get("taxes") or []
        if row.tax_type in configured and flt(row.tax_rate) > 0
    ]
    if len(template.get("taxes") or []) != 1 or len(matching) != 1:
        return None
    return flt(matching[0].tax_rate)

def ensure_side_specific_item_tax_mappings(doc, method=None):
    """Allow both side/rate templates wherever a shared legacy template is allowed."""
    if doc.doctype not in ("Item", "Item Group"):
        return

    companies = get_configured_vat_accounts()
    existing = {
        (
            row.get("item_tax_template"),
            row.get("tax_category"),
            row.get("valid_from"),
            flt(row.get("minimum_net_rate")),
            flt(row.get("maximum_net_rate")),
        )
        for row in doc.get("taxes") or []
    }
    additions = []
    for row in list(doc.get("taxes") or []):
        template_name = row.get("item_tax_template")
        if not template_name:
            continue
        company = frappe.get_cached_value("Item Tax Template", template_name, "company")
        vat_accounts = companies.get(company, {})
        rate = _legacy_vat_template_rate(template_name, company, vat_accounts)
        if rate is None:
            continue

        for side in ("sales", "purchase"):
            account = vat_accounts.get(side)
            if not account:
                continue
            target = get_or_create_vat_taxable_template(company, account, side, rate)
            key = (
                target,
                row.get("tax_category"),
                row.get("valid_from"),
                flt(row.get("minimum_net_rate")),
                flt(row.get("maximum_net_rate")),
            )
            if key in existing:
                continue
            additions.append(
                {
                    "item_tax_template": target,
                    "tax_category": row.get("tax_category"),
                    "valid_from": row.get("valid_from"),
                    "minimum_net_rate": row.get("minimum_net_rate"),
                    "maximum_net_rate": row.get("maximum_net_rate"),
                }
            )
            existing.add(key)

    for values in additions:
        doc.append("taxes", values)

def apply_side_specific_vat_template(doc, method):
    """Replace the opposite-side VAT account on taxable invoice items.

    Legacy ``Nepal Tax`` Item Tax Templates were shared by Sales and Purchase
    transactions, so their single VAT ledger could only be correct for one
    side. Preserve each item's VAT rate while moving it to the configured
    side-specific template and account.
    """
    if doc.doctype not in ("Sales Invoice", "Purchase Invoice"):
        return

    side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
    accounts = get_configured_vat_accounts().get(doc.company, {})
    vat_account = accounts.get(side)
    other_account = accounts.get("purchase" if side == "sales" else "sales")
    if not vat_account or not other_account or vat_account == other_account:
        return

    repaired_accounts = set()
    for item in doc.get("items") or []:
        detail = _parse_item_tax_rate(item.get("item_tax_rate"))
        source_template_name = item.get("item_tax_template")
        if not source_template_name:
            continue
        source_template = frappe.get_cached_doc(
            "Item Tax Template", source_template_name
        )
        source_side = _managed_taxable_template_side(source_template.title)
        legacy_rate = _legacy_vat_template_rate(
            source_template_name, doc.company, accounts
        )
        is_legacy_or_opposite = legacy_rate is not None or (
            source_side and source_side != side
        )
        if not is_legacy_or_opposite:
            continue

        source_account = (
            other_account
            if flt(detail.get(other_account)) > 0
            else vat_account
        )
        rate = flt(detail.get(source_account)) or flt(legacy_rate)
        if rate <= 0:
            continue
        item.item_tax_template = get_or_create_vat_taxable_template(
            doc.company, vat_account, side, rate
        )
        detail.pop(source_account, None)
        detail[vat_account] = rate
        item.item_tax_rate = json.dumps(detail)
        if source_account == other_account:
            repaired_accounts.add(other_account)

    if not repaired_accounts:
        return

    # Item Tax Template rows appear on the parent as zero-rate "On Net Total"
    # rows. Remove only that known legacy shape; preserve manual adjustments.
    doc.set(
        "taxes",
        [
            tax
            for tax in (doc.get("taxes") or [])
            if not (
                tax.account_head in repaired_accounts
                and tax.get("charge_type") == "On Net Total"
                and not flt(tax.get("rate"))
                and not tax.get("is_tax_withholding_account")
            )
        ],
    )

def is_purchase_tds_row(tax, vat_account=None):
    """True when a Purchase Invoice tax row is TDS (withholding or Deduct).

    Nepal TDS rates are not fixed, so rows are identified by ERPNext's
    withholding/deduct flags, never by rate. The configured VAT account is
    never treated as TDS.
    """
    if vat_account and tax.account_head == vat_account:
        return False
    return bool(tax.get("is_tax_withholding_account")) or tax.get("add_deduct_tax") == "Deduct"

def get_tds_amount(doc, vat_account=None):
    """Sum Purchase Invoice TDS (signed, so returns stay negative)."""
    if doc.doctype != "Purchase Invoice":
        return 0.0
    tds_amount = 0.0
    for tax in doc.get("taxes") or []:
        if is_purchase_tds_row(tax, vat_account):
            tds_amount += tax_row_amount(tax)
    return tds_amount

def set_bill_total(doc, vat_account=None):
    """Bill Total is grand_total, plus TDS on Purchase Invoice (TDS is deducted from grand_total)."""
    doc.summary_grand_total = flt(doc.grand_total) + get_tds_amount(doc, vat_account)

def invoice_ird_total(inv):
    """IRD register total: Taxable Summary Bill Total, else rounded/grand total."""
    if inv.get("summary_grand_total") is not None:
        return flt(inv.summary_grand_total)
    return flt(inv.rounded_total) or flt(inv.grand_total)

def category_calculates_tds_on_taxable_amount(category_name):
    """True when the Tax Withholding Category is set to use Purchase Invoice taxable amount."""
    if not category_name:
        return False
    if not frappe.db.has_column("Tax Withholding Category", "calculate_tds_on_taxable_amount"):
        return False
    return bool(
        frappe.db.get_value(
            "Tax Withholding Category", category_name, "calculate_tds_on_taxable_amount"
        )
    )

def get_purchase_tds_category(doc):
    """Return the invoice or supplier Tax Withholding Category."""
    return doc.get("tax_withholding_category") or frappe.db.get_value(
        "Supplier", doc.get("supplier"), "tax_withholding_category"
    )

def get_purchase_taxable_tds_base(doc, throw_on_unavailable=True):
    """Compute the transaction-currency taxable base or report it unavailable."""
    accounts = get_configured_vat_accounts().get(doc.company, {})
    vat_account = accounts.get("purchase")
    if doc.get("is_pan_or_abbreviated_bill"):
        set_taxable_amounts(doc, None)
        return flt(doc.get("summary_grand_total")), None

    reason = None
    if not vat_account:
        reason = _("Purchase VAT Account is not configured for company {0}.").format(
            frappe.bold(doc.company)
        )
    elif not any(
        tax.get("account_head") == vat_account for tax in doc.get("taxes") or []
    ):
        reason = _(
            "No Purchase VAT row using {0} was found, so Taxable Amount cannot be verified."
        ).format(frappe.bold(vat_account))

    if reason:
        if throw_on_unavailable:
            frappe.throw(
                _(
                    "Nepal Compliance cannot calculate TDS on Taxable Amount. {0} "
                    "Correct the VAT configuration or invoice taxes; net total will not be used as a fallback."
                ).format(reason),
                title=_("TDS Taxable Base Unavailable"),
            )
        return None, reason

    set_taxable_amounts(doc, None)
    if doc.get("taxable_amount") is None:
        reason = _("The invoice Taxable Amount could not be calculated.")
        if throw_on_unavailable:
            frappe.throw(reason, title=_("TDS Taxable Base Unavailable"))
        return None, reason
    return flt(doc.taxable_amount), None

def apply_taxable_amount_as_tds_base(doc):
    """Point ERPNext withholding at taxable_amount when the category asks for it.

    Must run after taxes have been calculated so VAT (and thus taxable amount)
    is available, and before set_tax_withholding reads tax_withholding_net_total.
    """
    if doc.doctype != "Purchase Invoice" or not doc.get("apply_tds"):
        return False
    category = get_purchase_tds_category(doc)
    if not category_calculates_tds_on_taxable_amount(category):
        return False

    taxable, _reason = get_purchase_taxable_tds_base(doc)
    doc.tax_withholding_net_total = taxable
    precision = (
        doc.precision("base_tax_withholding_net_total")
        if hasattr(doc, "precision")
        else None
    )
    doc.base_tax_withholding_net_total = flt(
        taxable * flt(doc.get("conversion_rate") or 1), precision
    )
    return True

def resolve_report_vat_source(inv, vat_breakup):
    """
    Decide the per-item VAT source for an invoice row in IRD reports.

    Returns (item_vat_map, stored, breakup). When the invoice has frozen taxable
    summary values (stored_taxable_amount is not None), the stored
    item_vat_detail JSON is the source and the result is immune to later VAT
    account changes. Otherwise fall back to the live account-based breakup from
    get_vat_breakup (legacy invoices and unconfigured companies).
    """
    breakup = vat_breakup.get(inv.get("invoice"), {}) or {}
    live_map = breakup.get("item_vat") if isinstance(breakup.get("item_vat"), dict) else {}

    if inv.get("stored_taxable_amount") is not None:
        item_vat_map = parse_stored_item_vat_map(inv.get("stored_item_vat_detail"))
        if item_vat_map is not None:
            return item_vat_map, True, breakup
        # Invalid stored JSON must not become {} (that would look like exemption).
        return live_map, False, breakup
    return live_map, False, breakup

def parse_stored_item_vat_map(raw):
    """Return a dict VAT map, or None when stored detail is missing or the wrong shape."""
    if raw is None or raw == "":
        return None
    parsed = raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            return None
    if not isinstance(parsed, dict):
        return None
    return parsed

def is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup):
    """Exempt classification for an invoice item row in IRD reports.

    With frozen (stored) values, mirror the rule that produced them at save
    time so report rows always sum back to the stored invoice totals. With the
    live fallback, defer to classify_item_taxability.
    """
    if stored:
        return bool(item.get("is_nontaxable_item")) or not flt(item_vat)
    breakup = breakup or {}
    return classify_item_taxability(
        item, item_vat, item_vat_map, breakup.get("total_vat"), breakup.get("configured")
    ) == "exempt"

def classify_item_taxability(item, item_vat, item_vat_map, invoice_total_vat, vat_configured):
    """
    Classify an invoice item row as "exempt" or "taxable" for IRD reports.

    Exemption is deliberate: the item is flagged is_nontaxable_item, or the VAT
    breakdown explicitly records 0 VAT for it. When the invoice carries VAT but
    the item is missing from the breakdown (or no VAT account is configured, so
    no breakdown could be built), the data is unavailable - report the row as
    taxable with 0 VAT instead of inventing an exemption.
    """
    if item.get("is_nontaxable_item"):
        return "exempt"
    key = item.get("item_code") or item.get("item_name")
    if key in item_vat_map:
        return "taxable" if flt(item_vat) else "exempt"
    return "taxable"
