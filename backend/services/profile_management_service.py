import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.profile_management_models import *
from models.trust_models import TrustBadgeType
import uuid

logger = logging.getLogger(__name__)

class ProfileManagementService:
    """Service for comprehensive vendor profile management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.vendor_profiles_collection = db.vendor_profiles
        self.services_collection = db.service_offerings
        self.contacts_collection = db.business_contacts
        self.inquiries_collection = db.service_inquiries
        self.analytics_collection = db.business_analytics
        self.visits_collection = db.profile_visits
        self.contact_submissions_collection = db.contact_form_submissions
        
    async def update_vendor_profile(self, vendor_id: str, update_request: ProfileUpdateRequest) -> ProfileUpdateResponse:
        """Update vendor profile with comprehensive validation"""
        try:
            updated_fields = []
            validation_errors = []
            badges_earned = []
            
            # Get current profile
            current_profile = await self.vendor_profiles_collection.find_one({"vendor_id": vendor_id})
            if not current_profile:
                raise ValueError("Vendor profile not found")
            
            # Build update data
            update_data = {"updated_at": datetime.now(timezone.utc)}
            
            # Basic Information Updates
            if update_request.business_name:
                update_data["business_name"] = update_request.business_name
                updated_fields.append("business_name")
            
            if update_request.business_description:
                if len(update_request.business_description) < 50:
                    validation_errors.append("Business description must be at least 50 characters")
                else:
                    update_data["business_description"] = update_request.business_description
                    updated_fields.append("business_description")
            
            if update_request.tagline:
                update_data["tagline"] = update_request.tagline
                updated_fields.append("tagline")
            
            if update_request.website:
                update_data["website"] = update_request.website
                updated_fields.append("website")
            
            # Address Information
            address_fields = ["business_address", "city", "state", "country", "postal_code"]
            for field in address_fields:
                value = getattr(update_request, field, None)
                if value:
                    update_data[field] = value
                    updated_fields.append(field)
            
            # Business Details
            if update_request.established_year:
                current_year = datetime.now().year
                if update_request.established_year > current_year:
                    validation_errors.append("Established year cannot be in the future")
                elif update_request.established_year < 1800:
                    validation_errors.append("Established year seems too old")
                else:
                    update_data["established_year"] = update_request.established_year
                    updated_fields.append("established_year")
            
            if update_request.employee_count is not None:
                update_data["employee_count"] = update_request.employee_count
                updated_fields.append("employee_count")
            
            if update_request.annual_revenue:
                update_data["annual_revenue"] = update_request.annual_revenue
                updated_fields.append("annual_revenue")
            
            # Business Hours
            if update_request.business_hours:
                # Validate business hours
                if len(update_request.business_hours) > 7:
                    validation_errors.append("Maximum 7 business hours entries allowed")
                else:
                    business_hours_data = [hour.dict() for hour in update_request.business_hours]
                    update_data["business_hours"] = business_hours_data
                    updated_fields.append("business_hours")
            
            # Business Contacts
            if update_request.business_contacts:
                # Validate contacts
                if len(update_request.business_contacts) > 10:
                    validation_errors.append("Maximum 10 business contacts allowed")
                else:
                    # Ensure only one primary contact
                    primary_count = sum(1 for contact in update_request.business_contacts if contact.is_primary)
                    if primary_count > 1:
                        validation_errors.append("Only one primary contact allowed")
                    elif primary_count == 0:
                        validation_errors.append("At least one primary contact required")
                    else:
                        contacts_data = [contact.dict() for contact in update_request.business_contacts]
                        update_data["business_contacts"] = contacts_data
                        updated_fields.append("business_contacts")
            
            # Social Media
            if update_request.social_media:
                social_media_data = [social.dict() for social in update_request.social_media]
                update_data["social_media"] = social_media_data
                updated_fields.append("social_media")
            
            # Visual Content
            if update_request.logo_url:
                update_data["logo_url"] = update_request.logo_url
                updated_fields.append("logo_url")
            
            if update_request.cover_image_url:
                update_data["cover_image_url"] = update_request.cover_image_url
                updated_fields.append("cover_image_url")
            
            if update_request.business_images:
                images_data = [img.dict() for img in update_request.business_images]
                update_data["business_images"] = images_data
                updated_fields.append("business_images")
            
            # Stop if there are validation errors
            if validation_errors:
                return ProfileUpdateResponse(
                    success=False,
                    validation_errors=validation_errors,
                    new_completion_score=0.0,
                    new_trust_score=0.0,
                    message="Profile update failed due to validation errors"
                )
            
            # Update the profile
            await self.vendor_profiles_collection.update_one(
                {"vendor_id": vendor_id},
                {"$set": update_data}
            )
            
            # Handle services separately if provided
            if update_request.services:
                await self._update_vendor_services(vendor_id, update_request.services)
                updated_fields.append("services")
            
            # Recalculate scores
            new_completion_score = await self._calculate_completion_score(vendor_id)
            new_trust_score = await self._calculate_trust_score(vendor_id)
            
            # Update scores in profile
            await self.vendor_profiles_collection.update_one(
                {"vendor_id": vendor_id},
                {
                    "$set": {
                        "profile_completion_score": new_completion_score,
                        "trust_score": new_trust_score
                    }
                }
            )
            
            # Check for new badges
            badges_earned = await self._check_and_award_badges(vendor_id, updated_fields)
            
            return ProfileUpdateResponse(
                success=True,
                updated_fields=updated_fields,
                new_completion_score=new_completion_score,
                new_trust_score=new_trust_score,
                badges_earned=badges_earned,
                message=f"Profile updated successfully. {len(updated_fields)} fields updated."
            )
            
        except Exception as e:
            logger.error(f"Profile update failed for {vendor_id}: {e}")
            raise
    
    async def get_vendor_services(self, vendor_id: str, status: Optional[str] = None) -> ServiceOfferingResponse:
        """Get vendor services with filtering"""
        try:
            query = {"vendor_id": vendor_id}
            if status:
                query["status"] = status
            
            services_data = await self.services_collection.find(query).to_list(length=None)
            
            services = []
            categories = set()
            
            for service_data in services_data:
                service_data.pop("_id", None)
                service = ServiceOffering(**service_data)
                services.append(service)
                categories.add(service.category.value)
            
            active_count = len([s for s in services if s.status == ServiceStatus.ACTIVE])
            
            return ServiceOfferingResponse(
                services=services,
                total_count=len(services),
                active_count=active_count,
                categories=list(categories)
            )
            
        except Exception as e:
            logger.error(f"Failed to get vendor services: {e}")
            raise
    
    async def create_service_offering(self, vendor_id: str, service: ServiceOffering) -> ServiceOffering:
        """Create new service offering"""
        try:
            service.vendor_id = vendor_id
            service.created_at = datetime.now(timezone.utc)
            service.updated_at = datetime.now(timezone.utc)
            
            # Validate required fields
            if not service.service_name or len(service.service_name) < 3:
                raise ValueError("Service name must be at least 3 characters")
            
            if not service.service_description or len(service.service_description) < 20:
                raise ValueError("Service description must be at least 20 characters")
            
            if service.pricing_type != PricingType.CUSTOM and not service.base_price:
                raise ValueError("Base price is required for non-custom pricing")
            
            # Store service
            service_dict = service.dict()
            await self.services_collection.insert_one(service_dict)
            service_dict.pop("_id", None)
            
            logger.info(f"Created service {service.service_name} for vendor {vendor_id}")
            return service
            
        except Exception as e:
            logger.error(f"Failed to create service offering: {e}")
            raise
    
    async def update_service_offering(self, service_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing service offering"""
        try:
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.services_collection.update_one(
                {"service_id": service_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update service offering: {e}")
            raise
    
    async def delete_service_offering(self, service_id: str, vendor_id: str) -> bool:
        """Delete service offering (soft delete)"""
        try:
            result = await self.services_collection.update_one(
                {"service_id": service_id, "vendor_id": vendor_id},
                {
                    "$set": {
                        "status": ServiceStatus.ARCHIVED.value,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete service offering: {e}")
            raise
    
    async def submit_service_inquiry(self, inquiry: ServiceInquiry) -> ServiceInquiry:
        """Submit inquiry for a service"""
        try:
            inquiry.created_at = datetime.now(timezone.utc)
            
            # Store inquiry
            inquiry_dict = inquiry.dict()
            await self.inquiries_collection.insert_one(inquiry_dict)
            inquiry_dict.pop("_id", None)
            
            # Update service inquiry count
            await self.services_collection.update_one(
                {"service_id": inquiry.service_id},
                {"$inc": {"inquiries_count": 1}}
            )
            
            logger.info(f"Service inquiry submitted for service {inquiry.service_id}")
            return inquiry
            
        except Exception as e:
            logger.error(f"Failed to submit service inquiry: {e}")
            raise
    
    async def get_vendor_inquiries(self, vendor_id: str, status: Optional[str] = None) -> List[ServiceInquiry]:
        """Get service inquiries for vendor"""
        try:
            query = {"vendor_id": vendor_id}
            if status:
                query["status"] = status
            
            inquiries_data = await self.inquiries_collection.find(query).sort("created_at", -1).to_list(length=None)
            
            inquiries = []
            for inquiry_data in inquiries_data:
                inquiry_data.pop("_id", None)
                inquiries.append(ServiceInquiry(**inquiry_data))
            
            return inquiries
            
        except Exception as e:
            logger.error(f"Failed to get vendor inquiries: {e}")
            raise
    
    async def track_profile_visit(self, vendor_id: str, visit_data: Dict[str, Any]) -> ProfileVisit:
        """Track profile visit for analytics"""
        try:
            visit = ProfileVisit(
                vendor_id=vendor_id,
                visitor_ip=visit_data.get("ip_address"),
                visitor_country=visit_data.get("country"),
                visitor_city=visit_data.get("city"),
                referrer=visit_data.get("referrer"),
                user_agent=visit_data.get("user_agent"),
                pages_viewed=visit_data.get("pages_viewed", []),
                time_on_site=visit_data.get("time_on_site", 0)
            )
            
            # Check if return visitor
            existing_visits = await self.visits_collection.count_documents({
                "vendor_id": vendor_id,
                "visitor_ip": visit.visitor_ip,
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)}
            })
            
            visit.is_return_visitor = existing_visits > 0
            
            # Store visit
            visit_dict = visit.dict()
            await self.visits_collection.insert_one(visit_dict)
            visit_dict.pop("_id", None)
            
            return visit
            
        except Exception as e:
            logger.error(f"Failed to track profile visit: {e}")
            raise
    
    async def generate_analytics(self, vendor_id: str, period: str = "monthly") -> BusinessAnalytics:
        """Generate business analytics for vendor"""
        try:
            # Calculate date range
            now = datetime.now(timezone.utc)
            if period == "daily":
                start_date = now - timedelta(days=1)
            elif period == "weekly":
                start_date = now - timedelta(days=7)
            else:  # monthly
                start_date = now - timedelta(days=30)
            
            # Get profile visits
            visits = await self.visits_collection.find({
                "vendor_id": vendor_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=None)
            
            # Get service inquiries
            inquiries = await self.inquiries_collection.find({
                "vendor_id": vendor_id,
                "created_at": {"$gte": start_date}
            }).to_list(length=None)
            
            # Calculate metrics
            profile_views = len(visits)
            unique_visitors = len(set(visit.get("visitor_ip") for visit in visits if visit.get("visitor_ip")))
            service_inquiries = len(inquiries)
            
            # Calculate conversion rate
            conversion_rate = (service_inquiries / profile_views * 100) if profile_views > 0 else 0.0
            
            # Traffic sources
            traffic_sources = {}
            for visit in visits:
                referrer = visit.get("referrer", "direct")
                if referrer.startswith("http"):
                    if "google" in referrer:
                        source = "organic"
                    elif "facebook" in referrer or "twitter" in referrer:
                        source = "social"
                    else:
                        source = "referral"
                else:
                    source = "direct"
                traffic_sources[source] = traffic_sources.get(source, 0) + 1
            
            analytics = BusinessAnalytics(
                vendor_id=vendor_id,
                analytics_period=period,
                profile_views=profile_views,
                profile_unique_visitors=unique_visitors,
                service_inquiries=service_inquiries,
                inquiry_to_conversion_rate=conversion_rate,
                traffic_sources=traffic_sources
            )
            
            # Store analytics
            analytics_dict = analytics.dict()
            await self.analytics_collection.insert_one(analytics_dict)
            analytics_dict.pop("_id", None)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to generate analytics: {e}")
            raise
    
    async def _update_vendor_services(self, vendor_id: str, services: List[ServiceOffering]):
        """Update vendor services"""
        try:
            # Delete existing services (soft delete)
            await self.services_collection.update_many(
                {"vendor_id": vendor_id},
                {"$set": {"status": ServiceStatus.ARCHIVED.value}}
            )
            
            # Insert new services
            for service in services:
                service.vendor_id = vendor_id
                await self.create_service_offering(vendor_id, service)
                
        except Exception as e:
            logger.error(f"Failed to update vendor services: {e}")
            raise
    
    async def _calculate_completion_score(self, vendor_id: str) -> float:
        """Calculate profile completion score"""
        try:
            profile = await self.vendor_profiles_collection.find_one({"vendor_id": vendor_id})
            if not profile:
                return 0.0
            
            score = 0.0
            
            # Basic info (30 points)
            if profile.get("business_name"): score += 5
            if profile.get("business_description") and len(profile.get("business_description", "")) >= 50: score += 10
            if profile.get("tagline"): score += 5
            if profile.get("logo_url"): score += 10
            
            # Contact info (25 points)
            if profile.get("business_address"): score += 5
            if profile.get("business_contacts"): score += 10
            if profile.get("website"): score += 5
            if profile.get("business_hours"): score += 5
            
            # Business details (20 points)
            if profile.get("established_year"): score += 5
            if profile.get("employee_count"): score += 5
            if profile.get("business_images"): score += 5
            if profile.get("social_media"): score += 5
            
            # Services (15 points)
            services_count = await self.services_collection.count_documents({
                "vendor_id": vendor_id,
                "status": ServiceStatus.ACTIVE.value
            })
            if services_count >= 1: score += 5
            if services_count >= 3: score += 5
            if services_count >= 5: score += 5
            
            # Verification (10 points)
            if profile.get("address_verified"): score += 5
            if profile.get("primary_contact_verified"): score += 5
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate completion score: {e}")
            return 0.0
    
    async def _calculate_trust_score(self, vendor_id: str) -> float:
        """Calculate trust score"""
        try:
            completion_score = await self._calculate_completion_score(vendor_id)
            
            # Get trust badges count
            badges_count = await self.db.trust_badges.count_documents({
                "vendor_id": vendor_id,
                "is_active": True
            })
            
            # Get reviews average rating
            avg_rating = 0.0
            reviews = await self.db.vendor_ratings.find({"vendor_id": vendor_id}).to_list(length=None)
            if reviews:
                total_rating = sum(review.get("overall_rating", 0) for review in reviews)
                avg_rating = total_rating / len(reviews)
            
            # Calculate trust score
            trust_score = (completion_score * 0.4) + (badges_count * 10) + (avg_rating * 10)
            
            return min(trust_score, 100.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate trust score: {e}")
            return 0.0
    
    async def _check_and_award_badges(self, vendor_id: str, updated_fields: List[str]) -> List[str]:
        """Check and award new badges based on profile updates"""
        try:
            badges_earned = []
            
            # Check for profile completion badge
            completion_score = await self._calculate_completion_score(vendor_id)
            if completion_score >= 75 and "business_description" in updated_fields:
                # Award comprehensive profile badge
                badges_earned.append("comprehensive_profile")
            
            # Check for business hours badge
            if "business_hours" in updated_fields:
                badges_earned.append("business_hours_provided")
            
            # Check for services badge
            if "services" in updated_fields:
                services_count = await self.services_collection.count_documents({
                    "vendor_id": vendor_id,
                    "status": ServiceStatus.ACTIVE.value
                })
                if services_count >= 3:
                    badges_earned.append("service_provider")
            
            return badges_earned
            
        except Exception as e:
            logger.error(f"Failed to check and award badges: {e}")
            return []