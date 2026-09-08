import json
import frappe
from frappe import _
from frappe.utils import flt
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
