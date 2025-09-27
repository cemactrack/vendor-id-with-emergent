from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class DeviceStatus(str, Enum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted" 
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"

class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_ANOMALY = "login_anomaly"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DEVICE_REGISTERED = "device_registered"
    DEVICE_BLOCKED = "device_blocked"
    PASSWORD_CHANGED = "password_changed"
    TWO_FA_ENABLED = "two_fa_enabled"
    TWO_FA_DISABLED = "two_fa_disabled"
    API_RATE_LIMIT_EXCEEDED = "api_rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DeviceFingerprint(BaseModel):
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    device_hash: str  # Unique device identifier
    device_name: Optional[str] = None  # User-assigned name
    user_agent: str
    screen_resolution: str
    timezone: str
    language: str
    platform: str  # Windows, MacOS, iOS, Android, etc.
    browser: str
    ip_address: str
    location_data: Dict[str, Any] = {}  # Country, city, ISP
    hardware_info: Dict[str, Any] = {}  # CPU, memory, graphics
    status: DeviceStatus = DeviceStatus.UNTRUSTED
    trust_score: float = 0.0  # 0-100
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    login_count: int = 0
    failed_attempts: int = 0
    is_mobile: bool = False
    is_verified: bool = False  # Email/SMS verification completed
    verification_method: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionSecurity(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    device_id: str
    jwt_token_id: str  # Reference to JWT token
    ip_address: str
    location_data: Dict[str, Any] = {}
    session_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_active: bool = True
    activities: List[Dict[str, Any]] = []  # Track user activities
    risk_indicators: List[str] = []  # Suspicious patterns
    concurrent_sessions: int = 1
    max_concurrent_allowed: int = 3
    
class SecurityEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    event_type: SecurityEventType
    risk_level: RiskLevel
    description: str
    metadata: Dict[str, Any] = {}
    ip_address: str
    user_agent: str
    device_id: Optional[str] = None
    session_id: Optional[str] = None
    automated_response: Optional[str] = None  # Action taken by system
    admin_reviewed: bool = False
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class APIRateLimit(BaseModel):
    limit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    endpoint: str  # API endpoint pattern
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    current_minute_count: int = 0
    current_hour_count: int = 0
    current_day_count: int = 0
    last_reset_minute: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_reset_hour: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_reset_day: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    blocked_until: Optional[datetime] = None
    violation_count: int = 0

class LoginAttempt(BaseModel):
    attempt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: Optional[str] = None  # May be unknown for failed attempts
    email: str
    ip_address: str
    user_agent: str
    device_fingerprint: str
    success: bool
    failure_reason: Optional[str] = None
    two_fa_used: bool = False
    location_data: Dict[str, Any] = {}
    risk_indicators: List[str] = []
    blocked_by_security: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SecurityAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str
    alert_type: str  # suspicious_login, unusual_activity, security_breach
    severity: RiskLevel
    title: str
    description: str
    evidence: List[Dict[str, Any]] = []  # Supporting evidence
    automated_actions: List[str] = []  # Actions taken by system
    status: str = "active"  # active, investigating, resolved, false_positive
    assigned_to: Optional[str] = None  # Security team member
    vendor_notified: bool = False
    admin_response: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TrustedDevice(BaseModel):
    """Devices that have been explicitly trusted by the vendor"""
    device_id: str
    vendor_id: str
    device_name: str  # User-assigned name
    device_type: str  # mobile, desktop, tablet
    verification_code: str  # Code sent for verification
    verified_at: datetime
    last_used: datetime
    trust_level: str = "high"  # high, medium, temporary
    expires_at: Optional[datetime] = None  # For temporary trust
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccessControl(BaseModel):
    """Role-based access control for team members"""
    access_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vendor_id: str  # Main vendor account
    user_id: str    # Team member
    role: str       # owner, admin, manager, editor, viewer
    permissions: List[str] = []  # Specific permissions
    ip_restrictions: List[str] = []  # Allowed IP ranges
    time_restrictions: Dict[str, Any] = {}  # Working hours, days
    is_active: bool = True
    granted_by: str  # Who granted access
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None

class SecurityConfiguration(BaseModel):
    """Security settings for a vendor account"""
    vendor_id: str
    password_policy: Dict[str, Any] = {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_symbols": True,
        "max_age_days": 90
    }
    two_fa_required: bool = True
    trusted_devices_enabled: bool = True
    max_concurrent_sessions: int = 3
    session_timeout_minutes: int = 480  # 8 hours
    api_rate_limits: Dict[str, int] = {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    }
    ip_whitelist: List[str] = []
    notification_preferences: Dict[str, bool] = {
        "login_alerts": True,
        "suspicious_activity": True,
        "device_registration": True,
        "security_updates": True
    }
    auto_lock_enabled: bool = True
    auto_lock_after_attempts: int = 5
    lockout_duration_minutes: int = 30
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Response models
class SecurityDashboard(BaseModel):
    vendor_id: str
    security_score: float  # Overall security score 0-100
    active_sessions: int
    trusted_devices: int
    recent_alerts: List[SecurityAlert]
    risk_summary: Dict[str, int]  # Count by risk level
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    last_security_audit: Optional[datetime] = None