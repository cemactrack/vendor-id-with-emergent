import asyncio
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.trust_models import *
import random
import string

logger = logging.getLogger(__name__)

class TrustValidationService:
    """Service for profile validation, trust scoring, and business verification"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.vendor_profiles_collection = db.enhanced_vendor_profiles
        self.trust_badges_collection = db.trust_badges
        self.validation_rules_collection = db.profile_validation_rules
        self.address_verifications_collection = db.address_verifications
        self.phone_verifications_collection = db.phone_verifications
        self.profile_freshness_collection = db.profile_freshness_checks
        
        # Validation rules will be initialized on first use
    
    async def validate_vendor_profile(self, vendor_id: str) -> ProfileValidationResult:
        """Comprehensive profile validation with trust scoring"""
        try:
            # Get vendor profile
            profile_data = await self.vendor_profiles_collection.find_one({"vendor_id": vendor_id})
            if not profile_data:
                return ProfileValidationResult(
                    vendor_id=vendor_id,
                    is_valid=False,
                    completion_score=0.0,
                    validation_errors=["Vendor profile not found"]
                )
            
            profile_data.pop("_id", None)
            profile = EnhancedVendorProfile(**profile_data)
            
            # Get validation rules
            rules = await self._get_validation_rules()
            
            # Validate against rules
            missing_fields = []
            validation_errors = []
            recommendations = []
            
            for rule in rules:
                field_value = getattr(profile, rule.field_name, None)
                
                # Check mandatory fields
                if rule.is_mandatory and not field_value:
                    missing_fields.append(rule.field_name)
                    validation_errors.append(f"Missing mandatory field: {rule.rule_name}")
                
                # Check minimum length
                if field_value and rule.minimum_length:
                    if isinstance(field_value, str) and len(field_value) < rule.minimum_length:
                        validation_errors.append(f"{rule.rule_name} must be at least {rule.minimum_length} characters")
                
                # Check validation pattern
                if field_value and rule.validation_pattern:
                    if isinstance(field_value, str) and not re.match(rule.validation_pattern, field_value):
                        validation_errors.append(f"{rule.rule_name} format is invalid")
                
                # Check verification requirements
                if rule.verification_required and field_value:
                    verification_field = f"{rule.field_name}_verified"
                    if not getattr(profile, verification_field, False):
                        recommendations.append(f"Verify {rule.rule_name} to increase trust score")
            
            # Calculate completion score
            completion_score = profile.calculate_completion_score()
            
            # Calculate trust score
            trust_score = await self._calculate_trust_score(profile)
            
            # Determine next verification level
            next_level = self._get_next_verification_level(profile, completion_score, trust_score)
            
            # Update profile scores
            await self._update_profile_scores(vendor_id, completion_score, trust_score)
            
            return ProfileValidationResult(
                vendor_id=vendor_id,
                is_valid=len(validation_errors) == 0,
                completion_score=completion_score,
                missing_mandatory_fields=missing_fields,
                validation_errors=validation_errors,
                recommendations=recommendations,
                trust_score=trust_score,
                next_verification_level=next_level
            )
            
        except Exception as e:
            logger.error(f"Profile validation failed for {vendor_id}: {e}")
            raise
    
    async def verify_business_address(self, request: AddressVerificationRequest) -> AddressVerificationResult:
        """Verify business address using external services"""
        try:
            # Simulate address verification (in production, use Google Places API, etc.)
            full_address = f"{request.address}, {request.city}, {request.state}, {request.country}"
            
            # Mock verification logic
            confidence = 0.85  # Would be from actual API
            is_verified = confidence > 0.7
            
            # Simulate address components
            address_components = {
                "street_number": "123",
                "route": request.address.split()[0] if request.address else "",
                "locality": request.city,
                "administrative_area_level_1": request.state,
                "country": request.country,
                "postal_code": request.postal_code or "00000"
            }
            
            # Mock coordinates
            coordinates = {
                "lat": 6.5244 + random.uniform(-0.1, 0.1),  # Lagos area
                "lng": 3.3792 + random.uniform(-0.1, 0.1)
            }
            
            result = AddressVerificationResult(
                vendor_id=request.vendor_id,
                original_address=full_address,
                verified_address=full_address if is_verified else None,
                is_verified=is_verified,
                verification_confidence=confidence,
                verification_method=request.verification_method,
                coordinates=coordinates if is_verified else None,
                address_components=address_components,
                verification_notes="Address verified successfully" if is_verified else "Address could not be verified"
            )
            
            # Store verification result
            result_dict = result.dict()
            await self.address_verifications_collection.insert_one(result_dict)
            result_dict.pop("_id", None)
            
            # Update vendor profile
            if is_verified:
                await self.vendor_profiles_collection.update_one(
                    {"vendor_id": request.vendor_id},
                    {
                        "$set": {
                            "address_verified": True,
                            "address_verification_method": request.verification_method,
                            "address_verified_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Award trust badge
                await self._award_trust_badge(request.vendor_id, TrustBadgeType.ADDRESS_VERIFIED)
            
            return result
            
        except Exception as e:
            logger.error(f"Address verification failed: {e}")
            raise
    
    async def verify_phone_number(self, request: PhoneVerificationRequest) -> PhoneVerificationResult:
        """Verify phone number with SMS/call verification"""
        try:
            # Generate verification code
            verification_code = ''.join(random.choices(string.digits, k=6))
            
            # Simulate phone verification (in production, use Twilio, etc.)
            is_verified = random.choice([True, True, False])  # 66% success rate for demo
            
            # Mock carrier info
            carrier_info = {
                "carrier_name": "MTN Nigeria" if request.country_code == "+234" else "Unknown",
                "line_type": "mobile",
                "country_code": request.country_code
            }
            
            result = PhoneVerificationResult(
                vendor_id=request.vendor_id,
                phone_number=request.phone_number,
                is_verified=is_verified,
                verification_code=verification_code if not is_verified else None,
                verification_method=request.verification_method,
                carrier_info=carrier_info,
                is_mobile=True,
                verification_attempts=1,
                verified_at=datetime.now(timezone.utc) if is_verified else None
            )
            
            # Store verification result
            result_dict = result.dict()
            await self.phone_verifications_collection.insert_one(result_dict)
            result_dict.pop("_id", None)
            
            # Update vendor profile if verified
            if is_verified:
                await self.vendor_profiles_collection.update_one(
                    {"vendor_id": request.vendor_id},
                    {
                        "$set": {
                            "primary_contact_verified": True,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                
                # Award trust badge
                await self._award_trust_badge(request.vendor_id, TrustBadgeType.PHONE_VERIFIED)
            
            return result
            
        except Exception as e:
            logger.error(f"Phone verification failed: {e}")
            raise
    
    async def check_profile_freshness(self, vendor_id: str) -> ProfileFreshnessCheck:
        """Check profile freshness and recommend updates"""
        try:
            profile = await self.vendor_profiles_collection.find_one({"vendor_id": vendor_id})
            if not profile:
                raise ValueError("Vendor profile not found")
            
            last_update = profile.get("updated_at", profile.get("created_at"))
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            
            days_since_update = (datetime.now(timezone.utc) - last_update).days
            
            # Calculate freshness score (100 for recent, decreases over time)
            if days_since_update <= 30:
                freshness_score = 100.0
            elif days_since_update <= 90:
                freshness_score = 100.0 - ((days_since_update - 30) * 1.5)  # Decrease 1.5 per day
            else:
                freshness_score = max(10.0, 100.0 - days_since_update)
            
            # Determine if update is required
            requires_update = days_since_update > 90 or freshness_score < 50
            
            # Generate recommendations
            recommendations = []
            if days_since_update > 60:
                recommendations.append("Update business description and services")
            if days_since_update > 90:
                recommendations.append("Verify contact information is current")
                recommendations.append("Update business photos if needed")
            if days_since_update > 180:
                recommendations.append("Review and update all profile information")
            
            freshness_check = ProfileFreshnessCheck(
                vendor_id=vendor_id,
                last_update=last_update,
                days_since_update=days_since_update,
                freshness_score=freshness_score,
                requires_update=requires_update,
                recommended_updates=recommendations
            )
            
            # Store freshness check
            freshness_dict = freshness_check.dict()
            await self.profile_freshness_collection.insert_one(freshness_dict)
            freshness_dict.pop("_id", None)
            
            # Update profile freshness score
            await self.vendor_profiles_collection.update_one(
                {"vendor_id": vendor_id},
                {"$set": {"profile_freshness_score": freshness_score}}
            )
            
            return freshness_check
            
        except Exception as e:
            logger.error(f"Profile freshness check failed: {e}")
            raise
    
    async def award_trust_badge(self, vendor_id: str, badge_type: TrustBadgeType, 
                              verification_data: Dict[str, Any] = None) -> TrustBadge:
        """Award trust badge to vendor"""
        try:
            # Check if badge already exists
            existing_badge = await self.trust_badges_collection.find_one({
                "vendor_id": vendor_id,
                "badge_type": badge_type.value
            })
            
            if existing_badge:
                logger.info(f"Badge {badge_type.value} already exists for vendor {vendor_id}")
                existing_badge.pop("_id", None)
                return TrustBadge(**existing_badge)
            
            # Create new badge
            badge_info = self._get_badge_info(badge_type)
            
            badge = TrustBadge(
                vendor_id=vendor_id,
                badge_type=badge_type,
                badge_name=badge_info["name"],
                badge_description=badge_info["description"],
                verification_data=verification_data or {},
                display_order=badge_info["display_order"]
            )
            
            # Store badge
            badge_dict = badge.dict()
            await self.trust_badges_collection.insert_one(badge_dict)
            badge_dict.pop("_id", None)
            
            # Update vendor profile trust badges
            await self._update_vendor_trust_badges(vendor_id)
            
            logger.info(f"Awarded badge {badge_type.value} to vendor {vendor_id}")
            return badge
            
        except Exception as e:
            logger.error(f"Failed to award trust badge: {e}")
            raise
    
    async def _calculate_trust_score(self, profile: EnhancedVendorProfile) -> float:
        """Calculate comprehensive trust score"""
        try:
            score = 0.0
            
            # Base profile completion (40 points)
            completion_factor = profile.profile_completion_score / 100.0
            score += completion_factor * 40
            
            # Verification status (30 points)
            verification_points = 0
            if profile.primary_contact_verified:
                verification_points += 10
            if profile.address_verified:
                verification_points += 10
            if len(profile.trust_badges) >= 3:
                verification_points += 10
            score += verification_points
            
            # Business credibility (20 points)
            if profile.established_year and profile.established_year <= (datetime.now().year - 2):
                score += 10  # 2+ years in business
            if len(profile.business_photos) >= 3:
                score += 5  # Has business photos
            if len(profile.client_testimonials) >= 2:
                score += 5  # Has testimonials
            
            # Activity and freshness (10 points)
            freshness_factor = profile.profile_freshness_score / 100.0
            score += freshness_factor * 10
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Trust score calculation failed: {e}")
            return 0.0
    
    async def _get_validation_rules(self) -> List[ProfileValidationRule]:
        """Get profile validation rules"""
        try:
            rules_data = await self.validation_rules_collection.find({}).to_list(length=None)
            rules = []
            for rule_data in rules_data:
                rule_data.pop("_id", None)
                rules.append(ProfileValidationRule(**rule_data))
            return rules
        except Exception:
            # Return default rules if none exist
            return self._get_default_validation_rules()
    
    def _get_default_validation_rules(self) -> List[ProfileValidationRule]:
        """Default validation rules"""
        return [
            ProfileValidationRule(
                rule_name="Business Name",
                field_name="business_name",
                is_mandatory=True,
                minimum_length=3,
                points_value=10,
                category="basic"
            ),
            ProfileValidationRule(
                rule_name="Business Description",
                field_name="business_description",
                is_mandatory=True,
                minimum_length=50,
                points_value=15,
                category="basic"
            ),
            ProfileValidationRule(
                rule_name="Business Address",
                field_name="business_address",
                is_mandatory=True,
                minimum_length=10,
                verification_required=True,
                points_value=10,
                category="contact"
            ),
            ProfileValidationRule(
                rule_name="Business Phone",
                field_name="business_contacts",
                is_mandatory=True,
                verification_required=True,
                points_value=10,
                category="contact"
            ),
            ProfileValidationRule(
                rule_name="Registration Number",
                field_name="registration_number",
                is_mandatory=True,
                minimum_length=5,
                points_value=10,
                category="business"
            )
        ]
    
    def _get_badge_info(self, badge_type: TrustBadgeType) -> Dict[str, Any]:
        """Get badge information"""
        badge_info = {
            TrustBadgeType.EMAIL_VERIFIED: {
                "name": "Email Verified",
                "description": "Email address has been verified",
                "display_order": 1
            },
            TrustBadgeType.PHONE_VERIFIED: {
                "name": "Phone Verified", 
                "description": "Phone number has been verified",
                "display_order": 2
            },
            TrustBadgeType.ADDRESS_VERIFIED: {
                "name": "Address Verified",
                "description": "Business address has been verified",
                "display_order": 3
            },
            TrustBadgeType.BUSINESS_REGISTERED: {
                "name": "Business Registered",
                "description": "Business registration verified",
                "display_order": 4
            }
        }
        
        return badge_info.get(badge_type, {
            "name": badge_type.value.replace("_", " ").title(),
            "description": f"{badge_type.value.replace('_', ' ').title()} verified",
            "display_order": 99
        })
    
    def _get_next_verification_level(self, profile: EnhancedVendorProfile, 
                                   completion_score: float, trust_score: float) -> Optional[BusinessVerificationLevel]:
        """Determine next verification level"""
        current_level = profile.verification_level
        
        if current_level == BusinessVerificationLevel.BASIC and completion_score >= 75:
            return BusinessVerificationLevel.ENHANCED
        elif current_level == BusinessVerificationLevel.ENHANCED and trust_score >= 75:
            return BusinessVerificationLevel.PREMIUM
        elif current_level == BusinessVerificationLevel.PREMIUM and trust_score >= 85:
            return BusinessVerificationLevel.ENTERPRISE
        
        return None
    
    async def _update_profile_scores(self, vendor_id: str, completion_score: float, trust_score: float):
        """Update profile completion and trust scores"""
        try:
            # Determine completion status
            if completion_score < 60:
                status = ProfileCompletionStatus.INCOMPLETE
            elif completion_score < 75:
                status = ProfileCompletionStatus.BASIC
            elif completion_score < 90:
                status = ProfileCompletionStatus.COMPLETE
            else:
                status = ProfileCompletionStatus.COMPREHENSIVE
            
            await self.vendor_profiles_collection.update_one(
                {"vendor_id": vendor_id},
                {
                    "$set": {
                        "profile_completion_score": completion_score,
                        "profile_completion_status": status.value,
                        "trust_score": trust_score,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to update profile scores: {e}")
    
    async def _update_vendor_trust_badges(self, vendor_id: str):
        """Update vendor profile with latest trust badges"""
        try:
            badges_data = await self.trust_badges_collection.find({
                "vendor_id": vendor_id,
                "is_active": True
            }).sort("display_order", 1).to_list(length=None)
            
            badges = []
            for badge_data in badges_data:
                badge_data.pop("_id", None)
                badges.append(badge_data)
            
            await self.vendor_profiles_collection.update_one(
                {"vendor_id": vendor_id},
                {"$set": {"trust_badges": badges}}
            )
        except Exception as e:
            logger.error(f"Failed to update vendor trust badges: {e}")
    
    async def _award_trust_badge(self, vendor_id: str, badge_type: TrustBadgeType):
        """Internal method to award trust badge"""
        try:
            await self.award_trust_badge(vendor_id, badge_type)
        except Exception as e:
            logger.error(f"Failed to award trust badge {badge_type}: {e}")
    
    async def _initialize_validation_rules(self):
        """Initialize default validation rules if none exist"""
        try:
            existing_count = await self.validation_rules_collection.count_documents({})
            if existing_count == 0:
                default_rules = self._get_default_validation_rules()
                rules_data = [rule.dict() for rule in default_rules]
                await self.validation_rules_collection.insert_many(rules_data)
                logger.info(f"Initialized {len(default_rules)} default validation rules")
        except Exception as e:
            logger.error(f"Failed to initialize validation rules: {e}")