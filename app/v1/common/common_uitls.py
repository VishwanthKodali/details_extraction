import openpyxl
from pathlib import Path
from app.v1.core.pdf_extraction import extract_invoice_data

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

async def create_excel_from_pdf(pdf_bytes: bytes, filename: str):
    data = await extract_invoice_data(pdf_bytes)

    excel_path = OUTPUT_DIR / f"{filename}.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoice Data"

    ws.append(["Field", "Value"])

    for key, value in data.model_dump().items():
        if key != "line_items":
            ws.append([key, value])

    wb.save(excel_path)
    return excel_path

def create_excel_file(data: dict, output_path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoice Data"

    ws.append(["Field", "Value"])
    for k, v in data.items():
        if k != "line_items":
            ws.append([k, v])

    wb.save(output_path)
    return output_path
