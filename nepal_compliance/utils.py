import json

import frappe
from frappe import _
from frappe.utils import flt, get_link_to_form
from frappe.utils.safe_exec import safe_eval
from frappe.model.naming import make_autoname
from typing import Union

def prevent_invoice_deletion(doc, method):
    """Block deletion of submitted invoices for IRD compliance."""
    if (doc.docstatus == 1):
        frappe.throw(_(f"Deletion of {doc.name} is not allowed due to compliance rule."))

def custom_autoname(doc, method):
    """Assign a unique naming-series name, retrying on collision."""
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
    """Evaluate a salary-tax formula against taxable_salary using safe_eval."""
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
    """Copy party and company VAT/PAN onto opening invoices when those fields are empty."""
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
    """Set the Nepali date field from the document's AD posting/transaction date."""
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
    """Require supplier invoice number and date before submitting a Purchase Invoice."""
    if doc.doctype != "Purchase Invoice":
        return

    if not doc.get("bill_no") or not str(doc.bill_no).strip():
        frappe.throw(_("<b>Supplier Invoice No</b> is mandatory before submitting a Purchase Invoice. This is required for auditing."))

    if not doc.get("bill_date"):
        frappe.throw(_("<b>Supplier Invoice Date</b> is mandatory before submitting a Purchase Invoice. This is required for auditing."))

def check_app_permission():
    """Allow the Nepal Compliance desk app when the user can read Settings."""
    if frappe.session.user == "Administrator":
        return True

    if frappe.has_permission("Nepal Compliance Settings", ptype="read"):
        return True

    return False

def get_configured_vat_accounts():
    """Return {company: {sales, purchase}} VAT ledgers from Nepal Compliance Settings."""
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    accounts = {}
    for row in settings.get("vat_accounts") or []:
        if row.company:
            accounts[row.company] = {
                "sales": row.sales_vat_account,
                "purchase": row.purchase_vat_account,
            }
    return accounts

VAT_EXEMPT_TEMPLATE_TITLE = "VAT Exempt"

def get_or_create_vat_exempt_template(company, vat_account):
    """Return the 0% VAT Exempt item tax template for the company, creating it if needed."""
    existing = frappe.get_all(
        "Item Tax Template",
        filters={"company": company, "title": VAT_EXEMPT_TEMPLATE_TITLE},
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
        "title": VAT_EXEMPT_TEMPLATE_TITLE,
        "company": company,
        "taxes": [{"tax_type": vat_account, "tax_rate": 0}],
    }).insert(ignore_permissions=True)
    return template.name

def apply_vat_exemption_for_nontaxable_items(doc, method):
    """Assign the 0% VAT Exempt item tax template to items flagged is_nontaxable_item."""
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

    template_name = get_or_create_vat_exempt_template(doc.company, vat_account)
    for item in flagged:
        item.item_tax_template = template_name
        item.item_tax_rate = json.dumps({vat_account: 0})

@frappe.whitelist()
def is_purchase_invoice_attachment_required():
    """True when Nepal Compliance Settings requires a purchase invoice attachment."""
    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    return int(bool(settings.get("require_purchase_invoice_attachment")))

def require_purchase_invoice_attachment(doc, method):
    """Block submit when a purchase invoice attachment is required and missing."""
    if doc.doctype != "Purchase Invoice":
        return

    settings = frappe.get_cached_doc("Nepal Compliance Settings")
    if not settings.get("require_purchase_invoice_attachment"):
        return

    if not doc.get("attach_purchase_invoice"):
        frappe.throw(_("<b>Attach Purchase Invoice</b> is mandatory before submitting a Purchase Invoice. Please attach the supplier's invoice document."))

def validate_duplicate_bill_no(doc, method):
    """Reject a supplier bill number that already exists in the same fiscal year."""
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
    rate, _ = parse_item_vat_entry(item_vat_map.get(key))
    return taxable_base_from_vat(row_vat, rate, item.get("net_amount"))


def set_taxable_amounts(doc, method):
    """Freeze taxable, non-taxable, VAT, and item VAT detail on the invoice."""
    side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
    vat_account = get_configured_vat_accounts().get(doc.company, {}).get(side)

    if not vat_account:
        # Leave the computed fields empty ("not computed") so reports fall back
        # to live account-based logic and configuring the account later can
        # still fix these invoices retroactively.
        doc.taxable_amount = None
        doc.non_taxable_amount = None
        doc.vat_amount = None
        doc.item_vat_detail = None
        doc.summary_grand_total = (
            flt(doc.grand_total) if doc.get("disable_rounded_total") else (flt(doc.rounded_total) or flt(doc.grand_total))
        )
        return

    item_vat = {}
    vat_amount = 0.0
    for tax in doc.get("taxes") or []:
        if tax.account_head != vat_account:
            continue
        vat_amount += flt(
            tax.tax_amount_after_discount_amount
            if tax.tax_amount_after_discount_amount is not None
            else tax.tax_amount
        )
        add_item_wise_vat(item_vat, tax.item_wise_tax_detail)

    taxable_amount = non_taxable_amount = 0.0
    items = list(doc.get("items") or [])
    row_vat = distribute_item_vat(items, item_vat)
    for item, vat_amt in zip(items, row_vat, strict=True):
        net = flt(item.get("net_amount"))
        if item.get("is_nontaxable_item") or not flt(vat_amt):
            non_taxable_amount += net
        else:
            taxable_amount += item_taxable_amount(item, vat_amt, item_vat)

    doc.taxable_amount = taxable_amount
    doc.non_taxable_amount = non_taxable_amount
    doc.vat_amount = vat_amount
    doc.item_vat_detail = json.dumps(item_vat)
    doc.summary_grand_total = (
        flt(doc.grand_total) if doc.get("disable_rounded_total") else (flt(doc.rounded_total) or flt(doc.grand_total))
    )

def get_vat_breakup(invoice_doctype, invoice_company_map):
    """
    Return per-invoice VAT amounts from the invoice's taxes table, considering only
    the tax rows whose account head matches the VAT account configured for the
    invoice's company in Nepal Compliance Settings.

    Returns {invoice_name: {"item_vat": {item_code: [rate, amount]}, "total_vat": float,
    "configured": bool}}. "configured" is False when the invoice's company has no
    VAT account set in Nepal Compliance Settings, meaning the empty breakup is
    unavailable data rather than a genuinely VAT-free invoice.
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
        add_item_wise_vat(entry["item_vat"], row.item_wise_tax_detail)

    return result

def resolve_report_vat_source(inv, vat_breakup):
    """
    Decide the per-item VAT source for an invoice row in IRD reports.

    Returns (item_vat_map, stored, breakup). When the invoice has frozen taxable
    summary values (stored_taxable_amount is not None), the stored
    item_vat_detail JSON is the source and the result is immune to later VAT
    account changes. Otherwise fall back to the live account-based breakup from
    get_vat_breakup (legacy invoices and unconfigured companies).
    """
    if inv.get("stored_taxable_amount") is not None:
        try:
            return json.loads(inv.get("stored_item_vat_detail") or "{}"), True, None
        except (TypeError, ValueError):
            return {}, True, None
    breakup = vat_breakup.get(inv.get("invoice"), {})
    return breakup.get("item_vat", {}), False, breakup


def is_exempt_report_item(item, item_vat, item_vat_map, stored, breakup):
    """Exempt classification for an invoice item row in IRD reports.

    With frozen (stored) values, mirror the rule that produced them at save
    time so report rows always sum back to the stored invoice totals. With the
    live fallback, defer to classify_item_taxability.
    """
    if stored:
        return bool(item.get("is_nontaxable_item")) or not flt(item_vat)
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
    if flt(invoice_total_vat) or not vat_configured:
        return "taxable"
    return "exempt"


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