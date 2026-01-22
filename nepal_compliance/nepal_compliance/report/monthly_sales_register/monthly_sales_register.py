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

	query = f"""
		SELECT
			si.posting_date,
			si.customer,
			COALESCE(si.vat_number, si.tax_id) AS vat_pan_number,
			si.name AS invoice_number,
			(SELECT SUM(qty) FROM `tabSales Invoice Item` WHERE parent = si.name) AS total_qty,
			(SELECT SUM(qty * rate) FROM `tabSales Invoice Item` WHERE parent = si.name) AS total_amount,
			(SELECT COALESCE(SUM(tax_amount), 0) FROM `tabSales Taxes and Charges` WHERE parent = si.name AND docstatus = 1) AS tax_amount,
			si.discount_amount,
			si.total,
			si.net_total,
			si.grand_total,
			si.outstanding_amount,
			si.status
		FROM `tabSales Invoice` si
		WHERE
			si.docstatus = 1
			{conditions}
		ORDER BY si.posting_date DESC
	"""

	rows = frappe.db.sql(query, values, as_dict=True)

	target_month = NEPALI_MONTH_MAP.get(filters.get("nepali_month"))

	for r in rows:
		bs = ad_to_bs(r.posting_date)

		if target_month and bs["month"] != target_month:
			continue

		data.append([
			bs_date(r.posting_date),
			r.customer,
			r.vat_pan_number,
			r.invoice_number,
			r.total_qty,
			r.total_amount,
			r.tax_amount,
			r.discount_amount,
			r.total,
			r.net_total,
			r.grand_total,
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

	fy = frappe.get_all(
		"Fiscal Year",
		filters={
			"company": filters["company"],
			"disabled": 0
		},
		fields=["name", "year_start_date", "year_end_date"],
		order_by="year_start_date desc",
		limit=1
	)

	if not fy:
		frappe.throw(_("No Fiscal Year found for company"))

	return frappe.get_doc("Fiscal Year", fy[0].name)


def build_conditions(filters, fy):
	conditions = []
	values = {}

	conditions.append(
		"AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
	)

	values["from_date"] = fy.year_start_date
	values["to_date"] = fy.year_end_date

	if filters.get("customer"):
		conditions.append("AND si.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("company"):
		conditions.append("AND si.company = %(company)s")
		values["company"] = filters["company"]

	return " ".join(conditions), values


def get_columns():
	return [
		_("Invoice Date (BS)") + ":Data:150",
		_("Customer") + ":Link/Customer:150",
		_("VAT/PAN Number") + ":Data:120",
		_("Invoice Number") + ":Link/Sales Invoice:200",
		_("Qty") + ":Float:60",
		_("Amount") + ":Currency:100",
		_("Tax Amount") + ":Currency:120",
		_("Discount") + ":Currency:120",
		_("Total") + ":Currency:120",
		_("Net Total") + ":Currency:120",
		_("Grand Total") + ":Currency:120",
		_("Outstanding Amount") + ":Currency:120",
		_("Status") + ":Data:80",
	]
