from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class EmailVerificationCreate(BaseModel):
    email: EmailStr

class EmailVerificationVerify(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class TwoFactorSetup(BaseModel):
    password: str  # Current password required for setup

class TwoFactorVerify(BaseModel):
    token: str  # 6-digit TOTP token

class TwoFactorDisable(BaseModel):
    password: str
    token: Optional[str] = None  # TOTP token or backup code

class BackupCodeVerify(BaseModel):
    code: str  # Backup code in XXXX-XXXX format

class SecurityEvent(BaseModel):
    id: str
    user_id: str
    event_type: str  # login_success, login_failed, 2fa_enabled, 2fa_disabled, password_changed, etc.
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSecurity(BaseModel):
    user_id: str
    email_verified: bool = False
    email_verification_token: Optional[str] = None
    email_verification_expires: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    backup_codes: List[str] = []
    failed_login_attempts: int = 0
    account_locked_until: Optional[datetime] = None
    last_login_attempt: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LoginWithTwoFactor(BaseModel):
    email: EmailStr
    password: str
    totp_token: Optional[str] = None
    backup_code: Optional[str] = None

class TwoFactorSetupResponse(BaseModel):
    qr_code: str
    setup_key: str
    backup_codes: List[str]
    issuer: str

class SecurityAuditLog(BaseModel):
    user_id: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    details: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)