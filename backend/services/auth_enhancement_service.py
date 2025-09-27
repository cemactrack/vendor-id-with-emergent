from typing import Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.auth_models import *
from services.email_service import EmailService
from services.two_factor_service import TwoFactorService
from datetime import datetime, timedelta
import uuid
import bcrypt
import secrets
import string
import logging

logger = logging.getLogger(__name__)

class AuthEnhancementService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.user_security_collection = db.user_security
        self.security_events_collection = db.security_events
        self.email_service = EmailService()
        self.two_factor_service = TwoFactorService()
        
    # Email Verification
    async def send_email_verification(self, user_id: str, email: str, full_name: str) -> bool:
        """Send email verification to user"""
        try:
            # Generate verification token
            token = self.email_service.generate_verification_token()
            expires = datetime.utcnow() + timedelta(hours=24)
            
            # Store in database
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "email_verification_token": token,
                        "email_verification_expires": expires,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Send email
            success = await self.email_service.send_verification_email(email, full_name, token)
            
            if success:
                await self._log_security_event(user_id, "email_verification_sent", {"email": email})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email verification for user {user_id}: {e}")
            return False
    
    async def verify_email(self, token: str) -> Tuple[bool, Optional[str]]:
        """Verify email using token"""
        try:
            # Find user by token
            security_doc = await self.user_security_collection.find_one({
                "email_verification_token": token,
                "email_verification_expires": {"$gt": datetime.utcnow()}
            })
            
            if not security_doc:
                return False, "Invalid or expired verification token"
            
            user_id = security_doc["user_id"]
            
            # Update email verification status
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "email_verified": True,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "email_verification_token": "",
                        "email_verification_expires": ""
                    }
                }
            )
            
            # Update user document
            await self.users_collection.update_one(
                {"id": user_id},
                {"$set": {"email_verified": True, "updated_at": datetime.utcnow()}}
            )
            
            await self._log_security_event(user_id, "email_verified")
            
            return True, "Email verified successfully"
            
        except Exception as e:
            logger.error(f"Failed to verify email with token {token}: {e}")
            return False, "Verification failed"
    
    # Password Reset
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        try:
            # Find user by email
            user = await self.users_collection.find_one({"email": email})
            if not user:
                # Don't reveal if email exists or not
                return True
            
            user_id = user["id"]
            full_name = user["full_name"]
            
            # Generate reset token
            token = self.email_service.generate_reset_token()
            expires = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            
            # Store in database
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "password_reset_token": token,
                        "password_reset_expires": expires,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Send email
            success = await self.email_service.send_password_reset_email(email, full_name, token)
            
            if success:
                await self._log_security_event(user_id, "password_reset_requested", {"email": email})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to request password reset for {email}: {e}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Reset password using token"""
        try:
            # Find user by token
            security_doc = await self.user_security_collection.find_one({
                "password_reset_token": token,
                "password_reset_expires": {"$gt": datetime.utcnow()}
            })
            
            if not security_doc:
                return False, "Invalid or expired reset token"
            
            user_id = security_doc["user_id"]
            
            # Hash new password
            password_bytes = new_password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # Update password
            await self.users_collection.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "password_hash": hashed_password,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Clear reset token and reset failed login attempts
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "failed_login_attempts": 0,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "password_reset_token": "",
                        "password_reset_expires": "",
                        "account_locked_until": ""
                    }
                }
            )
            
            await self._log_security_event(user_id, "password_reset_completed")
            
            return True, "Password reset successfully"
            
        except Exception as e:
            logger.error(f"Failed to reset password with token {token}: {e}")
            return False, "Password reset failed"
    
    # Two-Factor Authentication
    async def setup_two_factor(self, user_id: str, password: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """Setup 2FA for user"""
        try:
            # Verify current password
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                return False, None, "User not found"
            
            password_bytes = password.encode('utf-8')
            stored_hash = user.get("password_hash").encode('utf-8')
            if not bcrypt.checkpw(password_bytes, stored_hash):
                return False, None, "Invalid password"
            
            # Generate 2FA secret and setup info
            secret = self.two_factor_service.generate_secret()
            setup_info = self.two_factor_service.generate_recovery_info(user["email"], secret)
            
            # Store in database
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "two_factor_secret": secret,
                        "backup_codes": setup_info["hashed_backup_codes"],
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            await self._log_security_event(user_id, "2fa_setup_initiated")
            
            return True, {
                "qr_code": setup_info["qr_code"],
                "setup_key": setup_info["setup_key"],
                "backup_codes": setup_info["backup_codes"],
                "issuer": setup_info["issuer"]
            }, None
            
        except Exception as e:
            logger.error(f"Failed to setup 2FA for user {user_id}: {e}")
            return False, None, "2FA setup failed"
    
    async def enable_two_factor(self, user_id: str, totp_token: str) -> Tuple[bool, Optional[str]]:
        """Enable 2FA after verifying TOTP token"""
        try:
            # Get user's 2FA secret
            security_doc = await self.user_security_collection.find_one({"user_id": user_id})
            if not security_doc or not security_doc.get("two_factor_secret"):
                return False, "2FA not set up"
            
            secret = security_doc["two_factor_secret"]
            
            # Verify TOTP token
            if not self.two_factor_service.verify_totp(secret, totp_token):
                return False, "Invalid verification code"
            
            # Enable 2FA
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "two_factor_enabled": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Send confirmation email
            user = await self.users_collection.find_one({"id": user_id})
            if user:
                await self.email_service.send_2fa_setup_email(user["email"], user["full_name"])
            
            await self._log_security_event(user_id, "2fa_enabled")
            
            return True, "Two-factor authentication enabled successfully"
            
        except Exception as e:
            logger.error(f"Failed to enable 2FA for user {user_id}: {e}")
            return False, "Failed to enable 2FA"
    
    async def verify_two_factor(self, user_id: str, token: str = None, backup_code: str = None) -> Tuple[bool, Optional[str]]:
        """Verify 2FA token or backup code"""
        try:
            security_doc = await self.user_security_collection.find_one({"user_id": user_id})
            if not security_doc or not security_doc.get("two_factor_enabled"):
                return False, "2FA not enabled"
            
            if token:
                # Verify TOTP token
                secret = security_doc["two_factor_secret"]
                if self.two_factor_service.verify_totp(secret, token):
                    await self._log_security_event(user_id, "2fa_verified_totp")
                    return True, None
            
            if backup_code:
                # Verify backup code
                backup_codes = security_doc.get("backup_codes", [])
                if self.two_factor_service.verify_backup_code(backup_code, backup_codes):
                    # Remove used backup code
                    code_hash = self.two_factor_service.hash_backup_code(backup_code)
                    updated_codes = [code for code in backup_codes if code != code_hash]
                    
                    await self.user_security_collection.update_one(
                        {"user_id": user_id},
                        {
                            "$set": {
                                "backup_codes": updated_codes,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    await self._log_security_event(user_id, "2fa_verified_backup_code")
                    return True, None
            
            return False, "Invalid verification code"
            
        except Exception as e:
            logger.error(f"Failed to verify 2FA for user {user_id}: {e}")
            return False, "2FA verification failed"
    
    async def disable_two_factor(self, user_id: str, password: str, token: str = None) -> Tuple[bool, Optional[str]]:
        """Disable 2FA"""
        try:
            # Verify password
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                return False, "User not found"
            
            password_bytes = password.encode('utf-8')
            stored_hash = user.get("password_hash").encode('utf-8')
            if not bcrypt.checkpw(password_bytes, stored_hash):
                return False, "Invalid password"
            
            # Verify 2FA token if 2FA is enabled
            security_doc = await self.user_security_collection.find_one({"user_id": user_id})
            if security_doc and security_doc.get("two_factor_enabled"):
                if token:
                    secret = security_doc["two_factor_secret"]
                    if not self.two_factor_service.verify_totp(secret, token):
                        return False, "Invalid 2FA code"
                else:
                    return False, "2FA code required"
            
            # Disable 2FA
            await self.user_security_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "two_factor_enabled": False,
                        "updated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "two_factor_secret": "",
                        "backup_codes": ""
                    }
                }
            )
            
            await self._log_security_event(user_id, "2fa_disabled")
            
            return True, "Two-factor authentication disabled"
            
        except Exception as e:
            logger.error(f"Failed to disable 2FA for user {user_id}: {e}")
            return False, "Failed to disable 2FA"
    
    # Security & Account Management
    async def record_login_attempt(self, email: str, success: bool, ip_address: str = None, user_agent: str = None) -> bool:
        """Record login attempt and handle account lockout"""
        try:
            user = await self.users_collection.find_one({"email": email})
            if not user:
                return success  # Don't reveal user existence
            
            user_id = user["id"]
            
            if success:
                # Reset failed attempts on successful login
                await self.user_security_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "failed_login_attempts": 0,
                            "last_login_attempt": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        },
                        "$unset": {"account_locked_until": ""}
                    },
                    upsert=True
                )
                
                await self._log_security_event(user_id, "login_success", {
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })
            else:
                # Increment failed attempts
                security_doc = await self.user_security_collection.find_one({"user_id": user_id})
                failed_attempts = security_doc.get("failed_login_attempts", 0) + 1 if security_doc else 1
                
                update_data = {
                    "failed_login_attempts": failed_attempts,
                    "last_login_attempt": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # Lock account after 5 failed attempts for 30 minutes
                if failed_attempts >= 5:
                    update_data["account_locked_until"] = datetime.utcnow() + timedelta(minutes=30)
                
                await self.user_security_collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data},
                    upsert=True
                )
                
                await self._log_security_event(user_id, "login_failed", {
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "failed_attempts": failed_attempts
                })
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to record login attempt for {email}: {e}")
            return success
    
    async def is_account_locked(self, email: str) -> Tuple[bool, Optional[datetime]]:
        """Check if account is locked"""
        try:
            user = await self.users_collection.find_one({"email": email})
            if not user:
                return False, None
            
            security_doc = await self.user_security_collection.find_one({"user_id": user["id"]})
            if not security_doc:
                return False, None
            
            locked_until = security_doc.get("account_locked_until")
            if locked_until and locked_until > datetime.utcnow():
                return True, locked_until
            
            return False, None
            
        except Exception as e:
            logger.error(f"Failed to check account lock status for {email}: {e}")
            return False, None
    
    async def get_user_security_info(self, user_id: str) -> Optional[dict]:
        """Get user security information"""
        try:
            security_doc = await self.user_security_collection.find_one({"user_id": user_id})
            
            # Get user info for email verification status
            user_doc = await self.users_collection.find_one({"id": user_id})
            
            if not security_doc:
                # Return default security info for new users
                return {
                    "user_id": user_id,
                    "email_verified": user_doc.get("email_verified", False) if user_doc else False,
                    "two_factor_enabled": False,
                    "failed_login_attempts": 0,
                    "account_locked_until": None,
                    "created_at": user_doc.get("created_at") if user_doc else datetime.utcnow(),
                    "updated_at": user_doc.get("updated_at") if user_doc else datetime.utcnow()
                }
            
            # Remove sensitive data
            security_doc.pop("_id", None)
            security_doc.pop("two_factor_secret", None)
            security_doc.pop("backup_codes", None)
            security_doc.pop("email_verification_token", None)
            security_doc.pop("password_reset_token", None)
            security_doc.pop("email_verification_expires", None)
            security_doc.pop("password_reset_expires", None)
            
            # Ensure required fields are present
            if "email_verified" not in security_doc and user_doc:
                security_doc["email_verified"] = user_doc.get("email_verified", False)
            
            if "two_factor_enabled" not in security_doc:
                security_doc["two_factor_enabled"] = False
                
            if "failed_login_attempts" not in security_doc:
                security_doc["failed_login_attempts"] = 0
            
            return security_doc
            
        except Exception as e:
            logger.error(f"Failed to get security info for user {user_id}: {e}")
            return None
    
    async def get_security_events(self, user_id: str, limit: int = 20) -> List[dict]:
        """Get recent security events for user"""
        try:
            events = await self.security_events_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit).to_list(None)
            
            for event in events:
                event.pop("_id", None)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get security events for user {user_id}: {e}")
            return []
    
    async def _log_security_event(self, user_id: str, event_type: str, details: dict = None):
        """Log security event"""
        try:
            event = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "event_type": event_type,
                "details": details or {},
                "created_at": datetime.utcnow()
            }
            
            await self.security_events_collection.insert_one(event)
            
        except Exception as e:
            logger.error(f"Failed to log security event {event_type} for user {user_id}: {e}")