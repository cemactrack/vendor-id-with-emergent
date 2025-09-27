from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class BusinessVerificationLevel(str, Enum):
    BASIC = "basic"  # Email verification only
    ENHANCED = "enhanced"  # + phone + address verification
    PREMIUM = "premium"  # + business registration verification
    ENTERPRISE = "enterprise"  # + full compliance verification

class TrustBadgeType(str, Enum):
    EMAIL_VERIFIED = "email_verified"
    PHONE_VERIFIED = "phone_verified"
    ADDRESS_VERIFIED = "address_verified"
    BUSINESS_REGISTERED = "business_registered"
    TAX_COMPLIANT = "tax_compliant"
    CHAMBER_MEMBER = "chamber_member"
    INDUSTRY_CERTIFIED = "industry_certified"
    AWARDS_WINNER = "awards_winner"
    CLIENT_TESTIMONIALS = "client_testimonials"
    PHOTO_VERIFIED = "photo_verified"
    YEARS_ESTABLISHED = "years_established"
    COMPLIANCE_CERTIFIED = "compliance_certified"

class ProfileCompletionStatus(str, Enum):
    INCOMPLETE = "incomplete"  # < 60%
    BASIC = "basic"  # 60-74%
    COMPLETE = "complete"  # 75-89%
    COMPREHENSIVE = "comprehensive"  # 90-100%

class BusinessHours(BaseModel):
    day: str  # monday, tuesday, etc.
    open_time: str  # "09:00"
    close_time: str  # "17:00"
    is_open: bool = True
    break_start: Optional[str] = None  # "12:00"
    break_end: Optional[str] = None  # "13:00"

class BusinessContact(BaseModel):
    contact_type: str  # primary, secondary, support, sales
    contact_person: str
    phone: str
    email: EmailStr
    department: Optional[str] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None

class BusinessPhoto(BaseModel):
    photo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    photo_type: str  # storefront, team, products, certificates, awards
    photo_url: str
    caption: Optional[str] = None
    is_verified: bool = False
    verified_by: Optional[str] = None  # admin user ID
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientTestimonial(BaseModel):
    testimonial_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    client_company: Optional[str] = None
    testimonial_text: str
    rating: float = Field(..., ge=1, le=5)
    project_type: Optional[str] = None
    is_verified: bool = False
    verified_method: Optional[str] = None  # email, phone, linkedin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None

class IndustryCertification(BaseModel):
    certification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    certification_name: str
    certifying_body: str
    certificate_number: Optional[str] = None
    issue_date: datetime
    expiry_date: Optional[datetime] = None
    certificate_url: Optional[str] = None  # Link to certificate image/PDF
    is_verified: bool = False
    verification_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TrustBadge(BaseModel):
    badge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    badge_type: TrustBadgeType
    badge_name: str
    badge_description: str
    is_active: bool = True
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    verification_data: Dict[str, Any] = {}  # Supporting verification data
    display_order: int = 0  # For badge ordering

class ProfileValidationRule(BaseModel):
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str
    field_name: str
    is_mandatory: bool = False
    minimum_length: Optional[int] = None
    validation_pattern: Optional[str] = None  # regex pattern
    verification_required: bool = False
    points_value: int = 0  # Points towards completion score
    category: str = "basic"  # basic, contact, business, verification

class EnhancedVendorProfile(BaseModel):
    """Enhanced vendor profile with comprehensive validation and trust signals"""
    
    # Basic Information
    vendor_id: str
    user_id: str
    business_name: str
    business_description: str
    category: str
    
    # Enhanced Contact Information
    business_hours: List[BusinessHours] = []
    business_contacts: List[BusinessContact] = []
    primary_contact_verified: bool = False
    
    # Visual Trust Signals
    logo_url: Optional[str] = None
    business_photos: List[BusinessPhoto] = []
    photo_gallery_complete: bool = False
    
    # Business Details
    website: Optional[str] = None
    business_address: str
    address_verified: bool = False
    address_verification_method: Optional[str] = None
    address_verified_at: Optional[datetime] = None
    
    # Legal & Compliance
    registration_number: str
    tax_id: str
    established_year: int
    employee_count: int
    
    # Trust & Verification
    verification_level: BusinessVerificationLevel = BusinessVerificationLevel.BASIC
    trust_badges: List[TrustBadge] = []
    client_testimonials: List[ClientTestimonial] = []
    industry_certifications: List[IndustryCertification] = []
    
    # Profile Completion
    profile_completion_score: float = 0.0
    profile_completion_status: ProfileCompletionStatus = ProfileCompletionStatus.INCOMPLETE
    mandatory_fields_complete: bool = False
    last_profile_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    profile_freshness_score: float = 100.0  # Decreases over time
    
    # Quality Scores
    trust_score: float = 0.0
    quality_score: float = 0.0  # Based on completeness, verification, and activity
    visibility_score: float = 0.0  # Affects search ranking
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def calculate_completion_score(self) -> float:
        """Calculate profile completion score based on filled fields and verification"""
        score = 0.0
        total_possible = 100.0
        
        # Basic information (30 points)
        if self.business_name: score += 5
        if self.business_description and len(self.business_description) >= 50: score += 10
        if self.category: score += 5
        if self.logo_url: score += 10
        
        # Contact information (25 points)  
        if self.business_hours: score += 10
        if self.business_contacts: score += 10
        if self.primary_contact_verified: score += 5
        
        # Business details (20 points)
        if self.website: score += 5
        if self.business_address: score += 5
        if self.address_verified: score += 5
        if self.business_photos: score += 5
        
        # Legal & compliance (15 points)
        if self.registration_number: score += 5
        if self.tax_id: score += 5
        if self.established_year: score += 5
        
        # Trust signals (10 points)
        if self.trust_badges: score += 5
        if len(self.business_photos) >= 3: score += 5
        
        return min(score, total_possible)

class ProfileValidationResult(BaseModel):
    vendor_id: str
    is_valid: bool
    completion_score: float
    missing_mandatory_fields: List[str] = []
    validation_errors: List[str] = []
    recommendations: List[str] = []
    trust_score: float = 0.0
    next_verification_level: Optional[BusinessVerificationLevel] = None
    
class AddressVerificationRequest(BaseModel):
    vendor_id: str
    address: str
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    verification_method: str = "google_places"  # google_places, mapbox, manual

class AddressVerificationResult(BaseModel):
    vendor_id: str
    original_address: str
    verified_address: Optional[str] = None
    is_verified: bool = False
    verification_confidence: float = 0.0
    verification_method: str
    coordinates: Optional[Dict[str, float]] = None  # lat, lng
    address_components: Dict[str, str] = {}
    verification_notes: Optional[str] = None
    verified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PhoneVerificationRequest(BaseModel):
    vendor_id: str
    phone_number: str
    country_code: str = "+1"
    verification_method: str = "sms"  # sms, call, whatsapp

class PhoneVerificationResult(BaseModel):
    vendor_id: str
    phone_number: str
    is_verified: bool = False
    verification_code: Optional[str] = None
    verification_method: str
    carrier_info: Optional[Dict[str, str]] = None
    is_mobile: bool = False
    verification_attempts: int = 0
    verified_at: Optional[datetime] = None
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=15))

class ProfileFreshnessCheck(BaseModel):
    vendor_id: str
    last_update: datetime
    days_since_update: int
    freshness_score: float  # 100 for recent, decreases over time
    requires_update: bool = False
    recommended_updates: List[str] = []
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None