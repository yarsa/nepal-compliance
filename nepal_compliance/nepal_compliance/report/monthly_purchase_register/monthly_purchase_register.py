# Copyright (c) 2024, Yarsa Labs Pvt. Ltd. and contributors
# For license information, please see LICENSE at the root of this repository

import frappe
from frappe import _
from nepal_compliance.nepali_date_utils.nepali_date import ad_to_bs
from nepal_compliance.nepali_date_utils.utils import bs_date

NEPALI_MONTH_MAP = {
	"Baishakh": 1, "Jestha": 2, "Ashadh": 3, "Shrawan": 4,
	"Bhadra": 5, "Ashwin": 6, "Kartik": 7, "Mangsir": 8,
	"Poush": 9, "Magh": 10, "Falgun": 11, "Chaitra": 12,
}

def execute(filters=None):
	filters = filters or {}

	validate_company(filters)

	fy = get_fiscal_year(filters)

	columns = get_columns()
	data = []

	conditions, values = build_conditions(filters, fy)

	query = """
		SELECT
			pi.posting_date,
			pi.supplier,
			COALESCE(NULLIF(pi.vat_number, ''), NULLIF(pi.tax_id, '')) AS vat_pan_number,
			pi.name AS invoice_number,
			SUM(item.qty) AS total_qty,
			SUM(item.qty * item.rate) AS total_amount,
			pi.taxes_and_charges_added,
			pi.discount_amount,
			pi.total,
			pi.net_total,
			pi.grand_total,
			pi.total_advance,
			pi.outstanding_amount,
			pi.status
		FROM `tabPurchase Invoice` pi
		JOIN `tabPurchase Invoice Item` item
			ON item.parent = pi.name
		WHERE
			pi.docstatus = 1
			{conditions}
		GROUP BY pi.name
		ORDER BY pi.posting_date DESC
	"""
	query = query.replace("{conditions}", conditions)

	rows = frappe.db.sql(query, values, as_dict=True)

	target_month = NEPALI_MONTH_MAP.get(filters.get("nepali_month"))

	for r in rows:
		bs = ad_to_bs(r.posting_date)

		if target_month and bs["month"] != target_month:
			continue

		data.append([
			bs_date(r.posting_date),
			r.supplier,
			r.vat_pan_number,
			r.invoice_number,
			r.total_qty,
			r.total_amount,
			r.taxes_and_charges_added,
			r.discount_amount,
			r.total,
			r.net_total,
			r.grand_total,
			r.total_advance,
			r.outstanding_amount,
			r.status,
		])

	return columns, data

def validate_company(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is required"))

def get_fiscal_year(filters):
	if filters.get("fiscal_year"):
		return frappe.get_doc("Fiscal Year", filters["fiscal_year"])

	fy_names = frappe.get_all(
		"Fiscal Year Company",
		filters={"company": filters["company"]},
		pluck="parent"
	)

	if not fy_names:
		frappe.throw(_("No Fiscal Year found for company"))
  
	fy = frappe.get_all(
		"Fiscal Year",
		filters={
			"company": filters["company"],
			"disabled": 0
		},
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date asc",
		limit=1
	)

	if not fy:
		frappe.throw(_("No default Fiscal Year found for company"))

	return frappe.get_doc("Fiscal Year", fy[0].name)

def build_conditions(filters, fy):
	conditions = []
	values = {}

	conditions.append(
		"AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"
	)

	values["from_date"] = fy.year_start_date
	values["to_date"] = fy.year_end_date

	if filters.get("supplier"):
		conditions.append("AND pi.supplier = %(supplier)s")
		values["supplier"] = filters["supplier"]

	if filters.get("company"):
		conditions.append("AND pi.company = %(company)s")
		values["company"] = filters["company"]

	return " ".join(conditions), values

def get_columns():
	return [
		_("Invoice Date (BS)") + ":Data:150",
		_("Supplier") + ":Link/Supplier:150",
		_("VAT/PAN Number") + ":Data:120",
		_("Invoice Number") + ":Link/Purchase Invoice:200",
		_("Qty") + ":Float:60",
		_("Amount") + ":Currency:100",
		_("Tax and Charges Added") + ":Currency:120",
		_("Discount") + ":Currency:120",
		_("Total") + ":Currency:120",
		_("Net Total") + ":Currency:120",
		_("Grand Total") + ":Currency:120",
		_("Total Advance") + ":Currency:120",
		_("Outstanding Amount") + ":Currency:120",
		_("Status") + ":Data:80",
	]