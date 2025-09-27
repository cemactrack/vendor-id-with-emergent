import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.security_models import *
try:
    import geoip2.database
    GEOIP_AVAILABLE = True
except ImportError:
    GEOIP_AVAILABLE = False
import re

logger = logging.getLogger(__name__)

class SecurityService:
    """Comprehensive security service for device trust, session management, and threat detection"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.devices_collection = db.device_fingerprints
        self.sessions_collection = db.session_security
        self.security_events_collection = db.security_events
        self.rate_limits_collection = db.api_rate_limits
        self.login_attempts_collection = db.login_attempts
        self.security_alerts_collection = db.security_alerts
        self.trusted_devices_collection = db.trusted_devices
        self.access_control_collection = db.access_control
        self.security_config_collection = db.security_configuration
        
    async def register_device(self, vendor_id: str, request_data: Dict[str, Any]) -> DeviceFingerprint:
        """Register a new device for the vendor"""
        try:
            # Create device fingerprint hash
            device_info = {
                "user_agent": request_data.get("user_agent", ""),
                "screen_resolution": request_data.get("screen_resolution", ""),
                "timezone": request_data.get("timezone", ""),
                "language": request_data.get("language", ""),
                "platform": request_data.get("platform", "")
            }
            
            device_hash = self._create_device_hash(device_info)
            
            # Check if device already exists
            existing_device = await self.devices_collection.find_one({
                "vendor_id": vendor_id,
                "device_hash": device_hash
            })
            
            if existing_device:
                # Update last seen
                await self.devices_collection.update_one(
                    {"device_id": existing_device["device_id"]},
                    {
                        "$set": {
                            "last_seen": datetime.now(timezone.utc),
                            "login_count": existing_device.get("login_count", 0) + 1
                        }
                    }
                )
                existing_device.pop("_id", None)
                return DeviceFingerprint(**existing_device)
            
            # Get location data
            location_data = await self._get_location_data(request_data.get("ip_address", ""))
            
            # Create new device fingerprint
            device = DeviceFingerprint(
                vendor_id=vendor_id,
                device_hash=device_hash,
                user_agent=request_data.get("user_agent", ""),
                screen_resolution=request_data.get("screen_resolution", ""),
                timezone=request_data.get("timezone", ""),
                language=request_data.get("language", ""),
                platform=request_data.get("platform", ""),
                browser=self._extract_browser_info(request_data.get("user_agent", "")),
                ip_address=request_data.get("ip_address", ""),
                location_data=location_data,
                is_mobile=self._is_mobile_device(request_data.get("user_agent", "")),
                trust_score=self._calculate_initial_trust_score(location_data, request_data)
            )
            
            # Store device
            device_dict = device.dict()
            await self.devices_collection.insert_one(device_dict)
            device_dict.pop("_id", None)
            
            # Log security event
            await self._log_security_event(
                vendor_id, SecurityEventType.DEVICE_REGISTERED, RiskLevel.LOW,
                f"New device registered: {device.platform} {device.browser}",
                request_data.get("ip_address", ""), request_data.get("user_agent", ""),
                device.device_id
            )
            
            logger.info(f"Device registered for vendor {vendor_id}: {device.device_id}")
            return device
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            raise
    
    async def verify_device_trust(self, device_id: str, vendor_id: str) -> bool:
        """Verify if a device is trusted for the vendor"""
        try:
            device_data = await self.devices_collection.find_one({
                "device_id": device_id,
                "vendor_id": vendor_id
            })
            
            if not device_data:
                return False
            
            device = DeviceFingerprint(**device_data)
            
            # Check device status
            if device.status in [DeviceStatus.BLOCKED, DeviceStatus.SUSPICIOUS]:
                return False
            
            # Check trust score threshold
            if device.trust_score < 60.0:  # Minimum trust score
                return False
            
            # Check for recent suspicious activity
            recent_alerts = await self.security_alerts_collection.count_documents({
                "vendor_id": vendor_id,
                "evidence.device_id": device_id,
                "status": "active",
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
            })
            
            if recent_alerts > 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify device trust: {e}")
            return False
    
    async def create_secure_session(self, vendor_id: str, device_id: str, 
                                  jwt_token_id: str, ip_address: str,
                                  session_duration_hours: int = 8) -> SessionSecurity:
        """Create a secure session with monitoring"""
        try:
            # Check concurrent sessions
            active_sessions = await self.sessions_collection.count_documents({
                "vendor_id": vendor_id,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            })
            
            # Get security config
            config = await self._get_security_config(vendor_id)
            max_concurrent = config.get("max_concurrent_sessions", 3)
            
            if active_sessions >= max_concurrent:
                # Deactivate oldest session
                await self._deactivate_oldest_session(vendor_id)
            
            # Get location data
            location_data = await self._get_location_data(ip_address)
            
            # Create session
            session = SessionSecurity(
                vendor_id=vendor_id,
                device_id=device_id,
                jwt_token_id=jwt_token_id,
                ip_address=ip_address,
                location_data=location_data,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=session_duration_hours),
                concurrent_sessions=active_sessions + 1,
                max_concurrent_allowed=max_concurrent
            )
            
            # Store session
            session_dict = session.dict()
            await self.sessions_collection.insert_one(session_dict)
            session_dict.pop("_id", None)
            
            logger.info(f"Secure session created for vendor {vendor_id}: {session.session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create secure session: {e}")
            raise
    
    async def check_rate_limit(self, vendor_id: str, endpoint: str, ip_address: str) -> bool:
        """Check if request is within rate limits"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get or create rate limit record
            rate_limit_data = await self.rate_limits_collection.find_one({
                "vendor_id": vendor_id,
                "endpoint": endpoint
            })
            
            if not rate_limit_data:
                # Create new rate limit record
                rate_limit = APIRateLimit(
                    vendor_id=vendor_id,
                    endpoint=endpoint
                )
                rate_limit_dict = rate_limit.dict()
                await self.rate_limits_collection.insert_one(rate_limit_dict)
                return True
            
            rate_limit = APIRateLimit(**rate_limit_data)
            
            # Check if currently blocked
            if rate_limit.blocked_until and current_time < rate_limit.blocked_until:
                return False
            
            # Reset counters if needed
            if (current_time - rate_limit.last_reset_minute).seconds >= 60:
                rate_limit.current_minute_count = 0
                rate_limit.last_reset_minute = current_time
            
            if (current_time - rate_limit.last_reset_hour).seconds >= 3600:
                rate_limit.current_hour_count = 0
                rate_limit.last_reset_hour = current_time
            
            if (current_time - rate_limit.last_reset_day).days >= 1:
                rate_limit.current_day_count = 0
                rate_limit.last_reset_day = current_time
            
            # Check limits
            if (rate_limit.current_minute_count >= rate_limit.requests_per_minute or
                rate_limit.current_hour_count >= rate_limit.requests_per_hour or
                rate_limit.current_day_count >= rate_limit.requests_per_day):
                
                # Block for escalating periods based on violation count
                block_duration = min(300 * (2 ** rate_limit.violation_count), 3600)  # Max 1 hour
                rate_limit.blocked_until = current_time + timedelta(seconds=block_duration)
                rate_limit.violation_count += 1
                
                # Log security event
                await self._log_security_event(
                    vendor_id, SecurityEventType.API_RATE_LIMIT_EXCEEDED, RiskLevel.MEDIUM,
                    f"Rate limit exceeded for {endpoint}",
                    ip_address, "", None
                )
                
                # Update rate limit record
                await self.rate_limits_collection.update_one(
                    {"limit_id": rate_limit.limit_id},
                    {"$set": rate_limit.dict()}
                )
                
                return False
            
            # Increment counters
            rate_limit.current_minute_count += 1
            rate_limit.current_hour_count += 1
            rate_limit.current_day_count += 1
            
            # Update rate limit record
            await self.rate_limits_collection.update_one(
                {"limit_id": rate_limit.limit_id},
                {"$set": rate_limit.dict()}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return True  # Allow request on error
    
    async def log_login_attempt(self, email: str, vendor_id: Optional[str], 
                              ip_address: str, user_agent: str, success: bool,
                              failure_reason: Optional[str] = None, 
                              two_fa_used: bool = False) -> LoginAttempt:
        """Log login attempt for security monitoring"""
        try:
            device_fingerprint = self._create_device_hash({
                "user_agent": user_agent,
                "ip_address": ip_address
            })
            
            location_data = await self._get_location_data(ip_address)
            risk_indicators = await self._analyze_login_risk(email, ip_address, user_agent, location_data)
            
            login_attempt = LoginAttempt(
                vendor_id=vendor_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                success=success,
                failure_reason=failure_reason,
                two_fa_used=two_fa_used,
                location_data=location_data,
                risk_indicators=risk_indicators,
                blocked_by_security=len(risk_indicators) > 2
            )
            
            # Store login attempt
            login_dict = login_attempt.dict()
            await self.login_attempts_collection.insert_one(login_dict)
            login_dict.pop("_id", None)
            
            # Check for suspicious patterns
            if not success or len(risk_indicators) > 1:
                await self._check_suspicious_login_patterns(email, ip_address)
            
            # Log security event
            event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED
            risk_level = RiskLevel.HIGH if len(risk_indicators) > 2 else RiskLevel.LOW
            
            await self._log_security_event(
                vendor_id or "unknown", event_type, risk_level,
                f"Login attempt: {email} - {'Success' if success else failure_reason}",
                ip_address, user_agent, None
            )
            
            return login_attempt
            
        except Exception as e:
            logger.error(f"Failed to log login attempt: {e}")
            raise
    
    async def generate_security_dashboard(self, vendor_id: str) -> SecurityDashboard:
        """Generate security dashboard data for vendor"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get active sessions count
            active_sessions = await self.sessions_collection.count_documents({
                "vendor_id": vendor_id,
                "is_active": True,
                "expires_at": {"$gt": current_time}
            })
            
            # Get trusted devices count
            trusted_devices = await self.devices_collection.count_documents({
                "vendor_id": vendor_id,
                "status": DeviceStatus.TRUSTED.value
            })
            
            # Get recent alerts
            recent_alerts_data = await self.security_alerts_collection.find({
                "vendor_id": vendor_id,
                "created_at": {"$gte": current_time - timedelta(days=30)}
            }).sort("created_at", -1).limit(10).to_list(length=10)
            
            recent_alerts = []
            for alert_data in recent_alerts_data:
                alert_data.pop("_id", None)
                recent_alerts.append(SecurityAlert(**alert_data))
            
            # Calculate risk summary
            risk_summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            for alert in recent_alerts:
                risk_summary[alert.severity.value] += 1
            
            # Calculate security score
            security_score = await self._calculate_security_score(vendor_id)
            
            # Generate recommendations
            recommendations = await self._generate_security_recommendations(vendor_id, security_score)
            
            dashboard = SecurityDashboard(
                vendor_id=vendor_id,
                security_score=security_score,
                active_sessions=active_sessions,
                trusted_devices=trusted_devices,
                recent_alerts=recent_alerts,
                risk_summary=risk_summary,
                compliance_status={
                    "two_fa_enabled": await self._check_two_fa_status(vendor_id),
                    "password_policy_compliant": await self._check_password_policy(vendor_id),
                    "device_trust_enabled": trusted_devices > 0
                },
                recommendations=recommendations,
                last_security_audit=current_time
            )
            
            return dashboard
            
        except Exception as e:
            logger.error(f"Failed to generate security dashboard: {e}")
            raise
    
    def _create_device_hash(self, device_info: Dict[str, Any]) -> str:
        """Create unique hash for device fingerprinting"""
        fingerprint_string = "|".join([
            device_info.get("user_agent", ""),
            device_info.get("screen_resolution", ""),
            device_info.get("timezone", ""),
            device_info.get("language", ""),
            device_info.get("platform", "")
        ])
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    async def _get_location_data(self, ip_address: str) -> Dict[str, Any]:
        """Get location data from IP address"""
        try:
            # In production, use actual GeoIP service
            # For now, return mock data
            return {
                "country": "Unknown",
                "city": "Unknown",
                "isp": "Unknown",
                "vpn_detected": False,
                "proxy_detected": False
            }
        except Exception:
            return {}
    
    def _extract_browser_info(self, user_agent: str) -> str:
        """Extract browser information from user agent"""
        if "Chrome" in user_agent:
            return "Chrome"
        elif "Firefox" in user_agent:
            return "Firefox"
        elif "Safari" in user_agent:
            return "Safari"
        elif "Edge" in user_agent:
            return "Edge"
        else:
            return "Unknown"
    
    def _is_mobile_device(self, user_agent: str) -> bool:
        """Check if device is mobile"""
        mobile_indicators = ["Mobile", "Android", "iPhone", "iPad", "Windows Phone"]
        return any(indicator in user_agent for indicator in mobile_indicators)
    
    def _calculate_initial_trust_score(self, location_data: Dict[str, Any], 
                                     request_data: Dict[str, Any]) -> float:
        """Calculate initial trust score for new device"""
        score = 50.0  # Base score
        
        # Location factors
        if location_data.get("vpn_detected"):
            score -= 20
        if location_data.get("proxy_detected"):
            score -= 15
        
        # Device factors
        if self._is_mobile_device(request_data.get("user_agent", "")):
            score += 10  # Mobile devices slightly more trusted
        
        # Browser factors
        browser = self._extract_browser_info(request_data.get("user_agent", ""))
        if browser in ["Chrome", "Firefox", "Safari", "Edge"]:
            score += 5
        
        return max(0.0, min(100.0, score))
    
    async def _log_security_event(self, vendor_id: str, event_type: SecurityEventType,
                                risk_level: RiskLevel, description: str,
                                ip_address: str, user_agent: str,
                                device_id: Optional[str] = None):
        """Log security event"""
        try:
            event = SecurityEvent(
                vendor_id=vendor_id,
                event_type=event_type,
                risk_level=risk_level,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id
            )
            
            event_dict = event.dict()
            await self.security_events_collection.insert_one(event_dict)
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    async def _analyze_login_risk(self, email: str, ip_address: str, 
                                user_agent: str, location_data: Dict[str, Any]) -> List[str]:
        """Analyze login attempt for risk indicators"""
        risk_indicators = []
        
        # Check for VPN/Proxy
        if location_data.get("vpn_detected"):
            risk_indicators.append("vpn_detected")
        if location_data.get("proxy_detected"):
            risk_indicators.append("proxy_detected")
        
        # Check for unusual location
        # In production, compare with user's typical locations
        
        # Check for multiple recent failed attempts
        recent_failures = await self.login_attempts_collection.count_documents({
            "email": email,
            "success": False,
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=1)}
        })
        
        if recent_failures >= 3:
            risk_indicators.append("multiple_failed_attempts")
        
        return risk_indicators
    
    async def _check_suspicious_login_patterns(self, email: str, ip_address: str):
        """Check for suspicious login patterns and create alerts"""
        # Implementation for detecting patterns like:
        # - Multiple locations in short time
        # - Brute force attempts
        # - Unusual timing patterns
        pass
    
    async def _get_security_config(self, vendor_id: str) -> Dict[str, Any]:
        """Get security configuration for vendor"""
        config_data = await self.security_config_collection.find_one({"vendor_id": vendor_id})
        if config_data:
            return config_data
        else:
            # Return default config
            return {
                "max_concurrent_sessions": 3,
                "session_timeout_minutes": 480,
                "two_fa_required": True
            }
    
    async def _deactivate_oldest_session(self, vendor_id: str):
        """Deactivate oldest active session"""
        oldest_session = await self.sessions_collection.find_one(
            {
                "vendor_id": vendor_id,
                "is_active": True,
                "expires_at": {"$gt": datetime.now(timezone.utc)}
            },
            sort=[("session_start", 1)]
        )
        
        if oldest_session:
            await self.sessions_collection.update_one(
                {"session_id": oldest_session["session_id"]},
                {"$set": {"is_active": False}}
            )
    
    async def _calculate_security_score(self, vendor_id: str) -> float:
        """Calculate overall security score for vendor"""
        score = 100.0
        
        # Check 2FA status
        if not await self._check_two_fa_status(vendor_id):
            score -= 30
        
        # Check for recent security alerts
        recent_alerts = await self.security_alerts_collection.count_documents({
            "vendor_id": vendor_id,
            "status": "active",
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
        })
        score -= min(recent_alerts * 5, 25)
        
        # Check trusted devices
        trusted_devices = await self.devices_collection.count_documents({
            "vendor_id": vendor_id,
            "status": DeviceStatus.TRUSTED.value
        })
        if trusted_devices == 0:
            score -= 15
        
        return max(0.0, score)
    
    async def _check_two_fa_status(self, vendor_id: str) -> bool:
        """Check if 2FA is enabled for vendor"""
        # This would check the user's 2FA status
        # Placeholder implementation
        return True
    
    async def _check_password_policy(self, vendor_id: str) -> bool:
        """Check if password meets policy requirements"""
        # This would check password policy compliance
        # Placeholder implementation
        return True
    
    async def _generate_security_recommendations(self, vendor_id: str, 
                                               security_score: float) -> List[str]:
        """Generate security recommendations based on current state"""
        recommendations = []
        
        if security_score < 70:
            recommendations.append("Enable two-factor authentication for better security")
        
        if security_score < 80:
            recommendations.append("Review and approve trusted devices")
            recommendations.append("Update password to meet policy requirements")
        
        # Check for recent suspicious activity
        recent_alerts = await self.security_alerts_collection.count_documents({
            "vendor_id": vendor_id,
            "status": "active",
            "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}
        })
        
        if recent_alerts > 0:
            recommendations.append("Review recent security alerts and take necessary actions")
        
        return recommendations