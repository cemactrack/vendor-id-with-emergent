from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, time
from enum import Enum
import uuid

class ServiceCategory(str, Enum):
    TECHNOLOGY = "technology"
    CONSULTING = "consulting"
    MARKETING = "marketing"
    DESIGN = "design"
    CONSTRUCTION = "construction"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    LEGAL = "legal"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HOSPITALITY = "hospitality"
    TRANSPORTATION = "transportation"
    AGRICULTURE = "agriculture"
    ENERGY = "energy"
    OTHER = "other"

class PricingType(str, Enum):
    FIXED = "fixed"  # Fixed price
    HOURLY = "hourly"  # Per hour
    DAILY = "daily"   # Per day
    PROJECT = "project"  # Per project
    MONTHLY = "monthly"  # Monthly subscription
    CUSTOM = "custom"   # Custom pricing

class ServiceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class ContactType(str, Enum):
    PRIMARY = "primary"
    SALES = "sales"
    SUPPORT = "support"
    TECHNICAL = "technical"
    BILLING = "billing"
    EMERGENCY = "emergency"

class BusinessHour(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str  # Monday, Tuesday, etc.
    is_open: bool = True
    open_time: Optional[str] = None  # "09:00"
    close_time: Optional[str] = None  # "17:00"
    break_start: Optional[str] = None  # "12:00"
    break_end: Optional[str] = None  # "13:00"
    is_24_hours: bool = False
    notes: Optional[str] = None  # "Closed for lunch 12-1 PM"

class BusinessContact(BaseModel):
    contact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contact_type: ContactType
    contact_person: str
    job_title: Optional[str] = None
    phone: str
    email: EmailStr
    whatsapp: Optional[str] = None
    telegram: Optional[str] = None
    is_primary: bool = False
    is_public: bool = True  # Show on public profile
    is_verified: bool = False
    verification_method: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SocialMediaLink(BaseModel):
    platform: str  # linkedin, twitter, facebook, instagram, youtube
    username: Optional[str] = None
    url: str
    is_verified: bool = False
    follower_count: Optional[int] = None

class BusinessImage(BaseModel):
    image_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    image_type: str  # logo, storefront, team, product, certificate, award, other
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    display_order: int = 0
    is_featured: bool = False
    is_public: bool = True
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceOffering(BaseModel):
    service_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    service_name: str
    service_description: str
    category: ServiceCategory
    subcategory: Optional[str] = None
    
    # Pricing Information
    pricing_type: PricingType
    base_price: Optional[float] = None
    currency: str = "NGN"
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    pricing_notes: Optional[str] = None
    
    # Service Details
    duration_estimate: Optional[str] = None  # "2-3 weeks", "1 day", etc.
    deliverables: List[str] = []
    requirements: List[str] = []
    features: List[str] = []
    
    # Media
    images: List[BusinessImage] = []
    video_url: Optional[str] = None
    
    # Availability
    is_available: bool = True
    availability_notes: Optional[str] = None
    lead_time: Optional[str] = None  # "Available immediately", "2 week notice"
    
    # SEO & Discovery
    keywords: List[str] = []
    tags: List[str] = []
    
    # Status & Metadata
    status: ServiceStatus = ServiceStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    views_count: int = 0
    inquiries_count: int = 0

class ProfileUpdateRequest(BaseModel):
    # Basic Business Information
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    tagline: Optional[str] = None  # Short business tagline
    website: Optional[str] = None
    
    # Contact Information
    business_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Business Details
    established_year: Optional[int] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[str] = None  # "< $100K", "$100K - $1M", etc.
    business_registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    
    # Operating Information
    business_hours: Optional[List[BusinessHour]] = None
    business_contacts: Optional[List[BusinessContact]] = None
    social_media: Optional[List[SocialMediaLink]] = None
    
    # Visual Content
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    business_images: Optional[List[BusinessImage]] = None
    
    # Services
    services: Optional[List[ServiceOffering]] = None
    
    @validator('website')
    def validate_website(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v

class ProfileUpdateResponse(BaseModel):
    success: bool
    updated_fields: List[str] = []
    validation_errors: List[str] = []
    new_completion_score: float
    new_trust_score: float
    badges_earned: List[str] = []
    message: str

class ServiceInquiry(BaseModel):
    inquiry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    service_id: str
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    inquiry_message: str
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    project_details: Dict[str, Any] = {}
    status: str = "new"  # new, responded, in_progress, closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BusinessAnalytics(BaseModel):
    vendor_id: str
    analytics_period: str  # daily, weekly, monthly
    
    # Profile Metrics
    profile_views: int = 0
    profile_unique_visitors: int = 0
    search_appearances: int = 0
    search_clicks: int = 0
    
    # Service Metrics
    service_views: int = 0
    service_inquiries: int = 0
    inquiry_response_rate: float = 0.0
    
    # Trust Metrics
    trust_score_change: float = 0.0
    new_reviews: int = 0
    average_rating: float = 0.0
    
    # Conversion Metrics
    inquiry_to_conversion_rate: float = 0.0
    repeat_customer_rate: float = 0.0
    
    # Geographic Data
    top_locations: List[Dict[str, Any]] = []
    
    # Traffic Sources
    traffic_sources: Dict[str, int] = {}  # organic, direct, referral, social
    
    # Generated timestamp
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactFormSubmission(BaseModel):
    submission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: Optional[str] = None
    message: str
    source: str = "website"  # website, mobile, api
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_spam: bool = False
    spam_score: float = 0.0
    status: str = "new"  # new, read, responded, archived
    tags: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProfileVisit(BaseModel):
    visit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    visitor_ip: Optional[str] = None
    visitor_country: Optional[str] = None
    visitor_city: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    pages_viewed: List[str] = []
    time_on_site: int = 0  # seconds
    is_return_visitor: bool = False
    converted: bool = False  # Did they submit inquiry
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Response models for API
class ServiceOfferingResponse(BaseModel):
    services: List[ServiceOffering]
    total_count: int
    active_count: int
    categories: List[str]

class AnalyticsSummary(BaseModel):
    total_views: int
    total_inquiries: int
    conversion_rate: float
    top_services: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class ProfileCompletionAnalysis(BaseModel):
    completion_percentage: float
    missing_sections: List[str]
    recommendations: List[str]
    priority_actions: List[str]