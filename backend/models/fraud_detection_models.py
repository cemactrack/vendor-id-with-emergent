from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class FraudType(str, Enum):
    DUPLICATE_REGISTRATION = "duplicate_registration"
    IDENTITY_THEFT = "identity_theft"
    DOCUMENT_FORGERY = "document_forgery"
    REVIEW_MANIPULATION = "review_manipulation"
    COLLUSION = "collusion"
    SYNTHETIC_IDENTITY = "synthetic_identity"
    ACCOUNT_TAKEOVER = "account_takeover"

class DetectionStatus(str, Enum):
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    UNDER_INVESTIGATION = "under_investigation"
    RESOLVED = "resolved"

class RiskScore(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    biometric_risk: float = Field(default=0.0, ge=0, le=100)
    document_risk: float = Field(default=0.0, ge=0, le=100)
    behavioral_risk: float = Field(default=0.0, ge=0, le=100)
    network_risk: float = Field(default=0.0, ge=0, le=100)
    device_risk: float = Field(default=0.0, ge=0, le=100)
    temporal_risk: float = Field(default=0.0, ge=0, le=100)

class DuplicateDetectionResult(BaseModel):
    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    primary_vendor_id: str
    duplicate_vendor_ids: List[str] = []
    fraud_type: FraudType
    confidence_score: float = Field(..., ge=0, le=1)
    evidence: Dict[str, Any] = {}
    risk_score: RiskScore
    detection_method: str  # biometric, document, behavioral, etc.
    auto_detected: bool = True
    human_verified: bool = False
    status: DetectionStatus = DetectionStatus.SUSPECTED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    investigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class BiometricSimilarity(BaseModel):
    similarity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id_1: str
    vendor_id_2: str
    similarity_score: float = Field(..., ge=0, le=1)
    biometric_type: str  # face, fingerprint, iris
    match_points: List[Dict[str, Any]] = []
    quality_score_1: float
    quality_score_2: float
    processing_algorithm: str
    threshold_used: float
    match_confirmed: bool
    reviewed_by_human: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentSimilarity(BaseModel):
    similarity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id_1: str
    vendor_id_2: str
    document_type_1: str
    document_type_2: str
    similarity_indicators: Dict[str, Any] = {}  # OCR text, metadata, image hash
    structural_similarity: float = Field(default=0.0, ge=0, le=1)
    content_similarity: float = Field(default=0.0, ge=0, le=1)
    metadata_similarity: float = Field(default=0.0, ge=0, le=1)
    overall_similarity: float = Field(default=0.0, ge=0, le=1)
    suspicious_elements: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BehavioralPattern(BaseModel):
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    pattern_type: str  # login_timing, device_usage, application_flow
    pattern_data: Dict[str, Any] = {}
    frequency_analysis: Dict[str, Any] = {}
    anomaly_score: float = Field(default=0.0, ge=0, le=1)
    baseline_established: bool = False
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NetworkAnalysis(BaseModel):
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_ids: List[str]  # Vendors in the same network
    connection_type: str  # ip_address, device_fingerprint, timing_correlation
    connection_strength: float = Field(..., ge=0, le=1)
    shared_attributes: List[str] = []
    suspicious_indicators: List[str] = []
    network_size: int
    risk_level: str  # low, medium, high, critical
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FraudInvestigation(BaseModel):
    investigation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_ids: List[str]  # All vendors involved
    fraud_type: FraudType
    priority: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, closed, escalated
    assigned_investigator: Optional[str] = None
    evidence_collected: List[Dict[str, Any]] = []
    investigation_notes: List[Dict[str, Any]] = []
    resolution: Optional[str] = None
    actions_taken: List[str] = []
    financial_impact: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None

class SyntheticIdentityIndicators(BaseModel):
    vendor_id: str
    indicators: Dict[str, Any] = {
        "recently_created_identity": False,
        "limited_digital_footprint": False,
        "inconsistent_personal_data": False,
        "new_phone_number": False,
        "new_email_domain": False,
        "rapid_account_setup": False,
        "minimal_document_history": False
    }
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    last_assessment: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReviewManipulationDetection(BaseModel):
    detection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    manipulation_type: str  # fake_reviews, review_farming, rating_inflation
    suspicious_patterns: List[Dict[str, Any]] = []
    affected_reviews: List[str] = []  # Review IDs
    confidence_score: float = Field(..., ge=0, le=1)
    temporal_clustering: bool = False  # Reviews clustered in time
    reviewer_network_detected: bool = False
    linguistic_similarity: float = Field(default=0.0, ge=0, le=1)
    velocity_anomaly: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeviceFingerprinting(BaseModel):
    fingerprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    device_attributes: Dict[str, str] = {}
    browser_fingerprint: Dict[str, Any] = {}
    canvas_fingerprint: str
    webgl_fingerprint: str
    audio_fingerprint: str
    font_fingerprint: List[str] = []
    plugin_fingerprint: List[str] = []
    timezone_fingerprint: str
    language_fingerprint: List[str] = []
    uniqueness_score: float = Field(default=0.0, ge=0, le=1)
    stability_score: float = Field(default=0.0, ge=0, le=1)  # How stable over time
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FraudAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_ids: List[str]
    fraud_type: FraudType
    severity: str = "medium"  # low, medium, high, critical
    alert_title: str
    description: str
    evidence_summary: Dict[str, Any] = {}
    risk_score: RiskScore
    auto_generated: bool = True
    requires_immediate_action: bool = False
    related_investigations: List[str] = []  # Investigation IDs
    status: str = "active"  # active, acknowledged, resolved, false_positive
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FraudPrevention(BaseModel):
    """Configuration for fraud prevention measures"""
    vendor_id: str
    prevention_measures: Dict[str, bool] = {
        "biometric_duplicate_check": True,
        "document_verification": True,
        "device_fingerprinting": True,
        "behavioral_analysis": True,
        "review_monitoring": True,
        "velocity_checks": True
    }
    thresholds: Dict[str, float] = {
        "biometric_similarity_threshold": 0.85,
        "document_similarity_threshold": 0.80,
        "risk_score_threshold": 75.0,
        "review_velocity_threshold": 5.0  # reviews per day
    }
    automated_actions: Dict[str, str] = {
        "high_risk_registration": "manual_review",
        "duplicate_detection": "block_registration",
        "review_manipulation": "hide_reviews"
    }
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FraudStatistics(BaseModel):
    """Platform-wide fraud statistics"""
    period: str  # daily, weekly, monthly
    total_registrations: int
    fraud_attempts_detected: int
    fraud_rate: float  # Percentage
    fraud_types_breakdown: Dict[str, int]
    top_risk_factors: List[Dict[str, Any]]
    prevention_effectiveness: Dict[str, float]
    false_positive_rate: float
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComplianceAudit(BaseModel):
    """Audit trail for fraud detection compliance"""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    audit_type: str  # periodic, triggered, compliance_check
    checks_performed: List[str] = []
    findings: List[Dict[str, Any]] = []
    compliance_score: float = Field(default=0.0, ge=0, le=100)
    recommendations: List[str] = []
    auditor_id: str
    audit_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_audit_due: datetime