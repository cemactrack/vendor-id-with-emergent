from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

# Enums for Escrow System
class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_SUBMITTED = "payment_submitted"
    PAYMENT_CONFIRMED = "payment_confirmed"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    MANUAL_PAYMENT = "manual_payment"
    CASH_DEPOSIT = "cash_deposit"
    MOBILE_MONEY = "mobile_money"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"

class DisputeStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"

class DisputeOutcome(str, Enum):
    PENDING = "pending"
    CUSTOMER_FAVOR = "customer_favor"
    VENDOR_FAVOR = "vendor_favor"
    PARTIAL_REFUND = "partial_refund"
    MUTUAL_AGREEMENT = "mutual_agreement"

class EscrowStatus(str, Enum):
    WAITING_PAYMENT = "waiting_payment"
    FUNDS_HELD = "funds_held"
    RELEASED_TO_VENDOR = "released_to_vendor"
    REFUNDED_TO_CUSTOMER = "refunded_to_customer"
    PARTIAL_REFUND = "partial_refund"
    DISPUTED = "disputed"

# Currency Support
class SupportedCurrency(str, Enum):
    USD = "USD"  # US Dollar
    NGN = "NGN"  # Nigerian Naira
    GHS = "GHS"  # Ghanaian Cedi
    KES = "KES"  # Kenyan Shilling
    ZAR = "ZAR"  # South African Rand
    GBP = "GBP"  # British Pound
    EUR = "EUR"  # Euro
    CAD = "CAD"  # Canadian Dollar

# Order Models
class OrderItemCreate(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)
    currency: SupportedCurrency
    
class OrderItem(OrderItemCreate):
    item_id: str
    total_price: float

class OrderCreate(BaseModel):
    vendor_id: str
    items: List[OrderItemCreate]
    delivery_address: str = Field(..., min_length=10, max_length=500)
    special_instructions: Optional[str] = Field(None, max_length=500)
    expected_delivery_date: Optional[datetime] = None
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 items per order")
        return v

class Order(BaseModel):
    order_id: str
    customer_id: str
    vendor_id: str
    items: List[OrderItem]
    subtotal: float
    platform_fee: float
    total_amount: float
    currency: SupportedCurrency
    delivery_address: str
    special_instructions: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Payment Models
class PaymentInstructionCreate(BaseModel):
    payment_method: PaymentMethod
    bank_details: Optional[Dict[str, str]] = None
    reference_number: Optional[str] = None
    amount: float
    currency: SupportedCurrency

class PaymentInstruction(PaymentInstructionCreate):
    instruction_id: str
    order_id: str
    status: PaymentStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[str] = None  # Admin user ID
    payment_proof: Optional[str] = None  # File path to proof

class PaymentProofSubmission(BaseModel):
    instruction_id: str
    reference_number: str
    payment_date: datetime
    notes: Optional[str] = None
    proof_files: List[str] = []  # File paths

# Escrow Models
class EscrowAccount(BaseModel):
    escrow_id: str
    order_id: str
    customer_id: str
    vendor_id: str
    amount: float
    currency: SupportedCurrency
    platform_fee: float
    vendor_amount: float  # Amount after platform fee
    status: EscrowStatus
    created_at: datetime
    auto_release_date: datetime
    extension_requests: List[Dict[str, Any]] = []
    released_at: Optional[datetime] = None
    released_by: Optional[str] = None
    release_method: Optional[str] = None

class EscrowExtensionRequest(BaseModel):
    extension_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    requested_by: str  # customer_id or vendor_id
    requester_type: str  # "customer" or "vendor"
    extension_days: int = Field(..., ge=1, le=30)
    reason: str = Field(..., min_length=10, max_length=500)
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

# Dispute Models
class DisputeCreate(BaseModel):
    order_id: str
    reason: str = Field(..., min_length=10, max_length=1000)
    evidence_description: str = Field(..., min_length=10, max_length=2000)
    evidence_files: List[str] = []
    requested_outcome: str = Field(..., min_length=5, max_length=500)

class DisputeEvidence(BaseModel):
    evidence_id: str
    dispute_id: str
    submitted_by: str  # customer_id or vendor_id
    submitter_type: str  # "customer" or "vendor"
    description: str
    files: List[str] = []
    submitted_at: datetime

class DisputeResolution(BaseModel):
    resolution_id: str
    dispute_id: str
    resolved_by: str  # admin user ID
    outcome: DisputeOutcome
    customer_refund_amount: float = 0.0
    vendor_payout_amount: float = 0.0
    resolution_notes: str
    evidence_reviewed: List[str] = []
    resolved_at: datetime

class Dispute(BaseModel):
    dispute_id: str
    order_id: str
    customer_id: str
    vendor_id: str
    reason: str
    evidence_description: str
    evidence_files: List[str] = []
    requested_outcome: str
    status: DisputeStatus
    outcome: DisputeOutcome = DisputeOutcome.PENDING
    priority: int = 1  # 1-5, 5 being highest priority
    auto_resolution_eligible: bool = False
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[DisputeResolution] = None
    evidence: List[DisputeEvidence] = []

# Transaction History Models
class TransactionType(str, Enum):
    ESCROW_DEPOSIT = "escrow_deposit"
    ESCROW_RELEASE = "escrow_release"
    PLATFORM_FEE = "platform_fee"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    DISPUTE_RESOLUTION = "dispute_resolution"

class Transaction(BaseModel):
    transaction_id: str
    order_id: str
    escrow_id: Optional[str] = None
    transaction_type: TransactionType
    amount: float
    currency: SupportedCurrency
    from_party: str  # customer_id, vendor_id, or "platform"
    to_party: str    # customer_id, vendor_id, or "platform"
    description: str
    reference_number: Optional[str] = None
    processed_by: Optional[str] = None  # admin user ID for manual transactions
    created_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

# Dashboard Models
class OrderSummary(BaseModel):
    total_orders: int
    pending_payment: int
    in_progress: int
    completed: int
    disputed: int
    total_value: float
    currency: SupportedCurrency

class EscrowSummary(BaseModel):
    total_escrows: int
    funds_held: float
    pending_release: int
    disputed_funds: float
    currency: SupportedCurrency

class DisputeSummary(BaseModel):
    total_disputes: int
    open_disputes: int
    resolved_today: int
    average_resolution_time_hours: float

# Admin Models
class EscrowDashboardStats(BaseModel):
    order_summary: OrderSummary
    escrow_summary: EscrowSummary
    dispute_summary: DisputeSummary
    recent_transactions: List[Transaction]
    pending_payment_confirmations: int
    auto_releases_today: int

# API Response Models
class OrderResponse(BaseModel):
    order: Order
    escrow: Optional[EscrowAccount] = None
    payment_instructions: Optional[PaymentInstruction] = None
    message: str

class PaymentConfirmationResponse(BaseModel):
    order: Order
    escrow: EscrowAccount
    message: str

class DisputeResponse(BaseModel):
    dispute: Dispute
    message: str

# Notification Models
class EscrowNotificationType(str, Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_SUBMITTED = "payment_submitted"
    PAYMENT_CONFIRMED = "payment_confirmed"
    ORDER_DELIVERED = "order_delivered"
    FUNDS_RELEASED = "funds_released"
    DISPUTE_CREATED = "dispute_created"
    DISPUTE_RESOLVED = "dispute_resolved"
    AUTO_RELEASE_PENDING = "auto_release_pending"
    EXTENSION_REQUESTED = "extension_requested"

class EscrowNotification(BaseModel):
    notification_id: str
    order_id: str
    recipient_id: str  # customer_id or vendor_id
    recipient_type: str  # "customer" or "vendor"
    notification_type: EscrowNotificationType
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool = False
    created_at: datetime