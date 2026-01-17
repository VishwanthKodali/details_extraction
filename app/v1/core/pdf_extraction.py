import pdfplumber
import re
import io
from app.v1.models.detail_extraction import InvoiceData

def extract_block(text: str, start: str, end: str, max_lines=10) -> str:
    lines = text.splitlines()
    capture = False
    block = []

    for line in lines:
        if start.lower() in line.lower():
            capture = True
            continue
        if capture:
            if end.lower() in line.lower():
                break
            block.append(line.strip())
            if len(block) >= max_lines:
                break

    return " ".join([l for l in block if l])

async def extract_invoice_data(pdf_bytes: bytes) -> InvoiceData:
    data = InvoiceData()

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    # ---------- HEADER ----------
    match = re.search(r"Order Number:\s*([\d\-]+)", text)
    data.order_number = match.group(1) if match else ""
    match = re.search(r"Invoice Number\s*:\s*([A-Z0-9\-]+)", text)
    data.invoice_number = match.group(1) if match else ""
    match = re.search(r"Order Date:\s*([\d.]+)", text)
    data.order_date = match.group(1) if match else ""
    match = re.search(r"Invoice Date\s*:\s*([\d.]+)", text)
    data.invoice_date = match.group(1) if match else ""
    match = re.search(r"(HR-[A-Z0-9\-]+)", text)
    data.invoice_details = match.group(1) if match else ""

    data.invoice_type = "Cash Memo" if "Cash Memo" in text else "Tax Invoice"

    # ---------- SELLER ----------
    seller_block = extract_block(
        text,
        start="Sold By",
        end="Billing Address"
    )

    seller_lines = seller_block.split(",")
    data.seller_name = seller_lines[0].strip()
    data.seller_address = seller_block
    data.seller_info = seller_block

    match = re.search(r"PAN No:\s*([A-Z0-9]+)", text)
    data.seller_pan = match.group(1) if match else ""
    match = re.search(r"GST Registration No:\s*([A-Z0-9]+)", text)
    data.seller_gst = match.group(1) if match else ""

    # ---------- BILLING ----------
    billing_block = extract_block(
        text,
        start="Billing Address",
        end="Shipping Address"
    )
    data.billing_address = billing_block

    # ---------- SHIPPING ----------
    shipping_block = extract_block(
        text,
        start="Shipping Address",
        end="State/UT Code"
    )
    data.shipping_address = shipping_block

    # ---------- STATE & PLACE ----------
    match = re.search(r"State/UT Code:\s*(\d{2})", text)
    state = match.group(1) if match else ""
    data.billing_state_code = state
    data.shipping_state_code = state

    match = re.search(r"Place of supply:\s*([A-Z ]+)", text)
    data.place_of_supply = match.group(1).title() if match else ""

    match = re.search(r"Place of delivery:\s*([A-Z ]+)", text)
    data.place_of_delivery = match.group(1).title() if match else ""

    # ---------- TOTALS (TABLE TRUSTED) ----------
    amounts = re.findall(r"₹\s*([\d]+\.\d{2})", text)
    # Amazon footer always: tax first, then total
    if len(amounts) >= 2:
        data.total_tax = f"₹{amounts[-2]}"
        data.total_amount = f"₹{amounts[-1]}"
    else:
        data.total_tax = ""
        data.total_amount = ""

    match = re.search(r"Amount in Words:\s*(.+)", text)
    data.amount_in_words = match.group(1) if match else ""

    return data
