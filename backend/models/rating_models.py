from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# Enums for Rating System
class RatingCategory(str, Enum):
    PRODUCT_SERVICE_QUALITY = "product_service_quality"
    CUSTOMER_SERVICE = "customer_service" 
    DELIVERY_TIMELINESS = "delivery_timeliness"
    PRICING_TRANSPARENCY = "pricing_transparency"
    TRUST_RELIABILITY = "trust_reliability"
    ESCROW_DISPUTE_HANDLING = "escrow_dispute_handling"
    COMPLIANCE_DOCUMENTATION = "compliance_documentation"

class VendorBadge(str, Enum):
    GOLD_VERIFIED = "gold_verified"      # 4.5+ consistently
    TRUSTED_VENDOR = "trusted_vendor"    # 4.0+
    UNDER_REVIEW = "under_review"        # <3.0 or multiple disputes
    NEW_VENDOR = "new_vendor"           # <10 ratings
    SUSPENDED = "suspended"             # Policy violations

class ReviewStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FLAGGED = "flagged"
    REMOVED = "removed"

# Rating Criteria Models
class RatingCriteria(BaseModel):
    product_service_quality: int = Field(..., ge=1, le=5)
    customer_service: int = Field(..., ge=1, le=5)
    delivery_timeliness: int = Field(..., ge=1, le=5)
    pricing_transparency: int = Field(..., ge=1, le=5)
    trust_reliability: int = Field(..., ge=1, le=5)
    escrow_dispute_handling: int = Field(..., ge=1, le=5)
    compliance_documentation: int = Field(..., ge=1, le=5)
    
    @validator('*')
    def validate_rating_range(cls, v):
        if not isinstance(v, int) or v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class RatingCreate(BaseModel):
    order_id: str
    vendor_id: str
    ratings: RatingCriteria
    review_title: Optional[str] = Field(None, max_length=100)
    review_comment: Optional[str] = Field(None, max_length=1000)
    would_recommend: bool = True
    photos: List[str] = []  # Photo URLs/paths
    
    @validator('review_comment')
    def validate_comment_length(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Review comment must be at least 10 characters')
        return v

class VendorRating(BaseModel):
    rating_id: str
    order_id: str
    customer_id: str
    vendor_id: str
    ratings: RatingCriteria
    overall_rating: float  # Calculated weighted average
    review_title: Optional[str] = None
    review_comment: Optional[str] = None
    would_recommend: bool = True
    photos: List[str] = []
    status: ReviewStatus = ReviewStatus.PENDING
    helpful_votes: int = 0
    unhelpful_votes: int = 0
    created_at: datetime
    updated_at: datetime
    verified_purchase: bool = True  # Always true for escrow orders
    admin_notes: Optional[str] = None

# Vendor Score Models
class CategoryScore(BaseModel):
    category: RatingCategory
    average_rating: float
    total_ratings: int
    weight: float  # Weight in overall calculation

class VendorScoreDetails(BaseModel):
    vendor_id: str
    overall_score: float
    category_scores: List[CategoryScore]
    total_ratings: int
    total_reviews: int
    recommendation_percentage: float
    badge: VendorBadge
    badge_earned_at: Optional[datetime] = None
    last_updated: datetime
    
    # Historical tracking
    score_30_days: Optional[float] = None
    score_90_days: Optional[float] = None
    score_1_year: Optional[float] = None
    
    # Detailed metrics
    five_star_percentage: float = 0.0
    four_star_percentage: float = 0.0
    three_star_percentage: float = 0.0
    two_star_percentage: float = 0.0
    one_star_percentage: float = 0.0

class VendorBadgeHistory(BaseModel):
    badge_history_id: str
    vendor_id: str
    badge: VendorBadge
    earned_at: datetime
    lost_at: Optional[datetime] = None
    reason: str
    score_at_time: float
    total_ratings_at_time: int

# Rating Analytics Models
class RatingAnalytics(BaseModel):
    period: str  # "7d", "30d", "90d", "1y", "all"
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int]  # {5: 50, 4: 30, 3: 15, 2: 3, 1: 2}
    category_averages: Dict[str, float]
    trending_direction: str  # "up", "down", "stable"
    improvement_areas: List[str]  # Categories with lowest scores

class ReviewResponse(BaseModel):
    response_id: str
    rating_id: str
    vendor_id: str
    response_text: str
    created_at: datetime
    updated_at: datetime
    admin_approved: bool = False

# Review Moderation Models
class ReviewFlag(BaseModel):
    flag_id: str
    rating_id: str
    flagged_by: str  # user_id
    reason: str
    description: Optional[str] = None
    created_at: datetime
    reviewed_by: Optional[str] = None  # admin user_id
    reviewed_at: Optional[datetime] = None
    status: str = "pending"  # pending, valid, invalid
    action_taken: Optional[str] = None

# Vendor Rating Dashboard Models
class VendorRatingDashboard(BaseModel):
    vendor_id: str
    current_score: VendorScoreDetails
    recent_ratings: List[VendorRating]
    analytics: RatingAnalytics
    badge_progress: Dict[str, Any]  # Progress towards next badge
    improvement_suggestions: List[str]
    competitor_comparison: Optional[Dict[str, float]] = None

# Rating Summary for Listings
class VendorRatingSummary(BaseModel):
    vendor_id: str
    overall_score: float
    total_ratings: int
    badge: VendorBadge
    recent_score_trend: str  # "improving", "declining", "stable"
    top_categories: List[str]  # Best performing categories
    
class RatingWeights(BaseModel):
    """Configurable weights for rating categories"""
    product_service_quality: float = 0.25      # 25%
    customer_service: float = 0.20              # 20% 
    delivery_timeliness: float = 0.20           # 20%
    pricing_transparency: float = 0.10          # 10%
    trust_reliability: float = 0.15             # 15%
    escrow_dispute_handling: float = 0.05       # 5%
    compliance_documentation: float = 0.05      # 5%
    
    @validator('*')
    def validate_weight_range(cls, v):
        if not isinstance(v, (int, float)) or v < 0 or v > 1:
            raise ValueError('Weight must be between 0 and 1')
        return float(v)
    
    def validate_total_weight(self):
        """Ensure weights sum to 1.0"""
        total = (
            self.product_service_quality +
            self.customer_service +
            self.delivery_timeliness +
            self.pricing_transparency +
            self.trust_reliability +
            self.escrow_dispute_handling +
            self.compliance_documentation
        )
        if abs(total - 1.0) > 0.01:  # Allow small floating point differences
            raise ValueError(f'Total weights must sum to 1.0, got {total}')
        return True

# Badge Requirements Configuration
class BadgeRequirements(BaseModel):
    gold_verified: Dict[str, Any] = {
        "min_score": 4.5,
        "min_ratings": 50,
        "consistency_period_days": 90,
        "max_disputes_ratio": 0.02,  # Max 2% dispute rate
        "compliance_required": True
    }
    trusted_vendor: Dict[str, Any] = {
        "min_score": 4.0,
        "min_ratings": 20,
        "consistency_period_days": 30,
        "max_disputes_ratio": 0.05,  # Max 5% dispute rate
        "compliance_required": True
    }
    under_review: Dict[str, Any] = {
        "max_score": 3.0,
        "min_disputes": 3,
        "compliance_violations": 2
    }

# Customer Rating Models  
class CustomerRatingHistory(BaseModel):
    customer_id: str
    total_ratings_given: int
    average_rating_given: float
    reliability_score: float  # How consistent are their ratings
    verified_purchases_only: bool = True
    
class RatingIncentive(BaseModel):
    """Incentives for customers to leave ratings"""
    incentive_id: str
    customer_id: str
    order_id: str
    incentive_type: str  # "discount", "points", "badge"
    value: float
    description: str
    claimed: bool = False
    expires_at: datetime
    created_at: datetime

# Platform Rating Statistics
class PlatformRatingStats(BaseModel):
    total_ratings: int
    average_platform_score: float
    vendor_distribution: Dict[str, int]  # {gold: 45, trusted: 120, under_review: 5}
    category_performance: Dict[str, float]
    monthly_trends: List[Dict[str, Any]]
    top_performing_vendors: List[str]
    improvement_needed_vendors: List[str]

# API Response Models
class RatingSubmissionResponse(BaseModel):
    rating: VendorRating
    vendor_score_updated: VendorScoreDetails
    message: str

class VendorProfileWithRatings(BaseModel):
    vendor_profile: Dict[str, Any]  # From existing vendor model
    rating_summary: VendorRatingSummary
    recent_reviews: List[VendorRating]
    score_details: VendorScoreDetails