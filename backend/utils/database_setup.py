from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Database setup utilities for creating indexes and collections"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def create_indexes(self):
        """Create necessary database indexes for performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("id", unique=True)
            await self.db.users.create_index("role")
            await self.db.users.create_index("created_at")
            
            # User security collection indexes
            await self.db.user_security.create_index("user_id", unique=True)
            await self.db.user_security.create_index("email_verification_token")
            await self.db.user_security.create_index("password_reset_token")
            await self.db.user_security.create_index("account_locked_until")
            
            # Vendor profiles collection indexes
            await self.db.vendor_profiles.create_index("vendor_id", unique=True)
            await self.db.vendor_profiles.create_index("user_id", unique=True)
            await self.db.vendor_profiles.create_index("verification_status")
            await self.db.vendor_profiles.create_index("category")
            await self.db.vendor_profiles.create_index("country")
            await self.db.vendor_profiles.create_index("trust_score")
            await self.db.vendor_profiles.create_index("created_at")
            
            # Vendor documents collection indexes
            await self.db.vendor_documents.create_index("document_id", unique=True)
            await self.db.vendor_documents.create_index("vendor_id")
            await self.db.vendor_documents.create_index("document_type")
            await self.db.vendor_documents.create_index("file_hash")
            await self.db.vendor_documents.create_index("verification_status")
            await self.db.vendor_documents.create_index("upload_timestamp")
            
            # Service listings collection indexes
            await self.db.service_listings.create_index("listing_id", unique=True)
            await self.db.service_listings.create_index("vendor_id")
            await self.db.service_listings.create_index("category")
            await self.db.service_listings.create_index("status")
            await self.db.service_listings.create_index("created_at")
            
            # Verification requests collection indexes
            await self.db.verification_requests.create_index("verification_id", unique=True)
            await self.db.verification_requests.create_index("vendor_id")
            await self.db.verification_requests.create_index("status")
            await self.db.verification_requests.create_index("created_at")
            
            # Fraud reports collection indexes
            await self.db.fraud_reports.create_index("report_id", unique=True)
            await self.db.fraud_reports.create_index("reported_vendor_id")
            await self.db.fraud_reports.create_index("reporter_id")
            await self.db.fraud_reports.create_index("status")
            await self.db.fraud_reports.create_index("created_at")
            
            # Security events collection indexes
            await self.db.security_events.create_index("user_id")
            await self.db.security_events.create_index("event_type")
            await self.db.security_events.create_index("created_at")
            
            # OCR processing results collection indexes
            await self.db.ocr_processing_results.create_index("processing_id", unique=True)
            await self.db.ocr_processing_results.create_index("vendor_id")
            await self.db.ocr_processing_results.create_index("document_id")
            await self.db.ocr_processing_results.create_index("status")
            await self.db.ocr_processing_results.create_index("processing_timestamp")
            
            # OCR validation results collection indexes
            await self.db.ocr_validation_results.create_index("validation_id", unique=True)
            await self.db.ocr_validation_results.create_index("vendor_id")
            await self.db.ocr_validation_results.create_index("document_id")
            await self.db.ocr_validation_results.create_index("validation_timestamp")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise
    
    async def create_collections_if_not_exist(self):
        """Create collections if they don't exist"""
        collections = [
            "users",
            "user_security", 
            "vendor_profiles",
            "vendor_documents",
            "service_listings",
            "verification_requests",
            "fraud_reports",
            "security_events",
            "trust_events",
            "marketplace_integrations",
            "ocr_processing_results",
            "ocr_validation_results",
            "verification_queue"
        ]
        
        existing_collections = await self.db.list_collection_names()
        
        for collection_name in collections:
            if collection_name not in existing_collections:
                await self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
    
    async def setup_database(self):
        """Complete database setup"""
        await self.create_collections_if_not_exist()
        await self.create_indexes()
        logger.info("Database setup completed successfully")