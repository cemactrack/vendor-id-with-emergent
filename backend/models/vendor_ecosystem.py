from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import re

class CountryCode(str, Enum):
    NIGERIA = "NG"
    CAMEROON = "CM"
    USA = "US"
    GHANA = "GH"
    KENYA = "KE"
    SOUTH_AFRICA = "ZA"
    UK = "GB"
    CANADA = "CA"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    REJECTED = "rejected"

class UserRole(str, Enum):
    VENDOR = "vendor"
    VERIFICATION_OFFICER = "verification_officer"
    REGIONAL_ADMIN = "regional_admin"
    SYSTEM_ADMIN = "system_admin"
    CUSTOMER = "customer"

class BusinessCategory(str, Enum):
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    AGRICULTURE = "agriculture"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    RETAIL = "retail"
    SERVICES = "services"
    CONSTRUCTION = "construction"
    LOGISTICS = "logistics"
    FOOD_BEVERAGE = "food_beverage"
    AUTOMOTIVE = "automotive"
    TEXTILE = "textile"
    ENERGY = "energy"
    REAL_ESTATE = "real_estate"
    OTHER = "other"

class DocumentType(str, Enum):
    BUSINESS_REGISTRATION = "business_registration"
    TAX_ID = "tax_id"
    OPERATING_LICENSE = "operating_license"
    OWNER_ID = "owner_id"
    BANK_STATEMENT = "bank_statement"
    UTILITY_BILL = "utility_bill"
    COMPANY_PROFILE = "company_profile"
    CERTIFICATION = "certification"

# User Management Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    country: CountryCode
    role: UserRole = UserRole.VENDOR
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                raise ValueError('Phone number must be between 10-15 digits')
            return phone_digits
        return v

class User(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    country: CountryCode
    role: UserRole
    is_active: bool = True
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

# Document Management Models
class DocumentUpload(BaseModel):
    document_type: DocumentType
    file_path: str
    original_filename: str
    file_size: int
    mime_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class DocumentCreate(BaseModel):
    document_type: DocumentType
    file_data: str  # Base64 encoded file data
    filename: str
    description: Optional[str] = None

class Document(BaseModel):
    id: str
    vendor_id: str
    document_type: DocumentType
    file_path: str
    original_filename: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    uploaded_at: datetime
    expires_at: Optional[datetime] = None

# Vendor Profile Models
class VendorProfileCreate(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=200)
    business_description: Optional[str] = Field(None, max_length=1000)
    category: BusinessCategory
    website: Optional[str] = None
    business_address: str = Field(..., min_length=10, max_length=500)
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    established_year: Optional[int] = None
    employee_count: Optional[int] = None
    
    @validator('website')
    def validate_website(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v
    
    @validator('established_year')
    def validate_established_year(cls, v):
        if v and (v < 1800 or v > datetime.now().year):
            raise ValueError('Invalid establishment year')
        return v

class VendorProfile(BaseModel):
    id: str
    user_id: str
    vendor_id: str  # Auto-generated VID-XX-XXXX
    business_name: str
    business_description: Optional[str] = None
    category: BusinessCategory
    logo_url: Optional[str] = None
    website: Optional[str] = None
    business_address: str
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    established_year: Optional[int] = None
    employee_count: Optional[int] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_level: int = 0  # 0-5 trust levels
    trust_score: float = 0.0  # 0-100 trust score
    profile_completion: float = 0.0  # 0-100 completion percentage
    created_at: datetime
    updated_at: datetime
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

# Service Listing Models
class ServiceListingCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    category: BusinessCategory
    subcategory: Optional[str] = None
    price_range: Optional[str] = None  # e.g., "$100-$500", "Contact for quote"
    service_type: str = Field(..., max_length=100)  # e.g., "Consultation", "Product"
    availability: str = "available"  # available, unavailable, by_appointment
    location_served: List[str] = []  # Geographic areas served
    tags: List[str] = []
    images: List[str] = []  # Image URLs
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return [tag.lower().strip() for tag in v if tag.strip()]

class ServiceListing(BaseModel):
    id: str
    vendor_id: str
    title: str
    description: str
    category: BusinessCategory
    subcategory: Optional[str] = None
    price_range: Optional[str] = None
    service_type: str
    availability: str
    location_served: List[str]
    tags: List[str]
    images: List[str]
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    views_count: int = 0
    inquiries_count: int = 0
    created_at: datetime
    updated_at: datetime
    featured_until: Optional[datetime] = None

# Verification Workflow Models
class VerificationRequest(BaseModel):
    id: str
    vendor_id: str
    requested_by: str
    verification_type: str = "full_verification"  # full_verification, document_update, renewal
    required_documents: List[DocumentType]
    submitted_documents: List[str] = []  # Document IDs
    status: VerificationStatus = VerificationStatus.PENDING
    priority: int = 1  # 1-5, higher is more urgent
    assigned_officer: Optional[str] = None
    notes: Optional[str] = None
    verification_checklist: Dict[str, bool] = {}
    created_at: datetime
    updated_at: datetime
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class VerificationAction(BaseModel):
    id: str
    verification_request_id: str
    officer_id: str
    action_type: str  # "document_review", "status_change", "note_added", "request_info"
    description: str
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Analytics Models
class VendorAnalytics(BaseModel):
    vendor_id: str
    profile_views: int = 0
    listing_views: int = 0
    listing_inquiries: int = 0
    qr_scans: int = 0
    verification_checks: int = 0
    trust_score_history: List[Dict[str, Any]] = []
    monthly_stats: Dict[str, Dict[str, int]] = {}
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Marketplace Integration Models
class MarketplaceIntegration(BaseModel):
    id: str
    vendor_id: str
    platform_name: str  # "Shopify", "Amazon", "eBay", etc.
    platform_url: str
    integration_type: str  # "trust_badge", "verification_api", "profile_sync"
    api_credentials: Dict[str, str] = {}  # Encrypted
    sync_settings: Dict[str, Any] = {}
    is_active: bool = True
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# Fraud and Compliance Models
class FraudReport(BaseModel):
    id: str
    reporter_id: Optional[str] = None  # Anonymous reports allowed
    reported_vendor_id: str
    report_type: str  # "fake_documents", "impersonation", "fraudulent_activity"
    description: str = Field(..., min_length=20, max_length=1000)
    evidence_files: List[str] = []
    status: str = "open"  # open, investigating, resolved, dismissed
    priority: int = 1  # 1-5
    assigned_investigator: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

class TrustEvent(BaseModel):
    id: str
    vendor_id: str
    event_type: str  # "verification_completed", "document_expired", "fraud_reported", "positive_review"
    impact_score: float  # -100 to +100
    description: str
    source: str  # "system", "manual", "external_api"
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Response Models
class VendorEcosystemStats(BaseModel):
    total_vendors: int
    verified_vendors: int
    pending_verification: int
    active_listings: int
    total_documents: int
    trust_score_average: float
    countries_represented: int
    categories_covered: int
    verification_requests_pending: int = 0
    fraud_reports_open: int = 0

class VendorDashboardData(BaseModel):
    profile: VendorProfile
    analytics: VendorAnalytics
    active_listings: List[ServiceListing]
    verification_status: VerificationRequest
    trust_events: List[TrustEvent]
    integrations: List[MarketplaceIntegration]

class PublicVendorVerification(BaseModel):
    vendor_id: str
    business_name: str
    verification_status: VerificationStatus
    trust_score: float
    verification_level: int
    verified_since: Optional[datetime] = None
    categories: List[BusinessCategory]
    location: str
    qr_verification_url: str