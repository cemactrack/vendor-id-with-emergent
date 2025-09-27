from typing import Optional, List, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vendor_ecosystem import *
from models.auth_models import *
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class VendorEcosystemService:
    """Enhanced vendor ecosystem service with improved error handling and validation"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.vendors_collection = db.vendor_profiles
        self.listings_collection = db.service_listings
        self.verifications_collection = db.verification_requests
        self.fraud_reports_collection = db.fraud_reports
        self.trust_events_collection = db.trust_events
        self.integrations_collection = db.marketplace_integrations
        self.jwt_secret = "vendor-ecosystem-jwt-secret-key-2024"
    
    # ===== USER MANAGEMENT =====
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with enhanced validation"""
        try:
            # Check if user already exists
            existing_user = await self.users_collection.find_one({"email": user_data.email})
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Validate password strength
            if len(user_data.password) < 8:
                raise ValueError("Password must be at least 8 characters long")
            
            # Hash password
            password_bytes = user_data.password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
            
            # Create user document
            user_dict = {
                "id": str(uuid.uuid4()),
                "email": user_data.email,
                "full_name": user_data.full_name,
                "password_hash": hashed_password,
                "role": user_data.role.value if isinstance(user_data.role, UserRole) else user_data.role,
                "phone": user_data.phone,
                "country": user_data.country.value if user_data.country else None,
                "email_verified": False,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Insert user
            result = await self.users_collection.insert_one(user_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create user")
            
            # Remove password hash from response
            user_dict.pop("password_hash", None)
            user_dict.pop("_id", None)
            
            logger.info(f"User created successfully: {user_data.email}")
            return User(**user_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create user {user_data.email}: {e}")
            raise ValueError("User creation failed")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with enhanced security"""
        try:
            user = await self.users_collection.find_one({"email": email, "is_active": True})
            if not user:
                return None
            
            # Verify password
            password_bytes = password.encode('utf-8')
            stored_hash = user.get("password_hash", "").encode('utf-8')
            
            if not stored_hash or not bcrypt.checkpw(password_bytes, stored_hash):
                return None
            
            # Remove sensitive data
            user.pop("password_hash", None)
            user.pop("_id", None)
            
            return User(**user)
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None
    
    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT token with enhanced security"""
        try:
            payload = {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "exp": datetime.now(timezone.utc) + timedelta(days=7),
                "iat": datetime.now(timezone.utc),
                "vendor_id": getattr(user, 'vendor_id', None)
            }
            
            return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
            
        except Exception as e:
            logger.error(f"Failed to generate JWT token for user {user.id}: {e}")
            raise ValueError("Token generation failed")
    
    # ===== VENDOR PROFILE MANAGEMENT =====
    
    async def create_vendor_profile(self, user_id: str, profile_data: VendorProfileCreate) -> VendorProfile:
        """Create vendor profile with validation"""
        try:
            # Check if user exists
            user = await self.users_collection.find_one({"id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Check if vendor profile already exists
            existing_profile = await self.vendors_collection.find_one({"user_id": user_id})
            if existing_profile:
                raise ValueError("Vendor profile already exists for this user")
            
            # Generate vendor ID
            user_country = user.get("country", "US")  # Get country from user, default to US
            vendor_id = f"VID-{user_country}-{str(uuid.uuid4())[:8].upper()}"
            
            # Create profile document
            profile_dict = {
                "id": str(uuid.uuid4()),  # Add missing id field
                "vendor_id": vendor_id,
                "user_id": user_id,
                **profile_data.dict(),
                "verification_status": VerificationStatus.PENDING,
                "trust_score": 0.0,
                "verification_level": 0,
                "profile_completion": self._calculate_profile_completion(profile_data),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Convert enums to values
            if isinstance(profile_dict.get("category"), BusinessCategory):
                profile_dict["category"] = profile_dict["category"].value
            
            result = await self.vendors_collection.insert_one(profile_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create vendor profile")
            
            # Remove MongoDB ObjectId
            profile_dict.pop("_id", None)
            
            logger.info(f"Vendor profile created: {vendor_id}")
            return VendorProfile(**profile_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create vendor profile for user {user_id}: {e}")
            raise ValueError("Profile creation failed")
    
    def _calculate_profile_completion(self, profile_data: VendorProfileCreate) -> int:
        """Calculate profile completion percentage"""
        fields = [
            profile_data.business_name,
            profile_data.business_description,
            profile_data.business_address,
            profile_data.website,
            profile_data.category,
            profile_data.registration_number
        ]
        
        completed_fields = sum(1 for field in fields if field and str(field).strip())
        return int((completed_fields / len(fields)) * 100)
    
    async def get_vendor_profile(self, vendor_id: str) -> Optional[VendorProfile]:
        """Get vendor profile by ID"""
        try:
            profile = await self.vendors_collection.find_one({"vendor_id": vendor_id})
            if not profile:
                return None
            
            profile.pop("_id", None)
            return VendorProfile(**profile)
            
        except Exception as e:
            logger.error(f"Failed to get vendor profile {vendor_id}: {e}")
            return None
    
    async def get_vendor_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive vendor dashboard data"""
        try:
            # Get vendor profile
            profile = await self.vendors_collection.find_one({"user_id": user_id})
            if not profile:
                raise ValueError("Vendor profile not found")
            
            vendor_id = profile["vendor_id"]
            
            # Get analytics (mock data for now)
            analytics = {
                "profile_views": 0,
                "listing_views": 0,
                "qr_scans": 0,
                "verification_checks": 0
            }
            
            # Get active listings
            listings_cursor = self.listings_collection.find({"vendor_id": vendor_id})
            active_listings = await listings_cursor.to_list(length=None)
            for listing in active_listings:
                listing.pop("_id", None)
            
            # Get verification status
            verification = await self.verifications_collection.find_one({"vendor_id": vendor_id})
            if verification:
                verification.pop("_id", None)
            
            # Get trust events
            events_cursor = self.trust_events_collection.find({"vendor_id": vendor_id}).sort("created_at", -1).limit(10)
            trust_events = await events_cursor.to_list(length=None)
            for event in trust_events:
                event.pop("_id", None)
            
            # Get integrations
            integrations_cursor = self.integrations_collection.find({"vendor_id": vendor_id})
            integrations = await integrations_cursor.to_list(length=None)
            for integration in integrations:
                integration.pop("_id", None)
            
            # Get documents (from document service)
            documents = []  # This would be populated from document service
            
            # Remove MongoDB ObjectId from profile
            profile.pop("_id", None)
            
            return {
                "profile": profile,
                "analytics": analytics,
                "active_listings": active_listings,
                "verification_status": verification,
                "trust_events": trust_events,
                "integrations": integrations,
                "documents": documents,
                "dashboard": profile  # For backward compatibility
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get vendor dashboard for user {user_id}: {e}")
            raise ValueError("Failed to load dashboard data")
    
    # ===== SERVICE LISTINGS =====
    
    async def create_service_listing(self, vendor_id: str, listing_data: ServiceListingCreate) -> ServiceListing:
        """Create service listing"""
        try:
            # Verify vendor exists
            vendor = await self.vendors_collection.find_one({"vendor_id": vendor_id})
            if not vendor:
                raise ValueError("Vendor not found")
            
            listing_dict = {
                "listing_id": str(uuid.uuid4()),
                "vendor_id": vendor_id,
                **listing_data.dict(),
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            # Convert enums to values
            if isinstance(listing_dict.get("category"), BusinessCategory):
                listing_dict["category"] = listing_dict["category"].value
            
            result = await self.listings_collection.insert_one(listing_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create listing")
            
            listing_dict.pop("_id", None)
            
            logger.info(f"Service listing created: {listing_dict['listing_id']}")
            return ServiceListing(**listing_dict)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create service listing for vendor {vendor_id}: {e}")
            raise ValueError("Listing creation failed")
    
    async def search_listings(self, query: Optional[str], category: Optional[BusinessCategory], 
                            location: Optional[str], limit: int, offset: int) -> Tuple[List[Dict], int]:
        """Search service listings with filters"""
        try:
            # Build search filter
            filter_dict = {"status": "active"}
            
            if query:
                filter_dict["$or"] = [
                    {"service_title": {"$regex": query, "$options": "i"}},
                    {"service_description": {"$regex": query, "$options": "i"}}
                ]
            
            if category:
                filter_dict["category"] = category.value
            
            if location:
                filter_dict["service_location"] = {"$regex": location, "$options": "i"}
            
            # Get total count
            total = await self.listings_collection.count_documents(filter_dict)
            
            # Get listings
            cursor = self.listings_collection.find(filter_dict).skip(offset).limit(limit)
            listings = await cursor.to_list(length=None)
            
            # Remove MongoDB ObjectIds
            for listing in listings:
                listing.pop("_id", None)
            
            return listings, total
            
        except Exception as e:
            logger.error(f"Failed to search listings: {e}")
            return [], 0
    
    # ===== VERIFICATION MANAGEMENT =====
    
    async def get_pending_verifications(self, limit: int) -> List[Dict]:
        """Get pending verification requests"""
        try:
            cursor = self.verifications_collection.find(
                {"status": VerificationStatus.PENDING}
            ).sort("created_at", 1).limit(limit)
            
            verifications = await cursor.to_list(length=None)
            for verification in verifications:
                verification.pop("_id", None)
            
            return verifications
            
        except Exception as e:
            logger.error(f"Failed to get pending verifications: {e}")
            return []
    
    async def update_verification_status(self, verification_id: str, status: VerificationStatus, 
                                       officer_id: str, notes: Optional[str]) -> bool:
        """Update verification status"""
        try:
            result = await self.verifications_collection.update_one(
                {"verification_id": verification_id},
                {
                    "$set": {
                        "status": status.value,
                        "verification_officer_id": officer_id,
                        "verification_notes": notes,
                        "verified_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Verification {verification_id} updated to {status.value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update verification status: {e}")
            return False
    
    # ===== FRAUD REPORTING =====
    
    async def report_fraud(self, reporter_id: str, reported_vendor_id: str, 
                          report_type: str, description: str, evidence_files: List[str]) -> Dict:
        """Create fraud report"""
        try:
            report_dict = {
                "report_id": str(uuid.uuid4()),
                "reporter_id": reporter_id,
                "reported_vendor_id": reported_vendor_id,
                "report_type": report_type,
                "description": description,
                "evidence_files": evidence_files,
                "status": "open",
                "priority": 1,
                "created_at": datetime.now(timezone.utc)
            }
            
            result = await self.fraud_reports_collection.insert_one(report_dict)
            if not result.inserted_id:
                raise ValueError("Failed to create fraud report")
            
            report_dict.pop("_id", None)
            
            logger.info(f"Fraud report created: {report_dict['report_id']}")
            return report_dict
            
        except Exception as e:
            logger.error(f"Failed to create fraud report: {e}")
            raise ValueError("Fraud report creation failed")
    
    # ===== PUBLIC VERIFICATION =====
    
    async def verify_vendor_public(self, vendor_id: str) -> Optional[Dict]:
        """Public vendor verification for QR codes"""
        try:
            vendor = await self.vendors_collection.find_one({
                "vendor_id": vendor_id,
                "verification_status": VerificationStatus.VERIFIED
            })
            
            if not vendor:
                return None
            
            verification_data = {
                "vendor_id": vendor["vendor_id"],
                "business_name": vendor["business_name"],
                "verification_status": vendor["verification_status"],
                "trust_score": vendor.get("trust_score", 0),
                "verification_level": vendor.get("verification_level", 0),
                "verified_since": vendor.get("verified_at"),
                "categories": [vendor.get("category")],
                "location": vendor.get("business_address"),
                "qr_verification_url": f"https://idecosystem.preview.emergentagent.com/verify/{vendor_id}"
            }
            
            return verification_data
            
        except Exception as e:
            logger.error(f"Failed to verify vendor {vendor_id} publicly: {e}")
            return None
    
    # ===== SYSTEM STATISTICS =====
    
    async def get_ecosystem_stats(self) -> Dict:
        """Get system-wide statistics"""
        try:
            # Get vendor statistics
            total_vendors = await self.vendors_collection.count_documents({})
            verified_vendors = await self.vendors_collection.count_documents(
                {"verification_status": VerificationStatus.VERIFIED}
            )
            pending_verification = await self.vendors_collection.count_documents(
                {"verification_status": VerificationStatus.PENDING}
            )
            
            # Get listing statistics
            active_listings = await self.listings_collection.count_documents({"status": "active"})
            
            # Get document statistics (mock for now)
            total_documents = 0
            
            # Calculate trust score average
            pipeline = [
                {"$group": {"_id": None, "avg_trust_score": {"$avg": "$trust_score"}}}
            ]
            trust_score_result = await self.vendors_collection.aggregate(pipeline).to_list(1)
            avg_trust_score = trust_score_result[0]["avg_trust_score"] if trust_score_result else 0
            
            # Get unique countries
            countries_pipeline = [
                {"$group": {"_id": "$country"}},
                {"$count": "countries_count"}
            ]
            countries_result = await self.vendors_collection.aggregate(countries_pipeline).to_list(1)
            countries_represented = countries_result[0]["countries_count"] if countries_result else 0
            
            # Get unique categories
            categories_pipeline = [
                {"$group": {"_id": "$category"}},
                {"$count": "categories_count"}
            ]
            categories_result = await self.vendors_collection.aggregate(categories_pipeline).to_list(1)
            categories_covered = categories_result[0]["categories_count"] if categories_result else 0
            
            # Get pending verification requests
            verification_requests_pending = await self.verifications_collection.count_documents(
                {"status": VerificationStatus.PENDING}
            )
            
            # Get open fraud reports
            fraud_reports_open = await self.fraud_reports_collection.count_documents({"status": "open"})
            
            return {
                "total_vendors": total_vendors,
                "verified_vendors": verified_vendors,
                "pending_verification": pending_verification,
                "active_listings": active_listings,
                "total_documents": total_documents,
                "trust_score_average": float(avg_trust_score or 0),
                "countries_represented": countries_represented,
                "categories_covered": categories_covered,
                "verification_requests_pending": verification_requests_pending,
                "fraud_reports_open": fraud_reports_open
            }
            
        except Exception as e:
            logger.error(f"Failed to get ecosystem stats: {e}")
            return {}