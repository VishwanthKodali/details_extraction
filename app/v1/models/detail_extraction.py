from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class LineItem(BaseModel):
    desc: str
    qty: float = Field(..., ge=0)
    price: float = Field(..., ge=0)
    total: float = Field(..., ge=0)

class InvoiceResponse(BaseModel):
    invoice_number: Optional[str]
    date: Optional[str]
    total: Optional[float]
    line_items: List[LineItem] = []

class ExtractionRequest(BaseModel):
    pdf_bytes: bytes