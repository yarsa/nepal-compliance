# openpyxl 3.1.5 - MIT License, (c) 2024, Eric Gazoni, Charlie Clark, See License at https://pypi.org/project/openpyxl/

import frappe
from frappe import _
from frappe.utils import flt
import json
import openpyxl
from frappe.utils import get_site_path
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

def convert_to_nepali_fy_format(fy_name):
    """
    Converts a Gregorian fiscal year string to Nepali fiscal year format.
    
    If the input is already in Nepali format (contains "/" and the first part is 4 digits), it is returned unchanged. Otherwise, the function adds 57 years to each part of a "YYYY-YYYY" string and returns the result as "YYYY/YY". If conversion fails, the original input is returned.
    
    Parameters:
        fy_name (str): Fiscal year in Gregorian format (e.g., "2023-2024") or already in Nepali format.
    
    Returns:
        str: Fiscal year in Nepali format (e.g., "2080/81") or the original input if conversion is not possible.
    """
    if "/" in fy_name and len(fy_name.split("/")[0]) == 4:
        return fy_name
    try:
        start, end = [int(x) for x in fy_name.split("-")]
        nep_start = start + 57
        nep_end = end + 57
        return f"{nep_start}/{str(nep_end)[-2:]}"
    except Exception:
        return fy_name

@frappe.whitelist()
def generate_ird_sales_register_excel():
    """
    Generates and saves an IRD-compliant sales register Excel report with Nepali fiscal year formatting.
    
    The report includes company details, PAN, and fiscal year, and organizes sales register data into a structured, styled Excel sheet with merged headers, sub-headers, and totals. The generated file is saved to the site's public files directory and the relative URL path is returned.
    
    Returns:
        str: Relative URL path to the generated Excel file.
    """
    from nepal_compliance.nepal_compliance.report.sales_register_ird.sales_register_ird import get_data

    filters = frappe._dict(json.loads(frappe.form_dict.get("filters") or "{}"))
    rows = get_data(filters)

    if not rows:
        frappe.throw(_("No data found for the selected filters."))

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
    ws.title = "Sales Register"

    bold_center = Font(bold=True)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    def format_cell(cell):
        """
        Apply bold font, centered alignment, and a thin border to the given Excel cell.
        """
        cell.alignment = center
        cell.font = bold_center
        cell.border = border

    ws.merge_cells("A1:L1")
    ws["A1"] = "बिक्री खाता"
    ws["A1"].font = Font(bold=True, size=16)
    ws.merge_cells("A2:L2")
    ws["A2"] = "(नियम २३ को उपनियम (१) को खण्ड  (छ) संग सम्बन्धित )"
    ws["A2"].font = Font(bold=False)
    ws.merge_cells("A3:L3")
    ws["A3"] = ""
    ws.merge_cells("A4:L4")
    ws["A4"] = f"करदाता दर्ता नं (PAN): {pan}        करदाताको नाम: {company_name}         आर्थिक वर्ष: {convert_to_nepali_fy_format(fiscal_year)}"

    for r in range(1, 5):
        top_cell = ws.cell(row=r, column=1)
        top_cell.font = bold_center
        top_cell.alignment = center

    top_headers = [
        ("बीजक", 4),
        ("जम्मा बिक्री / निकासी (रु)", 1),
        ("स्थानीय कर छुटको बिक्री  मूल्य (रु)", 1),
        ("करयोग्य बिक्री", 2),
        ("निकासी", 4)
    ]

    sub_headers = [
        "मिति", "बीजक नम्बर", "खरिदकर्ताको नाम", "खरिदकर्ताको स्थायी लेखा नम्बर",
        "मूल्य (रु)", "कर (रु)",
        "निकासी गरेको वस्तु वा सेवाको मूल्य (रु)", "निकासी गरेको देश",
        "निकासी प्रज्ञापनपत्र नम्बर", "निकासी प्रज्ञापनपत्र मिति"
    ]

    col = 1
    sub_idx = 0

    for title, span in top_headers:
        if span == 1:
            ws.merge_cells(start_row=5, start_column=col, end_row=6, end_column=col)
            cell = ws.cell(row=5, column=col, value=title)
            format_cell(cell)
            col += 1
        else:
            ws.merge_cells(start_row=5, start_column=col, end_row=5, end_column=col + span - 1)
            cell = ws.cell(row=5, column=col, value=title)
            format_cell(cell)
            for i in range(span):
                sub_cell = ws.cell(row=6, column=col + i, value=sub_headers[sub_idx])
                format_cell(sub_cell)
                sub_idx += 1
            col += span

    data_start_row = 7
    for row_idx, inv in enumerate(rows, start=data_start_row):
        row_data = [
            inv.get("nepali_date"),
            inv.get("invoice"),
            inv.get("customer_name"),
            inv.get("pan"),
            inv.get("total"),
            inv.get("tax_exempt"),
            inv.get("taxable_amount"),
            inv.get("tax_amount"),
            inv.get("Value of Exported Goods or Services"),
            inv.get("export_country"),
            inv.get("Export Declaration Number"),
            inv.get("Export Declaration Date")
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = center
            cell.border = border
            if isinstance(val, (int, float)):
                cell.number_format = '#,##0.00'

    total_row = len(rows) + data_start_row
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=4)
    total_label_cell = ws.cell(row=total_row, column=1, value="Total")
    format_cell(total_label_cell)

    for col in range(5, 10):
        col_letter = get_column_letter(col)
        formula = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row - 1})"
        total_cell = ws.cell(row=total_row, column=col, value=formula)
        total_cell.border = border
        total_cell.alignment = center
        total_cell.number_format = '#,##0.00'

    for col in range(10, 13): 
        cell = ws.cell(row=total_row, column=col, value="")
        cell.border = border
        cell.alignment = center

    for col_cells in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = max_len + 4

    file_name = "IRD_Sales_Register.xlsx"
    path = get_site_path("public", "files", file_name)
    wb.save(path)
    return f"/files/{file_name}"
