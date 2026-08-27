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

    if not doc.get("bill_date"):
        frappe.throw(_("<b>Supplier Invoice Date</b> is mandatory before submitting a Purchase Invoice. This is required for auditing."))

def check_app_permission():
    if frappe.session.user == "Administrator":
        return True

    if frappe.has_permission("Nepal Compliance Settings", ptype="read"):
        return True

    return False

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

VAT_EXEMPT_TEMPLATE_TITLE = "VAT Exempt"

def get_or_create_vat_exempt_template(company, vat_account):
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

def set_taxable_amounts(doc, method):
    side = "sales" if doc.doctype == "Sales Invoice" else "purchase"
    vat_account = get_configured_vat_accounts().get(doc.company, {}).get(side)

    item_vat = {}
    vat_amount = 0.0
    if vat_account:
        for tax in doc.get("taxes") or []:
            if tax.account_head != vat_account:
                continue
            vat_amount += flt(
                tax.tax_amount_after_discount_amount
                if tax.tax_amount_after_discount_amount is not None
                else tax.tax_amount
            )
            detail = tax.item_wise_tax_detail
            if isinstance(detail, str):
                try:
                    detail = json.loads(detail)
                except (TypeError, ValueError):
                    detail = {}
            for item_key, rate_amount in (detail or {}).items():
                if isinstance(rate_amount, (list, tuple)) and len(rate_amount) > 1:
                    item_vat[item_key] = item_vat.get(item_key, 0.0) + flt(rate_amount[1])

    taxable_amount = non_taxable_amount = 0.0
    for item in doc.get("items") or []:
        amt = flt(item.get("net_amount"))
        if item.get("is_nontaxable_item") or not flt(item_vat.get(item.get("item_code") or item.get("item_name"))):
            non_taxable_amount += amt
        else:
            taxable_amount += amt

    doc.taxable_amount = taxable_amount
    doc.non_taxable_amount = non_taxable_amount
    doc.vat_amount = vat_amount
    doc.summary_grand_total = (
        flt(doc.grand_total) if doc.get("disable_rounded_total") else (flt(doc.rounded_total) or flt(doc.grand_total))
    )

def get_vat_breakup(invoice_doctype, invoice_company_map):
    """
    Return per-invoice VAT amounts from the invoice's taxes table, considering only
    the tax rows whose account head matches the VAT account configured for the
    invoice's company in Nepal Compliance Settings.

    Returns {invoice_name: {"item_vat": {item_code: amount}, "total_vat": float}}.
    """
    result = {name: {"item_vat": {}, "total_vat": 0.0} for name in invoice_company_map}
    if not invoice_company_map:
        return result

    is_sales = invoice_doctype == "Sales Invoice"
    side = "sales" if is_sales else "purchase"
    taxes_doctype = "Sales Taxes and Charges" if is_sales else "Purchase Taxes and Charges"

    configured = get_configured_vat_accounts()
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