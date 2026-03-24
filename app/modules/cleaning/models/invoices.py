"""
CleanClaw v3 — Invoice & InvoiceItem Pydantic models.
Maps to: cleaning_invoices + cleaning_invoice_items tables (migration 011).
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================
# INVOICE ITEM — CREATE
# ============================================

class InvoiceItemCreate(BaseModel):
    """Line item for an invoice."""
    service_id: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(default=1.0, ge=0.01)
    unit_price: float = Field(..., ge=0)
    sort_order: int = Field(default=0, ge=0)


# ============================================
# INVOICE ITEM — RESPONSE
# ============================================

class InvoiceItemResponse(BaseModel):
    """API response model for an invoice line item."""
    id: str
    invoice_id: str
    business_id: str
    service_id: Optional[str] = None
    description: str
    quantity: float
    unit_price: float
    total: float
    sort_order: int
    created_at: str


# ============================================
# INVOICE — CREATE
# ============================================

class InvoiceCreate(BaseModel):
    """Input model for creating an invoice."""
    client_id: str
    booking_id: Optional[str] = None
    invoice_number: Optional[str] = Field(
        None, max_length=50,
        description="Human-readable number. Auto-generated if omitted."
    )
    # Amounts
    subtotal: float = Field(default=0.0, ge=0)
    tax_rate: float = Field(default=0.0, ge=0, le=1.0)
    tax_amount: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    total: float = Field(default=0.0, ge=0)
    # Dates
    issue_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    due_date: str  # YYYY-MM-DD (required)
    # Content
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    # Items
    items: list[InvoiceItemCreate] = Field(
        default_factory=list,
        description="Line items for this invoice."
    )


# ============================================
# INVOICE — UPDATE
# ============================================

class InvoiceUpdate(BaseModel):
    """Partial update model for an invoice."""
    subtotal: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=1.0)
    tax_amount: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    amount_paid: Optional[float] = Field(None, ge=0)
    due_date: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(draft|sent|viewed|paid|partial|overdue|void|refunded)$"
    )
    payment_method: Optional[str] = Field(None, max_length=30)
    payment_reference: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


# ============================================
# INVOICE — RESPONSE
# ============================================

class InvoiceResponse(BaseModel):
    """API response model for an invoice."""
    id: str
    business_id: str
    client_id: str
    booking_id: Optional[str] = None
    invoice_number: str
    # Amounts
    subtotal: float
    tax_rate: float
    tax_amount: float
    discount_amount: float
    total: float
    amount_paid: float
    balance_due: float
    # Dates
    issue_date: str
    due_date: str
    paid_at: Optional[str] = None
    # Status
    status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    # Content
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    pdf_url: Optional[str] = None
    # Items (populated when fetching single invoice)
    items: list[InvoiceItemResponse] = []
    created_at: str
    updated_at: str


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""
    invoices: list[InvoiceResponse]
    total: int
