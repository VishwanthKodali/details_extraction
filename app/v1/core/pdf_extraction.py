import pdfplumber
import re
import io
from typing import Dict, List, Any
from datetime import datetime
import pytesseract
from PIL import Image
import asyncio

async def extract_invoice_data(pdf_bytes: bytes) -> Dict[str, Any]:
    """Async multi-method PDF extraction."""
    loop = asyncio.get_event_loop()
    
    # Method 1: Text + Regex (native PDFs)
    def text_extract():
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            tables = [t for p in pdf.pages for t in (p.extract_tables() or [])]
        return text, tables
    
    text, tables = await loop.run_in_executor(None, text_extract)
    
    data = {
        'invoice_number': re.search(r'(?:Invoice|Bill)\s*[#:]?\s*(\w+)', text, re.I),
        'date': re.search(r'(Date|Inv Date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.I),
        'total': re.search(r'Total[:\s]*\$?([\d,]+\.?\d*)', text, re.I),
        'line_items': []
    }
    
    # Method 2: Tables
    if tables and tables[0]:
        for row in tables[0][1:]:  # Skip header
            if len(row) >= 4 and all(row[:4]):
                data['line_items'].append({
                    'desc': row[0], 'qty': float(row[1] or 0),
                    'price': float(row[2] or 0), 'total': float(row[3] or 0)
                })
    
    # Method 3: OCR fallback for images/charts (if low text yield)
    if len(text.strip()) < 100:
        img = Image.open(io.BytesIO(pdf_bytes))
        ocr_text = pytesseract.image_to_string(img)
        # Re-run regex on ocr_text
    
    # Parse matches
    for key, match in data.items():
        if match:
            data[key] = match.group(1).strip()
    
    return data
