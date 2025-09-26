from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Response, Depends, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import Optional, List
from io import BytesIO
import csv
import json
import jwt
from datetime import datetime

# Import models and services
from models.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorsResponse
from models.vendor_ecosystem import *
from models.auth_models import *
from services.vendor_service import VendorService
from services.vendor_ecosystem_service import VendorEcosystemService
from services.auth_enhancement_service import AuthEnhancementService
from services.qr_barcode_service import QRBarcodeService
from services.upload_service import UploadService
from services.template_service import TemplateService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Vendor Verification and Trust Ecosystem API", version="2.0.0")

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/api/auth")
vendor_router = APIRouter(prefix="/api/vendors")
admin_router = APIRouter(prefix="/api/admin")
public_router = APIRouter(prefix="/api/public")

# Initialize services
vendor_service = VendorService(db)
ecosystem_service = VendorEcosystemService(db)
auth_service = AuthEnhancementService(db)
qr_barcode_service = QRBarcodeService()
upload_service = UploadService()
template_service = TemplateService()

# Security
security = HTTPBearer()
jwt_secret = os.getenv("JWT_SECRET", "fallback-secret-key")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Role-based access dependency
def require_role(required_role: UserRole):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role != required_role.value and user_role != UserRole.SYSTEM_ADMIN.value:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Health check
@api_router.get("/")
async def root():
    return {
        "message": "Vendor Verification and Trust Ecosystem API", 
        "version": "2.0.0",
        "status": "active",
        "features": [
            "vendor_verification",
            "document_management", 
            "service_listings",
            "trust_scoring",
            "fraud_detection",
            "marketplace_integration",
            "public_verification"
        ]
    }

# Authentication Endpoints
@auth_router.post("/register")
async def register_user(user_data: UserCreate):
    """Register new user"""
    try:
        user = await ecosystem_service.create_user(user_data)
        token = ecosystem_service.generate_jwt_token(user)
        return {
            "user": user,
            "token": token,
            "message": "User registered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@auth_router.post("/login")
async def login_user(email: str, password: str):
    """User login"""
    user = await ecosystem_service.authenticate_user(email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = ecosystem_service.generate_jwt_token(user)
    return {
        "user": user,
        "token": token,
        "message": "Login successful"
    }

# Vendor Profile Endpoints
@vendor_router.post("/profile")
async def create_vendor_profile(profile_data: VendorProfileCreate, current_user: dict = Depends(get_current_user)):
    """Create vendor profile"""
    try:
        profile = await ecosystem_service.create_vendor_profile(current_user["user_id"], profile_data)
        return {"profile": profile, "message": "Vendor profile created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Profile creation failed")

@vendor_router.get("/profile/{vendor_id}")
async def get_vendor_profile(vendor_id: str):
    """Get vendor profile (public)"""
    profile = await ecosystem_service.get_vendor_profile(vendor_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"profile": profile}

@vendor_router.get("/dashboard")
async def get_vendor_dashboard(current_user: dict = Depends(get_current_user)):
    """Get vendor dashboard data"""
    # Get vendor profile for current user
    vendor_doc = await db.vendor_profiles.find_one({"user_id": current_user["user_id"]})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    dashboard_data = await ecosystem_service.get_vendor_dashboard_data(vendor_doc["vendor_id"])
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Dashboard data not found")
    
    return {"dashboard": dashboard_data}

# Document Management Endpoints
@vendor_router.post("/documents")
async def upload_document(document_data: DocumentCreate, current_user: dict = Depends(get_current_user)):
    """Upload vendor document"""
    # Get vendor ID for current user
    vendor_doc = await db.vendor_profiles.find_one({"user_id": current_user["user_id"]})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    try:
        document = await ecosystem_service.upload_document(vendor_doc["vendor_id"], document_data)
        return {"document": document, "message": "Document uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Document upload failed")

@vendor_router.get("/documents")
async def get_vendor_documents(current_user: dict = Depends(get_current_user)):
    """Get vendor documents"""
    vendor_doc = await db.vendor_profiles.find_one({"user_id": current_user["user_id"]})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    documents = await ecosystem_service.get_vendor_documents(vendor_doc["vendor_id"])
    return {"documents": documents}

# Service Listings Endpoints
@vendor_router.post("/listings")
async def create_service_listing(listing_data: ServiceListingCreate, current_user: dict = Depends(get_current_user)):
    """Create service listing"""
    vendor_doc = await db.vendor_profiles.find_one({"user_id": current_user["user_id"]})
    if not vendor_doc:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    try:
        listing = await ecosystem_service.create_service_listing(vendor_doc["vendor_id"], listing_data)
        return {"listing": listing, "message": "Service listing created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Listing creation failed")

@vendor_router.get("/listings/search")
async def search_service_listings(
    query: Optional[str] = None,
    category: Optional[BusinessCategory] = None,
    location: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search service listings"""
    listings, total = await ecosystem_service.search_listings(query, category, location, limit, offset)
    return {"listings": listings, "total": total}

# Verification Endpoints (Admin)
@admin_router.get("/verifications/pending")
async def get_pending_verifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Get pending verification requests"""
    verifications = await ecosystem_service.get_pending_verifications(limit)
    return {"verifications": verifications}

@admin_router.put("/verifications/{verification_id}/status")
async def update_verification_status(
    verification_id: str,
    status: VerificationStatus,
    notes: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Update verification status"""
    success = await ecosystem_service.update_verification_status(
        verification_id, status, current_user["user_id"], notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Verification request not found")
    
    return {"message": f"Verification status updated to {status.value}"}

# Fraud Reporting Endpoints
@api_router.post("/fraud/report")
async def report_fraud(
    reported_vendor_id: str,
    report_type: str,
    description: str,
    evidence_files: List[str] = [],
    current_user: dict = Depends(get_current_user)
):
    """Report fraud"""
    try:
        report = await ecosystem_service.report_fraud(
            current_user["user_id"], reported_vendor_id, report_type, description, evidence_files
        )
        return {"report": report, "message": "Fraud report submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Fraud report submission failed")

# Public Verification Endpoints
@public_router.get("/verify/{vendor_id}")
async def verify_vendor_public(vendor_id: str):
    """Public vendor verification (QR code endpoint)"""
    verification = await ecosystem_service.verify_vendor_public(vendor_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Vendor not found or not verified")
    
    return {"verification": verification}

@public_router.get("/search")
async def public_vendor_search(
    query: Optional[str] = None,
    category: Optional[BusinessCategory] = None,
    country: Optional[CountryCode] = None,
    verified_only: bool = True,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Public vendor search"""
    # Build search filter
    search_filter = {}
    if verified_only:
        search_filter["verification_status"] = VerificationStatus.VERIFIED
    
    if category:
        search_filter["category"] = category
    
    if country:
        search_filter["vendor_id"] = {"$regex": f"VID-{country.value}-"}
    
    if query:
        search_filter["$or"] = [
            {"business_name": {"$regex": query, "$options": "i"}},
            {"business_description": {"$regex": query, "$options": "i"}}
        ]
    
    # Get vendors
    total = await db.vendor_profiles.count_documents(search_filter)
    vendors_docs = await db.vendor_profiles.find(search_filter)\
        .sort("trust_score", -1).skip(offset).limit(limit).to_list(None)
    
    vendors = []
    for doc in vendors_docs:
        doc.pop('_id', None)
        vendor = VendorProfile(**doc)
        vendors.append({
            "vendor_id": vendor.vendor_id,
            "business_name": vendor.business_name,
            "category": vendor.category,
            "trust_score": vendor.trust_score,
            "verification_level": vendor.verification_level,
            "location": vendor.business_address,
            "verified_since": vendor.verified_at
        })
    
    return {"vendors": vendors, "total": total}

# System Statistics
@admin_router.get("/stats")
async def get_ecosystem_stats(current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))):
    """Get ecosystem statistics"""
    stats = await ecosystem_service.get_ecosystem_stats()
    return {"stats": stats}

# Legacy endpoints for backward compatibility
@api_router.get("/vendors", response_model=VendorsResponse)
async def get_legacy_vendors(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    template: Optional[str] = Query(None),
    expired: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Legacy vendor endpoint for backward compatibility"""
    try:
        vendors, total = await vendor_service.get_vendors(search, status, template, expired, limit, offset)
        return VendorsResponse(vendors=vendors, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/vendors", response_model=VendorResponse)
async def create_legacy_vendor(vendor_data: VendorCreate):
    """Legacy vendor creation for backward compatibility"""
    try:
        vendor = await vendor_service.create_vendor(vendor_data)
        return VendorResponse(vendor=vendor, message="Vendor created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Include routers
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(vendor_router)
app.include_router(admin_router)
app.include_router(public_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()