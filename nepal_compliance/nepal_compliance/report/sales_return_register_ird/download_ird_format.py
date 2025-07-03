import frappe
import json
import openpyxl
from frappe.utils import get_site_path
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

def convert_to_nepali_fy_format(fy_name):
    if "/" in fy_name and len(fy_name.split("/")[0]) == 4:
        return fy_name
    try:
        start, end = map(int, fy_name.split("-"))
        nep_start = start + 57
        nep_end = end + 57
        return f"{nep_start}/{str(nep_end)[-2:]}"
    except Exception:
        return fy_name

@frappe.whitelist()
def generate_ird_purchase_register_excel():
    from nepal_compliance.nepal_compliance.report.sales_return_register_ird.sales_return_register_ird import get_data

    filters = frappe._dict(json.loads(frappe.form_dict.get("filters") or "{}"))
    rows = get_data(filters)

    if not rows:
        frappe.throw("No data found for the selected filters.")

    company = filters.get("company")
    company_info = frappe.get_doc("Company", company) if company else None
    company_name = company_info.company_name if company_info else "Company Name"

    address = frappe.db.get_value(
        "Address",
        {"is_your_company_address": 1},
        "address_line1"
    ) or ""

    pan = company_info.tax_id or "N/A"
    posting_date = frappe.utils.nowdate()
    fiscal_year = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ["<=", posting_date],
            "year_end_date": [">=", posting_date]
        },
        "name"
    ) or "Fiscal Year"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Return Register"

    bold_center = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    def format_cell(cell):
        cell.alignment = center
        cell.font = bold_center
        cell.border = border

    ws.merge_cells("A1:K1")
    ws["A1"] = company_name
    ws.merge_cells("A2:K2")
    ws["A2"] = address
    ws.merge_cells("A3:K3")
    ws["A3"] = f"बिक्री फिर्ता खाता,  करदाता दर्ता नं (PAN): {pan}"
    ws.merge_cells("A4:K4")
    ws["A4"] = f"कर अवधि : {convert_to_nepali_fy_format(fiscal_year)}"

    for r in range(1, 5):
        top_cell = ws.cell(row=r, column=1)
        top_cell.font = bold_center
        top_cell.alignment = center

    top_headers = [
        ("बीजक", 7),
        ("जम्मा फिर्ता (रु)", 1),
        ("स्थानीय कर छुटको फिर्ता मूल्य (रु)", 1),
        ("करयोग्य फिर्ता", 2),
    ]

    sub_headers = [
        "मिति", "बीजक नं.", "खरिदकर्ताको नाम", "खरिदकर्ताको स्थायी लेखा नम्बर",
        "वस्तु वा सेवाको नाम", "वस्तु वा सेवाको परिमाण", "वस्तु वा सेवाको एकाइ",
        "", "",
        "मूल्य (रु)", "कर (रु)"
    ]

    col = 1
    sub_idx = 0

    for title, span in top_headers:
        if span == 1:
            ws.merge_cells(start_row=5, start_column=col, end_row=6, end_column=col)
            cell = ws.cell(row=5, column=col)
            cell.value = title
            format_cell(cell)
            col += 1
        else:
            ws.merge_cells(start_row=5, start_column=col, end_row=5, end_column=col + span - 1)
            cell = ws.cell(row=5, column=col)
            cell.value = title
            format_cell(cell)
            for i in range(span):
                sub_cell = ws.cell(row=6, column=col + i)
                sub_cell.value = sub_headers[sub_idx]
                format_cell(sub_cell)
                sub_idx += 1
            col += span

    data_start_row = 7
    for row_idx, inv in enumerate(rows, start=data_start_row):
        row_data = [
            inv.get("nepali_date"), inv.get("invoice"), inv.get("customer_name"), inv.get("pan"),
            inv.get("name"), inv.get("qty"), inv.get("uom"),
            inv.get("total"), inv.get("tax_exempt"),
            inv.get("taxable_amount"), inv.get("tax_amount")
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = center
            cell.border = border
            if isinstance(val, (int, float)):
                cell.number_format = '#,##0.00'

    total_row = len(rows) + data_start_row
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=7)
    total_label_cell = ws.cell(row=total_row, column=1, value="Total")
    format_cell(total_label_cell)

    for col in range(8, 12):
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row - 1})"
        total_cell = ws.cell(row=total_row, column=col, value=formula)
        total_cell.border = border
        total_cell.alignment = center
        total_cell.number_format = '#,##0.00'

    for col_cells in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = max_len + 4

    file_name = "IRD_Sales_Return_Register.xlsx"
    path = get_site_path("public", "files", file_name)
    wb.save(path)
    return f"/files/{file_name}"
