from typing import List, Optional, Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vendor_ecosystem import *
from datetime import datetime, timedelta
import random
import string
import hashlib
import secrets
import uuid
from passlib.context import CryptContext
import bcrypt
import jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os

class VendorEcosystemService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.vendors_collection = db.vendor_profiles
        self.documents_collection = db.documents
        self.listings_collection = db.service_listings
        self.verifications_collection = db.verification_requests
        self.analytics_collection = db.vendor_analytics
        self.integrations_collection = db.marketplace_integrations
        self.fraud_reports_collection = db.fraud_reports
        self.trust_events_collection = db.trust_events
        self.verification_actions_collection = db.verification_actions
        
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Use direct bcrypt as fallback for compatibility issues
        self.use_direct_bcrypt = True
        self.jwt_secret = os.getenv("JWT_SECRET", "fallback-secret-key")
    
    # User Management
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user account"""
        # Check if user already exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")
        
        user_id = str(uuid.uuid4())
        # Use direct bcrypt to avoid passlib compatibility issues
        if self.use_direct_bcrypt:
            password_bytes = user_data.password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        else:
            # Fix for bcrypt 72-byte limit issue with passlib
            password_to_hash = user_data.password
            if len(password_to_hash.encode('utf-8')) > 72:
                password_to_hash = password_to_hash[:72]
            hashed_password = self.pwd_context.hash(password_to_hash)
        
        user_dict = {
            "id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password,
            "full_name": user_data.full_name,
            "phone": user_data.phone,
            "country": user_data.country,
            "role": user_data.role,
            "is_active": True,
            "email_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None
        }
        
        await self.users_collection.insert_one(user_dict)
        user_dict.pop('password_hash')
        return User(**user_dict)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user login"""
        user_doc = await self.users_collection.find_one({"email": email})
        if not user_doc:
            return None
        
        # Use direct bcrypt to avoid passlib compatibility issues
        if self.use_direct_bcrypt:
            password_bytes = password.encode('utf-8')
            stored_hash = user_doc.get("password_hash").encode('utf-8')
            if not bcrypt.checkpw(password_bytes, stored_hash):
                return None
        else:
            # Fix for bcrypt 72-byte limit issue with passlib
            password_to_verify = password
            if len(password_to_verify.encode('utf-8')) > 72:
                password_to_verify = password_to_verify[:72]
                
            if not self.pwd_context.verify(password_to_verify, user_doc.get("password_hash")):
                return None
        
        # Update last login
        await self.users_collection.update_one(
            {"id": user_doc["id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        user_doc.pop('password_hash')
        user_doc.pop('_id', None)
        return User(**user_doc)
    
    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    # Vendor ID Generation
    def generate_vendor_id(self, country: CountryCode) -> str:
        """Generate unique vendor ID per country"""
        number = random.randint(1000, 9999)
        return f"VID-{country.value}-{number}"
    
    async def ensure_unique_vendor_id(self, country: CountryCode) -> str:
        """Ensure generated vendor ID is unique"""
        max_attempts = 100
        for _ in range(max_attempts):
            vendor_id = self.generate_vendor_id(country)
            existing = await self.vendors_collection.find_one({"vendor_id": vendor_id})
            if not existing:
                return vendor_id
        raise Exception("Unable to generate unique vendor ID")
    
    # Vendor Profile Management
    async def create_vendor_profile(self, user_id: str, profile_data: VendorProfileCreate) -> VendorProfile:
        """Create vendor profile"""
        # Get user to determine country
        user_doc = await self.users_collection.find_one({"id": user_id})
        if not user_doc:
            raise ValueError("User not found")
        
        # Check if vendor profile already exists
        existing_profile = await self.vendors_collection.find_one({"user_id": user_id})
        if existing_profile:
            raise ValueError("Vendor profile already exists for this user")
        
        vendor_id = await self.ensure_unique_vendor_id(CountryCode(user_doc["country"]))
        profile_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Calculate profile completion
        completion_score = self.calculate_profile_completion(profile_data)
        
        profile_dict = {
            "id": profile_id,
            "user_id": user_id,
            "vendor_id": vendor_id,
            "business_name": profile_data.business_name,
            "business_description": profile_data.business_description,
            "category": profile_data.category,
            "logo_url": None,
            "website": profile_data.website,
            "business_address": profile_data.business_address,
            "registration_number": profile_data.registration_number,
            "tax_id": profile_data.tax_id,
            "established_year": profile_data.established_year,
            "employee_count": profile_data.employee_count,
            "verification_status": VerificationStatus.PENDING,
            "verification_level": 0,
            "trust_score": 0.0,
            "profile_completion": completion_score,
            "created_at": now,
            "updated_at": now,
            "verified_at": None,
            "expires_at": None
        }
        
        await self.vendors_collection.insert_one(profile_dict)
        
        # Initialize analytics
        await self.initialize_vendor_analytics(vendor_id)
        
        # Create initial verification request
        await self.create_verification_request(vendor_id, user_id)
        
        profile_dict.pop('_id', None)
        return VendorProfile(**profile_dict)
    
    def calculate_profile_completion(self, profile_data: VendorProfileCreate) -> float:
        """Calculate profile completion percentage"""
        fields = [
            profile_data.business_name,
            profile_data.business_description,
            profile_data.category,
            profile_data.website,
            profile_data.business_address,
            profile_data.registration_number,
            profile_data.tax_id,
            profile_data.established_year,
            profile_data.employee_count
        ]
        
        completed_fields = sum(1 for field in fields if field is not None and str(field).strip())
        return (completed_fields / len(fields)) * 100
    
    async def get_vendor_profile(self, vendor_id: str) -> Optional[VendorProfile]:
        """Get vendor profile by vendor ID"""
        profile_doc = await self.vendors_collection.find_one({"vendor_id": vendor_id})
        if profile_doc:
            profile_doc.pop('_id', None)
            return VendorProfile(**profile_doc)
        return None
    
    async def update_vendor_profile(self, vendor_id: str, update_data: dict) -> Optional[VendorProfile]:
        """Update vendor profile"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.vendors_collection.update_one(
            {"vendor_id": vendor_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return await self.get_vendor_profile(vendor_id)
        return None
    
    # Document Management
    async def upload_document(self, vendor_id: str, document_data: DocumentCreate) -> Document:
        """Upload and store vendor document"""
        document_id = str(uuid.uuid4())
        
        # In a real implementation, you'd save the file to storage (S3, etc.)
        # For now, we'll simulate file storage
        file_path = f"documents/{vendor_id}/{document_id}_{document_data.filename}"
        
        document_dict = {
            "id": document_id,
            "vendor_id": vendor_id,
            "document_type": document_data.document_type,
            "file_path": file_path,
            "original_filename": document_data.filename,
            "file_size": len(document_data.file_data),
            "mime_type": self.get_mime_type(document_data.filename),
            "description": document_data.description,
            "verification_status": VerificationStatus.PENDING,
            "verification_notes": None,
            "verified_by": None,
            "verified_at": None,
            "uploaded_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=365)  # Documents expire in 1 year
        }
        
        await self.documents_collection.insert_one(document_dict)
        document_dict.pop('_id', None)
        return Document(**document_dict)
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename"""
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    async def get_vendor_documents(self, vendor_id: str) -> List[Document]:
        """Get all documents for a vendor"""
        documents = await self.documents_collection.find({"vendor_id": vendor_id}).to_list(None)
        return [Document(**{**doc, "id": doc.pop("_id", doc.get("id"))}) for doc in documents]
    
    # Verification Workflow
    async def create_verification_request(self, vendor_id: str, requested_by: str) -> VerificationRequest:
        """Create verification request"""
        request_id = str(uuid.uuid4())
        
        # Determine required documents based on country and business type
        required_docs = [
            DocumentType.BUSINESS_REGISTRATION,
            DocumentType.TAX_ID,
            DocumentType.OWNER_ID,
            DocumentType.UTILITY_BILL
        ]
        
        verification_dict = {
            "id": request_id,
            "vendor_id": vendor_id,
            "requested_by": requested_by,
            "verification_type": "full_verification",
            "required_documents": required_docs,
            "submitted_documents": [],
            "status": VerificationStatus.PENDING,
            "priority": 1,
            "assigned_officer": None,
            "notes": None,
            "verification_checklist": {doc.value: False for doc in required_docs},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deadline": datetime.utcnow() + timedelta(days=30),
            "completed_at": None
        }
        
        await self.verifications_collection.insert_one(verification_dict)
        verification_dict.pop('_id', None)
        return VerificationRequest(**verification_dict)
    
    async def get_pending_verifications(self, limit: int = 50) -> List[VerificationRequest]:
        """Get pending verification requests"""
        verifications = await self.verifications_collection.find(
            {"status": {"$in": [VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]}}
        ).limit(limit).to_list(None)
        
        return [VerificationRequest(**{**v, "id": v.pop("_id", v.get("id"))}) for v in verifications]
    
    async def update_verification_status(self, verification_id: str, status: VerificationStatus, 
                                       officer_id: str, notes: Optional[str] = None) -> bool:
        """Update verification status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == VerificationStatus.VERIFIED:
            update_data["completed_at"] = datetime.utcnow()
            
            # Update vendor profile verification status
            verification = await self.verifications_collection.find_one({"id": verification_id})
            if verification:
                await self.vendors_collection.update_one(
                    {"vendor_id": verification["vendor_id"]},
                    {"$set": {
                        "verification_status": VerificationStatus.VERIFIED,
                        "verified_at": datetime.utcnow(),
                        "expires_at": datetime.utcnow() + timedelta(days=365),
                        "verification_level": 3,
                        "trust_score": 75.0
                    }}
                )
                
                # Record trust event
                await self.record_trust_event(
                    verification["vendor_id"],
                    "verification_completed",
                    25.0,
                    "Full verification completed successfully",
                    "verification_system"
                )
        
        if notes:
            update_data["notes"] = notes
        
        result = await self.verifications_collection.update_one(
            {"id": verification_id},
            {"$set": update_data}
        )
        
        # Record verification action
        await self.record_verification_action(
            verification_id,
            officer_id,
            "status_change",
            f"Status changed to {status.value}",
            {"previous_status": "unknown", "new_status": status.value, "notes": notes}
        )
        
        return result.modified_count > 0
    
    async def record_verification_action(self, verification_id: str, officer_id: str,
                                       action_type: str, description: str, details: Dict[str, Any]):
        """Record verification action for audit trail"""
        action_dict = {
            "id": str(uuid.uuid4()),
            "verification_request_id": verification_id,
            "officer_id": officer_id,
            "action_type": action_type,
            "description": description,
            "details": details,
            "created_at": datetime.utcnow()
        }
        
        await self.verification_actions_collection.insert_one(action_dict)
    
    # Service Listings
    async def create_service_listing(self, vendor_id: str, listing_data: ServiceListingCreate) -> ServiceListing:
        """Create service listing"""
        # Verify vendor is verified
        vendor = await self.get_vendor_profile(vendor_id)
        if not vendor or vendor.verification_status != VerificationStatus.VERIFIED:
            raise ValueError("Only verified vendors can create listings")
        
        listing_id = str(uuid.uuid4())
        
        listing_dict = {
            "id": listing_id,
            "vendor_id": vendor_id,
            "title": listing_data.title,
            "description": listing_data.description,
            "category": listing_data.category,
            "subcategory": listing_data.subcategory,
            "price_range": listing_data.price_range,
            "service_type": listing_data.service_type,
            "availability": listing_data.availability,
            "location_served": listing_data.location_served,
            "tags": listing_data.tags,
            "images": listing_data.images,
            "contact_email": listing_data.contact_email,
            "contact_phone": listing_data.contact_phone,
            "is_active": True,
            "views_count": 0,
            "inquiries_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "featured_until": None
        }
        
        await self.listings_collection.insert_one(listing_dict)
        listing_dict.pop('_id', None)
        return ServiceListing(**listing_dict)
    
    async def search_listings(self, query: Optional[str] = None, category: Optional[BusinessCategory] = None,
                            location: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[List[ServiceListing], int]:
        """Search service listings"""
        filter_query = {"is_active": True}
        
        if query:
            filter_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$regex": query, "$options": "i"}}
            ]
        
        if category:
            filter_query["category"] = category
        
        if location:
            filter_query["location_served"] = {"$regex": location, "$options": "i"}
        
        total = await self.listings_collection.count_documents(filter_query)
        
        listings = await self.listings_collection.find(filter_query)\
            .sort("created_at", -1).skip(offset).limit(limit).to_list(None)
        
        return [
            ServiceListing(**{**listing, "id": listing.pop("_id", listing.get("id"))}) 
            for listing in listings
        ], total
    
    # Analytics
    async def initialize_vendor_analytics(self, vendor_id: str):
        """Initialize analytics for vendor"""
        analytics_dict = {
            "vendor_id": vendor_id,
            "profile_views": 0,
            "listing_views": 0,
            "listing_inquiries": 0,
            "qr_scans": 0,
            "verification_checks": 0,
            "trust_score_history": [],
            "monthly_stats": {},
            "last_updated": datetime.utcnow()
        }
        
        await self.analytics_collection.insert_one(analytics_dict)
    
    async def update_analytics(self, vendor_id: str, metric: str, increment: int = 1):
        """Update vendor analytics"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        await self.analytics_collection.update_one(
            {"vendor_id": vendor_id},
            {
                "$inc": {metric: increment},
                "$set": {"last_updated": datetime.utcnow()},
                "$inc": {f"monthly_stats.{current_month}.{metric}": increment}
            }
        )
    
    # Trust and Security
    async def record_trust_event(self, vendor_id: str, event_type: str, impact_score: float,
                               description: str, source: str, metadata: Dict[str, Any] = None):
        """Record trust event"""
        event_dict = {
            "id": str(uuid.uuid4()),
            "vendor_id": vendor_id,
            "event_type": event_type,
            "impact_score": impact_score,
            "description": description,
            "source": source,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        
        await self.trust_events_collection.insert_one(event_dict)
        
        # Update vendor trust score
        vendor = await self.get_vendor_profile(vendor_id)
        if vendor:
            new_trust_score = max(0, min(100, vendor.trust_score + impact_score))
            await self.update_vendor_profile(vendor_id, {"trust_score": new_trust_score})
    
    async def report_fraud(self, reporter_id: Optional[str], vendor_id: str, 
                         report_type: str, description: str, evidence_files: List[str] = None) -> FraudReport:
        """Report fraud"""
        report_id = str(uuid.uuid4())
        
        report_dict = {
            "id": report_id,
            "reporter_id": reporter_id,
            "reported_vendor_id": vendor_id,
            "report_type": report_type,
            "description": description,
            "evidence_files": evidence_files or [],
            "status": "open",
            "priority": 3,  # Medium priority by default
            "assigned_investigator": None,
            "resolution_notes": None,
            "created_at": datetime.utcnow(),
            "resolved_at": None
        }
        
        await self.fraud_reports_collection.insert_one(report_dict)
        
        # Record negative trust event
        await self.record_trust_event(
            vendor_id,
            "fraud_reported",
            -10.0,
            f"Fraud report filed: {report_type}",
            "fraud_reporting_system",
            {"report_id": report_id}
        )
        
        report_dict.pop('_id', None)
        return FraudReport(**report_dict)
    
    # Public Verification
    async def verify_vendor_public(self, vendor_id: str) -> Optional[PublicVendorVerification]:
        """Public vendor verification (for QR code scanning)"""
        vendor = await self.get_vendor_profile(vendor_id)
        if not vendor:
            return None
        
        # Update scan analytics
        await self.update_analytics(vendor_id, "qr_scans")
        await self.update_analytics(vendor_id, "verification_checks")
        
        return PublicVendorVerification(
            vendor_id=vendor.vendor_id,
            business_name=vendor.business_name,
            verification_status=vendor.verification_status,
            trust_score=vendor.trust_score,
            verification_level=vendor.verification_level,
            verified_since=vendor.verified_at,
            categories=[vendor.category],
            location=vendor.business_address,
            qr_verification_url=f"https://vendor-id.com/verify/{vendor.vendor_id}"
        )
    
    # Dashboard Data
    async def get_vendor_dashboard_data(self, vendor_id: str) -> Optional[VendorDashboardData]:
        """Get complete vendor dashboard data"""
        vendor = await self.get_vendor_profile(vendor_id)
        if not vendor:
            return None
        
        # Get analytics
        analytics_doc = await self.analytics_collection.find_one({"vendor_id": vendor_id})
        analytics = VendorAnalytics(**analytics_doc) if analytics_doc else VendorAnalytics(vendor_id=vendor_id)
        
        # Get active listings
        listings, _ = await self.search_listings(category=None, limit=10)
        active_listings = [l for l in listings if l.vendor_id == vendor_id]
        
        # Get verification status
        verification_doc = await self.verifications_collection.find_one(
            {"vendor_id": vendor_id}, sort=[("created_at", -1)]
        )
        verification_status = VerificationRequest(**verification_doc) if verification_doc else None
        
        # Get trust events
        trust_events_docs = await self.trust_events_collection.find(
            {"vendor_id": vendor_id}
        ).sort("created_at", -1).limit(10).to_list(None)
        trust_events = [TrustEvent(**event) for event in trust_events_docs]
        
        # Get integrations
        integrations_docs = await self.integrations_collection.find(
            {"vendor_id": vendor_id}
        ).to_list(None)
        integrations = [MarketplaceIntegration(**integration) for integration in integrations_docs]
        
        return VendorDashboardData(
            profile=vendor,
            analytics=analytics,
            active_listings=active_listings,
            verification_status=verification_status,
            trust_events=trust_events,
            integrations=integrations
        )
    
    # System Statistics
    async def get_ecosystem_stats(self) -> VendorEcosystemStats:
        """Get system-wide statistics"""
        total_vendors = await self.vendors_collection.count_documents({})
        verified_vendors = await self.vendors_collection.count_documents(
            {"verification_status": VerificationStatus.VERIFIED}
        )
        pending_verification = await self.vendors_collection.count_documents(
            {"verification_status": VerificationStatus.PENDING}
        )
        active_listings = await self.listings_collection.count_documents({"is_active": True})
        total_documents = await self.documents_collection.count_documents({})
        verification_requests_pending = await self.verifications_collection.count_documents(
            {"status": {"$in": [VerificationStatus.PENDING, VerificationStatus.UNDER_REVIEW]}}
        )
        fraud_reports_open = await self.fraud_reports_collection.count_documents({"status": "open"})
        
        # Calculate average trust score
        pipeline = [{"$group": {"_id": None, "avg_trust_score": {"$avg": "$trust_score"}}}]
        trust_score_result = await self.vendors_collection.aggregate(pipeline).to_list(1)
        avg_trust_score = trust_score_result[0]["avg_trust_score"] if trust_score_result else 0.0
        
        # Count unique countries
        countries_pipeline = [{"$group": {"_id": {"$substr": ["$vendor_id", 4, 2]}}}]
        countries_result = await self.vendors_collection.aggregate(countries_pipeline).to_list(None)
        countries_represented = len(countries_result)
        
        # Count categories
        categories_pipeline = [{"$group": {"_id": "$category"}}]
        categories_result = await self.vendors_collection.aggregate(categories_pipeline).to_list(None)
        categories_covered = len(categories_result)
        
        return VendorEcosystemStats(
            total_vendors=total_vendors,
            verified_vendors=verified_vendors,
            pending_verification=pending_verification,
            active_listings=active_listings,
            total_documents=total_documents,
            trust_score_average=round(avg_trust_score, 2),
            countries_represented=countries_represented,
            categories_covered=categories_covered,
            verification_requests_pending=verification_requests_pending,
            fraud_reports_open=fraud_reports_open
        )