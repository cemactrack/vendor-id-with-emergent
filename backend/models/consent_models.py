from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class ConsentType(str, Enum):
    BIOMETRIC_PROCESSING = "biometric_processing"
    BIOMETRIC_STORAGE = "biometric_storage"
    BIOMETRIC_MATCHING = "biometric_matching"
    DATA_PROCESSING = "data_processing"
    MARKETING_COMMUNICATIONS = "marketing_communications"
    THIRD_PARTY_SHARING = "third_party_sharing"
    CROSS_BORDER_TRANSFER = "cross_border_transfer"

class ConsentStatus(str, Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

class DataRetentionPolicy(str, Enum):
    SEVEN_YEARS = "7_years"  # Legal compliance requirement
    UNTIL_WITHDRAWAL = "until_withdrawal"
    UNTIL_ACCOUNT_DELETION = "until_account_deletion"
    CUSTOM_PERIOD = "custom_period"

class ConsentRecord(BaseModel):
    consent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    consent_type: ConsentType
    status: ConsentStatus = ConsentStatus.PENDING
    consent_text: str  # Full consent text shown to user
    consent_version: str  # Version of consent terms
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    ip_address: str
    user_agent: str
    retention_policy: DataRetentionPolicy = DataRetentionPolicy.SEVEN_YEARS
    retention_until: Optional[datetime] = None
    legal_basis: str = "consent"  # GDPR legal basis
    purpose_limitation: List[str] = []  # Specific purposes for data use
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsentWithdrawalRequest(BaseModel):
    withdrawal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    consent_ids: List[str]  # Specific consents to withdraw
    withdrawal_reason: Optional[str] = None
    data_deletion_requested: bool = True
    deletion_deadline: datetime  # GDPR: 30 days max
    ip_address: str
    user_agent: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DataDeletionRequest(BaseModel):
    deletion_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    request_type: str = "right_to_erasure"  # right_to_erasure, account_closure
    data_categories: List[str] = []  # biometric_templates, documents, profile_data
    reason: str
    verification_method: str  # how identity was verified for deletion
    status: str = "pending"  # pending, approved, processing, completed, denied
    approved_by: Optional[str] = None  # admin user ID
    processed_by: Optional[str] = None
    completion_evidence: Optional[str] = None  # proof of deletion
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    deadline: datetime  # GDPR: 30 days

class BiometricDataAudit(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    data_type: str  # template, raw_biometric, processed_image
    operation: str  # created, accessed, modified, deleted, transferred
    operator_id: str  # who performed the operation
    operator_role: str  # admin, system, vendor
    purpose: str  # verification, matching, audit, deletion
    legal_basis: str  # consent, legitimate_interest, legal_obligation
    data_location: str  # server, backup, archive
    encryption_status: str  # encrypted, decrypted, in_transit
    retention_applied: bool = True
    cross_border_transfer: bool = False
    transfer_country: Optional[str] = None
    consent_reference: Optional[str] = None  # consent_id if applicable
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComplianceReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    report_type: str = "gdpr_compliance"  # gdpr_compliance, data_inventory, consent_status
    compliance_score: float  # 0-100
    issues_found: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    data_inventory: Dict[str, Any] = {}
    consent_summary: Dict[str, int] = {}
    retention_compliance: Dict[str, bool] = {}
    generated_by: str  # system or admin user
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime

# GDPR-specific models
class DataPortabilityRequest(BaseModel):
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    requested_data: List[str] = []  # profile, documents, ratings, biometric_metadata
    format_requested: str = "json"  # json, csv, xml
    include_raw_data: bool = False  # exclude raw biometric data for security
    status: str = "pending"
    export_file_path: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class ConsentRenewalReminder(BaseModel):
    reminder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    consent_id: str
    reminder_type: str = "expiry_approaching"  # expiry_approaching, policy_updated, annual_review
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    response_deadline: datetime
    vendor_response: Optional[str] = None  # renewed, withdrawn, no_response
    responded_at: Optional[datetime] = None