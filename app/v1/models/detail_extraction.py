from pydantic import BaseModel, Field
from typing import List

class LineItem(BaseModel):
    desc: str = ""
    qty: float = 0.0
    price: float = 0.0
    total: float = 0.0

class InvoiceResponse(BaseModel):
    billing_address: str = ""
    shipping_address: str = ""
    invoice_type: str = ""
    order_number: str = ""
    invoice_number: str = ""
    order_date: str = ""
    invoice_details: str = ""
    invoice_date: str = ""
    seller_info: str = ""
    seller_pan: str = ""
    seller_gst: str = ""
    fssai_license: str = "Not mentioned"
    billing_state_code: str = ""
    shipping_state_code: str = ""
    place_of_supply: str = ""
    place_of_delivery: str = ""
    reverse_charge: str = "No"
    amount_in_words: str = ""
    seller_name: str = ""
    seller_address: str = ""
    total_tax: str = ""
    total_amount: str = ""
    line_items: List[LineItem] = Field(default_factory=list)

class InvoiceData(InvoiceResponse):
    pass
