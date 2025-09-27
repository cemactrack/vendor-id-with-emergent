from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

# Enums for Biometric System
class BiometricType(str, Enum):
    FACE = "face"
    FINGERPRINT = "fingerprint"
    IRIS = "iris"
    VOICE = "voice"

class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    PROVISIONALLY_VERIFIED = "provisionally_verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class BiometricQuality(str, Enum):
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-89%
    ACCEPTABLE = "acceptable"  # 50-69%
    POOR = "poor"           # 30-49%
    UNACCEPTABLE = "unacceptable"  # 0-29%

class DocumentType(str, Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVERS_LICENSE = "drivers_license"
    VOTER_ID = "voter_id"
    RESIDENCE_PERMIT = "residence_permit"

class LivenessCheckType(str, Enum):
    BLINK = "blink"
    HEAD_TURN_LEFT = "head_turn_left"
    HEAD_TURN_RIGHT = "head_turn_right" 
    SMILE = "smile"
    NOD = "nod"
    RANDOM_CHALLENGE = "random_challenge"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Document Analysis Models
class DocumentAnalysisResult(BaseModel):
    document_type: DocumentType
    extracted_text: Dict[str, str]  # {"name": "John Doe", "id_number": "123456789", etc}
    face_image_extracted: bool
    face_image_path: Optional[str] = None
    face_confidence: float = 0.0
    document_valid: bool = False
    security_features_detected: List[str] = []  # watermarks, holograms, etc
    tampering_detected: bool = False
    quality_score: float = 0.0
    processing_metadata: Dict[str, Any] = {}

class DocumentUploadRequest(BaseModel):
    document_type: DocumentType
    image_data: str  # Base64 encoded image
    file_name: str
    vendor_id: str
    
    @validator('image_data')
    def validate_image_data(cls, v):
        if not v or len(v) < 100:
            raise ValueError('Invalid image data')
        return v

# Biometric Template Models
class BiometricTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    biometric_type: BiometricType
    encrypted_template: str  # Encrypted biometric template
    template_version: str = "1.0"
    quality_score: float
    confidence_level: float
    extraction_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True

# Liveness Detection Models
class LivenessChallenge(BaseModel):
    challenge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    challenge_type: LivenessCheckType
    challenge_sequence: List[LivenessCheckType]
    instructions: str
    timeout_seconds: int = 30
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed: bool = False
    success: bool = False

class LivenessResponse(BaseModel):
    challenge_id: str
    response_data: str  # Base64 encoded video/images
    response_metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LivenessResult(BaseModel):
    challenge_id: str
    vendor_id: str
    success: bool
    confidence_score: float
    liveness_indicators: Dict[str, bool] = {}  # {"blink_detected": True, "head_movement": True}
    face_detected: bool = False
    face_quality: BiometricQuality = BiometricQuality.UNACCEPTABLE
    spoof_detection_passed: bool = False
    processing_time_ms: int = 0
    failure_reasons: List[str] = []

# Face Matching Models
class FaceMatchRequest(BaseModel):
    vendor_id: str
    reference_image: str  # Base64 from document
    comparison_image: str  # Base64 from live scan
    match_threshold: float = 0.75

class FaceMatchResult(BaseModel):
    match_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    similarity_score: float
    match_confirmed: bool
    confidence_level: float
    reference_face_quality: BiometricQuality
    comparison_face_quality: BiometricQuality
    processing_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Fingerprint Models
class FingerprintCaptureRequest(BaseModel):
    vendor_id: str
    fingerprint_data: str  # Base64 encoded fingerprint image
    finger_position: str  # "thumb_right", "index_left", etc
    capture_method: str = "mobile_sensor"  # mobile_sensor, external_device, webcam

class FingerprintTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    finger_position: str
    minutiae_template: str  # Encrypted minutiae points
    quality_score: float
    ridge_count: int
    template_size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Iris Scanning Models (if supported)
class IrisCaptureRequest(BaseModel):
    vendor_id: str
    iris_image_data: str  # Base64 encoded iris image
    eye_position: str = "both"  # "left", "right", "both"
    capture_device: str = "mobile_camera"

class IrisTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    eye_position: str
    iris_code: str  # Encrypted iris code
    quality_metrics: Dict[str, float] = {}
    template_confidence: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Cross-Matching & Duplicate Detection
class DuplicateCheckRequest(BaseModel):
    vendor_id: str
    biometric_templates: List[str]  # List of template IDs to check
    match_threshold: float = 0.85

class DuplicateCheckResult(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    duplicate_found: bool
    matching_vendor_ids: List[str] = []
    similarity_scores: Dict[str, float] = {}  # {"vendor_id": similarity_score}
    confidence_level: float
    biometric_conflicts: List[Dict[str, Any]] = []

# Risk Assessment Models
class DeviceFingerprint(BaseModel):
    fingerprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    device_id: str
    user_agent: str
    screen_resolution: str
    timezone: str
    language_settings: List[str]
    installed_fonts: List[str] = []
    canvas_fingerprint: str
    webgl_fingerprint: str
    audio_fingerprint: str
    battery_info: Dict[str, Any] = {}
    network_info: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GeoLocationData(BaseModel):
    vendor_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    ip_address: str
    country: str
    region: str
    city: str
    isp: str
    vpn_detected: bool = False
    proxy_detected: bool = False
    tor_detected: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskAssessment(BaseModel):
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    overall_risk_level: RiskLevel
    risk_score: float  # 0-100
    risk_factors: List[Dict[str, Any]] = []
    device_risk: float = 0.0
    location_risk: float = 0.0
    behavior_risk: float = 0.0
    duplicate_risk: float = 0.0
    document_risk: float = 0.0
    biometric_risk: float = 0.0
    recommendations: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Biometric Verification Session
class BiometricVerificationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    session_type: str = "initial_verification"  # initial_verification, re_verification, spot_check
    status: VerificationStatus = VerificationStatus.PENDING
    
    # Document Analysis
    document_uploaded: bool = False
    document_analysis: Optional[DocumentAnalysisResult] = None
    
    # Liveness Check
    liveness_completed: bool = False
    liveness_result: Optional[LivenessResult] = None
    
    # Face Matching
    face_match_completed: bool = False
    face_match_result: Optional[FaceMatchResult] = None
    
    # Fingerprint
    fingerprint_captured: bool = False
    fingerprint_templates: List[FingerprintTemplate] = []
    
    # Iris (optional)
    iris_captured: bool = False
    iris_templates: List[IrisTemplate] = []
    
    # Cross-matching
    duplicate_check_completed: bool = False
    duplicate_check_result: Optional[DuplicateCheckResult] = None
    
    # Risk Assessment
    risk_assessment: Optional[RiskAssessment] = None
    
    # Session Metadata
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    device_fingerprint: Optional[DeviceFingerprint] = None
    geo_location: Optional[GeoLocationData] = None
    
    # Verification Results
    verification_score: float = 0.0
    verification_confidence: float = 0.0
    completion_percentage: float = 0.0
    failure_reasons: List[str] = []
    admin_notes: Optional[str] = None
    
    # Re-verification
    next_verification_due: Optional[datetime] = None
    verification_history: List[str] = []  # Previous session IDs

# Biometric Audit Trail
class BiometricAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    session_id: Optional[str] = None
    event_type: str  # "template_created", "match_performed", "data_accessed", etc
    event_description: str
    biometric_types_involved: List[BiometricType] = []
    user_id: Optional[str] = None  # Admin user who performed action
    ip_address: str
    user_agent: str
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Manual Review Models
class ManualReviewRequest(BaseModel):
    review_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    vendor_id: str
    review_reason: str
    failed_components: List[str] = []
    priority: str = "normal"  # low, normal, high, urgent
    assigned_reviewer: Optional[str] = None
    status: str = "pending"  # pending, in_review, completed, escalated
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class ManualReviewDecision(BaseModel):
    review_id: str
    reviewer_id: str
    decision: str  # approve, reject, request_additional_info
    decision_notes: str
    additional_checks_required: List[str] = []
    verification_override: bool = False
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Configuration Models
class BiometricConfig(BaseModel):
    """System configuration for biometric verification"""
    
    # Quality Thresholds
    min_face_quality: float = 0.7
    min_fingerprint_quality: float = 0.6
    min_iris_quality: float = 0.8
    
    # Matching Thresholds
    face_match_threshold: float = 0.75
    fingerprint_match_threshold: float = 0.80
    iris_match_threshold: float = 0.85
    duplicate_detection_threshold: float = 0.90
    
    # Session Configuration
    session_timeout_minutes: int = 30
    max_retry_attempts: int = 3
    liveness_challenge_count: int = 3
    
    # Re-verification
    verification_validity_days: int = 365
    high_risk_reverification_days: int = 180
    
    # Security
    template_encryption_enabled: bool = True
    audit_all_operations: bool = True
    data_retention_days: int = 2555  # 7 years for compliance
    
    # Device Support  
    mobile_camera_enabled: bool = True
    desktop_camera_enabled: bool = True
    external_device_support: bool = True
    
    # Risk Scoring
    max_risk_score_for_approval: float = 30.0
    auto_reject_risk_score: float = 80.0

# Response Models for API
class BiometricVerificationResponse(BaseModel):
    session: BiometricVerificationSession
    next_step: str
    next_step_instructions: str
    completion_percentage: float
    estimated_time_remaining_minutes: int
    
class VerificationStatusResponse(BaseModel):
    vendor_id: str
    current_status: VerificationStatus
    verification_score: float
    next_verification_due: Optional[datetime]
    compliance_status: str
    active_templates: Dict[BiometricType, int]  # Count of templates per type