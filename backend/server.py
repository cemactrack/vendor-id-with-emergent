from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Query, Response, Depends, status, Header
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
from datetime import datetime, timezone, timedelta

# Import models and services
from models.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorsResponse
from models.vendor_ecosystem import *
from models.auth_models import *
from models.escrow_models import *
from models.biometric_models import *
from models.consent_models import *
from models.security_models import *
from models.fraud_detection_models import *
from services.vendor_service import VendorService
from services.enhanced_vendor_ecosystem_service import VendorEcosystemService
from services.auth_enhancement_service import AuthEnhancementService
from services.document_verification_service import DocumentVerificationService
from services.vendor_id_service import VendorIDService
from services.qr_barcode_service import QRBarcodeService
from services.upload_service import UploadService
from services.template_service import TemplateService
from services.ocr_service import DocumentOCRService
from services.escrow_service import EscrowService
from services.rating_service import RatingService
from services.biometric_service import BiometricService
from services.consent_service import ConsentService
from services.security_service import SecurityService
from services.fraud_detection_service import FraudDetectionService
from utils.database_setup import DatabaseSetup

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
escrow_router = APIRouter(prefix="/api/escrow")
ratings_router = APIRouter(prefix="/api/ratings")
biometric_router = APIRouter(prefix="/api/biometric")
security_router = APIRouter(prefix="/api/security")
public_router = APIRouter(prefix="/api/public")

# Initialize services
vendor_service = VendorService(db)
ecosystem_service = VendorEcosystemService(db)
auth_service = AuthEnhancementService(db)
document_service = DocumentVerificationService(db)
vendor_id_service = VendorIDService(db)
qr_barcode_service = QRBarcodeService()
upload_service = UploadService()
template_service = TemplateService()
ocr_service = DocumentOCRService(mongo_url)
escrow_service = EscrowService(db)
rating_service = RatingService(db)
biometric_service = BiometricService(db)
consent_service = ConsentService(db)
security_service = SecurityService(db)
fraud_detection_service = FraudDetectionService(db)
db_setup = DatabaseSetup(db)

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
@auth_router.post("/login")
async def login_user(email: str, password: str, totp_token: Optional[str] = None, backup_code: Optional[str] = None):
    """Enhanced user login with 2FA support"""
    # Check account lockout
    is_locked, locked_until = await auth_service.is_account_locked(email)
    if is_locked:
        raise HTTPException(
            status_code=423, 
            detail=f"Account locked due to multiple failed attempts. Try again after {locked_until}"
        )
    
    # Authenticate user
    user = await ecosystem_service.authenticate_user(email, password)
    if not user:
        # Record failed login attempt
        await auth_service.record_login_attempt(email, False)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if 2FA is enabled
    security_info = await auth_service.get_user_security_info(user.id)
    if security_info and security_info.get("two_factor_enabled"):
        if not totp_token and not backup_code:
            # Record successful password authentication but require 2FA
            return {
                "requires_2fa": True,
                "message": "Please provide 2FA code"
            }
        
        # Verify 2FA
        success, error = await auth_service.verify_two_factor(user.id, totp_token, backup_code)
        if not success:
            await auth_service.record_login_attempt(email, False)
            raise HTTPException(status_code=401, detail=error or "Invalid 2FA code")
    
    # Record successful login
    await auth_service.record_login_attempt(email, True)
    
    token = ecosystem_service.generate_jwt_token(user)
    return {
        "user": user,
        "token": token,
        "message": "Login successful"
    }

@auth_router.post("/register")
async def register_user(user_data: UserCreate):
    """Enhanced user registration with email verification"""
    try:
        user = await ecosystem_service.create_user(user_data)
        
        # Send email verification
        email_sent = await auth_service.send_email_verification(
            user.id, 
            user.email, 
            user.full_name
        )
        
        if not email_sent:
            logger.warning(f"Failed to send verification email to {user.email}")
        
        token = ecosystem_service.generate_jwt_token(user)
        return {
            "user": user,
            "token": token,
            "message": "User registered successfully. Please check your email for verification.",
            "email_verification_sent": email_sent
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

# Enhanced Authentication Endpoints
@auth_router.post("/verify-email")
async def verify_email(request: EmailVerificationVerify):
    """Verify user email"""
    success, message = await auth_service.verify_email(request.token)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@auth_router.post("/resend-verification")
async def resend_email_verification(current_user: dict = Depends(get_current_user)):
    """Resend email verification"""
    user = await ecosystem_service.users_collection.find_one({"id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    success = await auth_service.send_email_verification(
        user["id"], 
        user["email"], 
        user["full_name"]
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    return {"message": "Verification email sent"}

@auth_router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Request password reset"""
    success = await auth_service.request_password_reset(request.email)
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@auth_router.post("/reset-password")
async def reset_password(request: PasswordReset):
    """Reset password using token"""
    success, message = await auth_service.reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

# Two-Factor Authentication Endpoints
@auth_router.post("/2fa/setup")
async def setup_two_factor(request: TwoFactorSetup, current_user: dict = Depends(get_current_user)):
    """Setup 2FA for user"""
    success, setup_data, error = await auth_service.setup_two_factor(
        current_user["user_id"], 
        request.password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "message": "2FA setup initiated. Scan the QR code with your authenticator app.",
        "setup_data": setup_data
    }

@auth_router.post("/2fa/enable")
async def enable_two_factor(request: TwoFactorVerify, current_user: dict = Depends(get_current_user)):
    """Enable 2FA after verification"""
    success, message = await auth_service.enable_two_factor(current_user["user_id"], request.token)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@auth_router.post("/2fa/disable")
async def disable_two_factor(request: TwoFactorDisable, current_user: dict = Depends(get_current_user)):
    """Disable 2FA"""
    success, message = await auth_service.disable_two_factor(
        current_user["user_id"], 
        request.password, 
        request.token
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

@auth_router.post("/2fa/verify")
async def verify_two_factor_code(request: TwoFactorVerify, current_user: dict = Depends(get_current_user)):
    """Verify 2FA code"""
    success, message = await auth_service.verify_two_factor(current_user["user_id"], request.token)
    
    if not success:
        raise HTTPException(status_code=400, detail=message or "Invalid 2FA code")
    
    return {"message": "2FA code verified successfully"}

# Security & Account Management Endpoints
@auth_router.get("/security/info")
async def get_security_info(current_user: dict = Depends(get_current_user)):
    """Get user security information"""
    security_info = await auth_service.get_user_security_info(current_user["user_id"])
    return {"security": security_info}

@auth_router.get("/security/events")
async def get_security_events(current_user: dict = Depends(get_current_user), limit: int = 20):
    """Get recent security events"""
    events = await auth_service.get_security_events(current_user["user_id"], limit)
    return {"events": events}

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
    try:
        logger.info(f"Dashboard request for user: {current_user}")
        
        # Try to get dashboard data
        dashboard_data = await ecosystem_service.get_vendor_dashboard(current_user["user_id"])
        
        return {
            "success": True,
            "dashboard": dashboard_data.get("dashboard", {}),
            "profile": dashboard_data.get("profile", {}),
            "analytics": dashboard_data.get("analytics", {}),
            "active_listings": dashboard_data.get("active_listings", []),
            "verification_status": dashboard_data.get("verification_status", {}),
            "trust_events": dashboard_data.get("trust_events", []),
            "integrations": dashboard_data.get("integrations", []),
            "documents": dashboard_data.get("documents", []),
            "security_events": dashboard_data.get("security_events", [])
        }
    except ValueError as ve:
        logger.error(f"Dashboard data error for user {current_user.get('user_id')}: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Dashboard fetch failed for user {current_user.get('user_id')}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")

# Document Management Endpoints
@vendor_router.post("/documents/upload")
async def upload_vendor_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload vendor verification document"""
    try:
        # Read file data
        file_data = await file.read()
        
        # Save document
        success, document_id, message = await document_service.save_uploaded_document(
            current_user["user_id"],
            file_data,
            file.filename,
            document_type
        )
        
        if success:
            return {
                "document_id": document_id,
                "message": message
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@vendor_router.get("/documents")
async def get_vendor_documents(current_user: dict = Depends(get_current_user)):
    """Get all documents for current vendor"""
    try:
        documents = await document_service.get_vendor_documents(current_user["user_id"])
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch documents")

@vendor_router.delete("/documents/{document_id}")
async def delete_vendor_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a vendor document"""
    try:
        # Note: In production, you might want to add ownership verification
        # For now, we'll implement a basic deletion
        result = await document_service.documents_collection.delete_one({
            "document_id": document_id,
            "vendor_id": current_user["user_id"]
        })
        
        if result.deleted_count > 0:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document")

@vendor_router.get("/documents/summary")
async def get_vendor_verification_summary(current_user: dict = Depends(get_current_user)):
    """Get verification summary for current vendor"""
    try:
        summary = await document_service.get_vendor_verification_summary(current_user["user_id"])
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch verification summary")

# Admin Document Review Endpoints
@admin_router.get("/verification-queue")
async def get_verification_queue(
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get documents pending verification"""
    try:
        # Check admin permissions
        if current_user.get("role") not in ["verification_officer", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        queue = await document_service.get_verification_queue(limit)
        return {"queue": queue}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch verification queue")

@admin_router.get("/documents/{document_id}/review")
async def get_document_for_review(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document details for review"""
    try:
        # Check admin permissions
        if current_user.get("role") not in ["verification_officer", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get document details
        document = await document_service.documents_collection.find_one({
            "document_id": document_id
        })
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get vendor profile
        vendor_profile = await ecosystem_service.vendors_collection.find_one({
            "vendor_id": document["vendor_id"]
        })
        
        # Remove sensitive data
        document.pop("_id", None)
        document.pop("file_path", None)
        document.pop("file_hash", None)
        
        if vendor_profile:
            vendor_profile.pop("_id", None)
        
        return {
            "document": document,
            "vendor": vendor_profile
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get document for review")

@admin_router.post("/documents/{document_id}/approve")
async def approve_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve a document"""
    try:
        # Check admin permissions
        if current_user.get("role") not in ["verification_officer", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        success, message = await document_service.approve_document(
            document_id, 
            current_user["user_id"], 
            ""
        )
        
        if success:
            # Check if all required documents are approved for this vendor
            document = await document_service.documents_collection.find_one({
                "document_id": document_id
            })
            
            if document:
                summary = await document_service.get_vendor_verification_summary(
                    document["vendor_id"]
                )
                
                # If verification is complete, generate Vendor ID
                if summary.get("verification_complete"):
                    # Get vendor profile for country info (document["vendor_id"] is actually user_id)
                    vendor_profile = await ecosystem_service.vendors_collection.find_one({
                        "user_id": document["vendor_id"]
                    })
                    
                    if vendor_profile:
                        country = vendor_profile.get("country", "US")
                        # Use the actual vendor_id from the profile, not the user_id
                        success_id, vendor_id_number, msg = await vendor_id_service.generate_vendor_id(
                            vendor_profile["vendor_id"], 
                            country
                        )
                        
                        if success_id:
                            message += f" Vendor ID {vendor_id_number} has been generated."
            
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Failed to approve document: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve document")

@admin_router.post("/documents/{document_id}/reject")
async def reject_document(
    document_id: str,
    reason: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Reject a document"""
    try:
        # Check admin permissions
        if current_user.get("role") not in ["verification_officer", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        if not reason.strip():
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        
        success, message = await document_service.reject_document(
            document_id, 
            current_user["user_id"], 
            reason
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Failed to reject document: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject document")

# Vendor ID Management Endpoints
@vendor_router.get("/vendor-id")
async def get_vendor_id_info(current_user: dict = Depends(get_current_user)):
    """Get vendor ID information for current user"""
    try:
        # Get vendor profile
        vendor_profile = await ecosystem_service.vendors_collection.find_one({
            "user_id": current_user["user_id"]
        })
        
        if not vendor_profile:
            raise HTTPException(status_code=404, detail="Vendor profile not found")
        
        if vendor_profile.get("vendor_id_number"):
            vendor_id_info = await vendor_id_service.get_vendor_id_info(
                vendor_profile["vendor_id_number"]
            )
            return {"vendor_id": vendor_id_info}
        else:
            return {"vendor_id": None, "message": "Vendor ID not yet assigned"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get vendor ID information")

@vendor_router.post("/vendor-id/request-physical-card")
async def request_physical_card(
    shipping_address: dict,
    current_user: dict = Depends(get_current_user)
):
    """Request physical vendor ID card"""
    try:
        # Get vendor profile
        vendor_profile = await ecosystem_service.vendors_collection.find_one({
            "user_id": current_user["user_id"]
        })
        
        if not vendor_profile or not vendor_profile.get("vendor_id_number"):
            raise HTTPException(status_code=400, detail="Vendor ID not assigned yet")
        
        success, message = await vendor_id_service.request_physical_card(
            vendor_profile["vendor_id_number"],
            shipping_address
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to request physical card")

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

# ===== OCR ENDPOINTS =====

@vendor_router.post("/documents/{document_id}/ocr/process")
async def process_document_ocr(
    document_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Process document with OCR for text extraction"""
    try:
        vendor_id = current_user.get("vendor_id", current_user["user_id"])
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name is required")
        
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['pdf', 'png', 'jpg', 'jpeg']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Supported: PDF, PNG, JPG, JPEG"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
        
        # Process with OCR
        result = await ocr_service.process_document_for_vendor(
            vendor_id=vendor_id,
            document_id=document_id,
            file_content=file_content,
            file_type=file_ext,
            document_type=document_type
        )
        
        return {
            "message": "OCR processing completed successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@vendor_router.get("/documents/{document_id}/ocr/results")
async def get_document_ocr_results(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get OCR results for a document"""
    try:
        vendor_id = current_user.get("vendor_id", current_user["user_id"])
        
        results = await ocr_service.get_document_ocr_results(vendor_id, document_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="OCR results not found")
        
        return {"ocr_results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving OCR results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve OCR results")

@vendor_router.post("/documents/{document_id}/ocr/validate")
async def validate_document_ocr(
    document_id: str,
    validation_request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Validate OCR extracted data against expected values"""
    try:
        vendor_id = current_user.get("vendor_id", current_user["user_id"])
        
        expected_fields = validation_request.get("expected_fields", {})
        
        if not expected_fields:
            raise HTTPException(status_code=400, detail="Expected fields are required for validation")
        
        validation_results = await ocr_service.validate_extracted_data(
            vendor_id=vendor_id,
            document_id=document_id,
            expected_fields=expected_fields
        )
        
        return {
            "message": "Document validation completed",
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"OCR validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@vendor_router.get("/ocr/summary")
async def get_vendor_ocr_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get OCR processing summary for current vendor"""
    try:
        vendor_id = current_user.get("vendor_id", current_user["user_id"])
        
        summary = await ocr_service.get_vendor_ocr_summary(vendor_id)
        
        return {"ocr_summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating OCR summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate OCR summary")

@admin_router.get("/ocr/results/{processing_id}")
async def admin_get_ocr_results(
    processing_id: str,
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Admin endpoint to get OCR results by processing ID"""
    try:
        results = await ocr_service.get_ocr_results(processing_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="OCR results not found")
        
        return {"ocr_results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin OCR results error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve OCR results")

# ===== ESCROW ENDPOINTS =====

# Order Management
@escrow_router.post("/orders/create")
async def create_order(
    order_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new order with escrow"""
    try:
        from models.escrow_models import OrderCreate
        
        # Parse order data
        order_create = OrderCreate(**order_data)
        
        # Create order
        success, result, error = await escrow_service.create_order(current_user["user_id"], order_create)
        
        if success:
            return {
                "message": "Order created successfully",
                "order": result["order"],
                "escrow": result["escrow"],
                "payment_instructions": result["payment_instructions"]
            }
        else:
            raise HTTPException(status_code=400, detail=error)
            
    except Exception as e:
        logger.error(f"Order creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create order")

@escrow_router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get order details"""
    try:
        order = await escrow_service.get_order(order_id, current_user["user_id"])
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"order": order}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve order")

@escrow_router.get("/orders")
async def get_user_orders(
    role: str = "customer",
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's orders"""
    try:
        orders = await escrow_service.get_user_orders(current_user["user_id"], role, limit)
        
        return {
            "orders": orders,
            "total": len(orders)
        }
        
    except Exception as e:
        logger.error(f"Get user orders error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve orders")

# Payment Management
@escrow_router.post("/payments/submit-proof")
async def submit_payment_proof(
    payment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Submit payment proof"""
    try:
        from models.escrow_models import PaymentProofSubmission
        
        proof_data = PaymentProofSubmission(**payment_data)
        success, message = await escrow_service.submit_payment_proof(current_user["user_id"], proof_data)
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Submit payment proof error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit payment proof")

@escrow_router.post("/payments/{instruction_id}/confirm")
async def confirm_payment(
    instruction_id: str,
    confirmation_data: dict,
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Admin confirms payment"""
    try:
        confirmed = confirmation_data.get("confirmed", False)
        notes = confirmation_data.get("notes", "")
        
        success, message = await escrow_service.confirm_payment(
            current_user["user_id"], instruction_id, confirmed, notes
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Confirm payment error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm payment")

# Order Fulfillment
@escrow_router.post("/orders/{order_id}/delivered")
async def mark_order_delivered(
    order_id: str,
    delivery_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Vendor marks order as delivered"""
    try:
        delivery_notes = delivery_data.get("delivery_notes", "")
        
        success, message = await escrow_service.mark_order_delivered(
            current_user.get("vendor_id", current_user["user_id"]), order_id, delivery_notes
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Mark delivered error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark order as delivered")

@escrow_router.post("/orders/{order_id}/confirm-receipt")
async def confirm_order_receipt(
    order_id: str,
    receipt_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Customer confirms order receipt"""
    try:
        satisfaction_rating = receipt_data.get("satisfaction_rating", 5)
        
        success, message = await escrow_service.confirm_order_receipt(
            current_user["user_id"], order_id, satisfaction_rating
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Confirm receipt error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to confirm order receipt")

# Extension Requests
@escrow_router.post("/orders/{order_id}/request-extension")
async def request_extension(
    order_id: str,
    extension_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Request escrow extension"""
    try:
        from models.escrow_models import EscrowExtensionRequest
        
        # Determine requester type
        requester_type = "vendor" if current_user.get("vendor_id") else "customer"
        
        extension_request = EscrowExtensionRequest(
            order_id=order_id,
            requested_by=current_user["user_id"],
            requester_type=requester_type,
            **extension_data
        )
        
        success, message = await escrow_service.request_extension(
            current_user["user_id"], order_id, extension_request
        )
        
        if success:
            return {"message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        logger.error(f"Request extension error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to request extension")

# Dispute Management
@escrow_router.post("/disputes/create")
async def create_dispute(
    dispute_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a dispute"""
    try:
        from models.escrow_models import DisputeCreate
        
        dispute_create = DisputeCreate(**dispute_data)
        
        success, result, error = await escrow_service.create_dispute(
            current_user["user_id"], dispute_create
        )
        
        if success:
            return {
                "message": "Dispute created successfully",
                "dispute": result
            }
        else:
            raise HTTPException(status_code=400, detail=error)
            
    except Exception as e:
        logger.error(f"Create dispute error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create dispute")

# Admin Endpoints
@escrow_router.get("/admin/pending-payments")
async def get_pending_payments(
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Get pending payment confirmations"""
    try:
        payments = await escrow_service.get_pending_payment_confirmations()
        
        return {
            "pending_payments": payments,
            "total": len(payments)
        }
        
    except Exception as e:
        logger.error(f"Get pending payments error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending payments")

@escrow_router.get("/admin/dashboard")
async def get_escrow_dashboard(
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Get escrow dashboard statistics"""
    try:
        # This would be implemented in the escrow service
        stats = {
            "total_orders": 0,
            "pending_payments": 0,
            "active_escrows": 0,
            "open_disputes": 0,
            "funds_held": 0.0
        }
        
        return {"dashboard": stats}
        
    except Exception as e:
        logger.error(f"Get escrow dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

# ===== RATING & REVIEW ENDPOINTS =====

@ratings_router.post("/submit")
async def submit_rating(
    rating_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Submit a rating and review for a vendor"""
    try:
        from models.rating_models import RatingCreate
        
        # Parse rating data
        rating_create = RatingCreate(**rating_data)
        
        # Submit rating
        success, result, error = await rating_service.submit_rating(current_user["user_id"], rating_create)
        
        if success:
            return {
                "message": "Rating submitted successfully",
                "rating": result["rating"],
                "vendor_score": result["vendor_score"]
            }
        else:
            raise HTTPException(status_code=400, detail=error)
            
    except Exception as e:
        logger.error(f"Submit rating error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit rating")

@ratings_router.get("/vendor/{vendor_id}")
async def get_vendor_ratings(
    vendor_id: str,
    limit: int = 50,
    offset: int = 0
):
    """Get ratings for a specific vendor"""
    try:
        ratings, total = await rating_service.get_vendor_ratings(vendor_id, limit, offset)
        
        return {
            "ratings": ratings,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Get vendor ratings error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ratings")

@ratings_router.get("/vendor/{vendor_id}/score")
async def get_vendor_score(vendor_id: str):
    """Get vendor's current score and badge information"""
    try:
        score = await rating_service.get_vendor_score(vendor_id)
        
        if not score:
            raise HTTPException(status_code=404, detail="Vendor score not found")
        
        return {"score": score}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vendor score error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendor score")

@ratings_router.get("/vendor/{vendor_id}/summary")
async def get_vendor_rating_summary(vendor_id: str):
    """Get vendor rating summary for display"""
    try:
        summary = await rating_service.get_vendor_rating_summary(vendor_id)
        
        if not summary:
            # Return default summary for vendors with no ratings
            return {
                "summary": {
                    "vendor_id": vendor_id,
                    "overall_score": 0.0,
                    "total_ratings": 0,
                    "badge": "new_vendor",
                    "recent_score_trend": "stable",
                    "top_categories": []
                }
            }
        
        return {"summary": summary.dict()}
        
    except Exception as e:
        logger.error(f"Get vendor summary error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve vendor summary")

@ratings_router.get("/eligible-orders")
async def get_rating_eligible_orders(
    vendor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get orders eligible for rating by current user"""
    try:
        eligible_orders = await rating_service.get_customer_rating_eligibility(
            current_user["user_id"], vendor_id
        )
        
        return {
            "eligible_orders": eligible_orders,
            "total": len(eligible_orders)
        }
        
    except Exception as e:
        logger.error(f"Get eligible orders error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve eligible orders")

@ratings_router.get("/vendor/{vendor_id}/analytics")
async def get_vendor_rating_analytics(
    vendor_id: str,
    period: str = "30d",
    current_user: dict = Depends(get_current_user)
):
    """Get rating analytics for vendor (vendor access only)"""
    try:
        # Verify user is the vendor or admin
        user_vendor_id = current_user.get("vendor_id", current_user["user_id"])
        if user_vendor_id != vendor_id and current_user.get("role") != "verification_officer":
            raise HTTPException(status_code=403, detail="Unauthorized to view analytics")
        
        analytics = await rating_service.get_rating_analytics(vendor_id, period)
        
        if not analytics:
            return {
                "analytics": {
                    "period": period,
                    "total_ratings": 0,
                    "average_rating": 0.0,
                    "rating_distribution": {},
                    "category_averages": {},
                    "trending_direction": "stable",
                    "improvement_areas": []
                }
            }
        
        return {"analytics": analytics.dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get rating analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rating analytics")

# Admin Rating Management
@ratings_router.get("/admin/flagged")
async def get_flagged_reviews(
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Get flagged reviews for admin review"""
    try:
        # This would be implemented in rating_service
        flagged_reviews = []
        
        return {
            "flagged_reviews": flagged_reviews,
            "total": len(flagged_reviews)
        }
        
    except Exception as e:
        logger.error(f"Get flagged reviews error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flagged reviews")

@ratings_router.get("/admin/vendor-badges")
async def get_vendor_badge_distribution(
    current_user: dict = Depends(require_role(UserRole.VERIFICATION_OFFICER))
):
    """Get distribution of vendor badges"""
    try:
        # Get badge distribution from database
        pipeline = [
            {"$group": {"_id": "$badge", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        cursor = db.vendor_scores.aggregate(pipeline)
        distribution = await cursor.to_list(length=None)
        
        badge_stats = {}
        for item in distribution:
            badge_stats[item["_id"]] = item["count"]
        
        return {"badge_distribution": badge_stats}
        
    except Exception as e:
        logger.error(f"Get badge distribution error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve badge distribution")

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

# =====================================
# Biometric Verification Endpoints
# =====================================

@biometric_router.post("/verification/start")
async def start_biometric_verification(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Start biometric verification session"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        if not vendor_id:
            raise HTTPException(status_code=400, detail="Vendor ID required")
        
        session_type = request.get("session_type", "initial_verification")
        session = await biometric_service.start_verification_session(vendor_id, session_type)
        
        return {
            "success": True,
            "session": session.dict(),
            "next_step": "document_upload",
            "message": "Biometric verification session started"
        }
    except Exception as e:
        logger.error(f"Failed to start biometric verification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@biometric_router.get("/verification/status/{vendor_id}")
async def get_biometric_status(
    vendor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get biometric verification status"""
    try:
        # Check authorization - user can only access their own status or admin can access any
        if current_user.get("vendor_id") != vendor_id and current_user.get("user_id") != vendor_id:
            if current_user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Access denied")
        
        status = await biometric_service.get_verification_status(vendor_id)
        return {
            "success": True,
            "status": status.dict()
        }
    except Exception as e:
        logger.error(f"Failed to get biometric status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@biometric_router.post("/document/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze uploaded identity document"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, and WebP allowed")
        
        # Read file content
        file_content = await file.read()
        
        # Convert to base64
        import base64
        file_base64 = base64.b64encode(file_content).decode()
        
        # Process document
        from models.biometric_models import DocumentType, DocumentUploadRequest
        doc_type = DocumentType(document_type)
        
        upload_request = DocumentUploadRequest(
            document_type=doc_type,
            image_data=f"data:{file.content_type};base64,{file_base64}",
            file_name=file.filename,
            vendor_id=current_user.get("vendor_id") or current_user.get("user_id")
        )
        
        result = await biometric_service.processor.process_document_analysis(
            upload_request.image_data,
            upload_request.document_type
        )
        
        return {
            "success": True,
            "analysis_result": result.dict(),
            "message": "Document analyzed successfully"
        }
        
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@biometric_router.post("/liveness/challenge")
async def create_liveness_challenge(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create liveness detection challenge"""
    try:
        from models.biometric_models import LivenessChallenge, LivenessCheckType
        
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        challenge_types = [LivenessCheckType.BLINK, LivenessCheckType.HEAD_TURN_LEFT, LivenessCheckType.SMILE]
        
        challenge = LivenessChallenge(
            vendor_id=vendor_id,
            challenge_type=challenge_types[0],  # Start with first challenge
            challenge_sequence=challenge_types,
            instructions="Please perform the following actions: blink, turn head left, then smile",
            timeout_seconds=30
        )
        
        # Store challenge in database
        challenge_dict = challenge.dict()
        await biometric_service.db.liveness_challenges.insert_one(challenge_dict)
        challenge_dict.pop("_id", None)
        
        return {
            "success": True,
            "challenge": challenge_dict,
            "message": "Liveness challenge created"
        }
        
    except Exception as e:
        logger.error(f"Failed to create liveness challenge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@biometric_router.post("/liveness/respond")
async def respond_to_liveness_challenge(
    file: UploadFile = File(...),
    challenge_id: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Respond to liveness challenge with video/image"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Convert to base64
        import base64
        file_base64 = base64.b64encode(file_content).decode()
        
        # Get challenge
        challenge_data = await biometric_service.db.liveness_challenges.find_one({"challenge_id": challenge_id})
        if not challenge_data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge_data.pop("_id", None)
        from models.biometric_models import LivenessChallenge, LivenessResponse
        challenge = LivenessChallenge(**challenge_data)
        
        # Create response
        response = LivenessResponse(
            challenge_id=challenge_id,
            response_data=f"data:{file.content_type};base64,{file_base64}"
        )
        
        # Process liveness
        result = await biometric_service.processor.perform_liveness_check(challenge, response)
        
        # Store result
        result_dict = result.dict()
        await biometric_service.db.liveness_results.insert_one(result_dict)
        result_dict.pop("_id", None)
        
        return {
            "success": True,
            "liveness_result": result_dict,
            "message": "Liveness check completed"
        }
        
    except Exception as e:
        logger.error(f"Liveness response failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@biometric_router.post("/face/match")
async def match_faces(
    reference_file: UploadFile = File(...),
    comparison_file: UploadFile = File(...),
    match_threshold: float = Form(0.75),
    current_user: dict = Depends(get_current_user)
):
    """Match faces between reference and comparison images"""
    try:
        # Read files
        ref_content = await reference_file.read()
        comp_content = await comparison_file.read()
        
        # Convert to base64
        import base64
        ref_base64 = base64.b64encode(ref_content).decode()
        comp_base64 = base64.b64encode(comp_content).decode()
        
        # Create match request
        from models.biometric_models import FaceMatchRequest
        match_request = FaceMatchRequest(
            vendor_id=current_user.get("vendor_id") or current_user.get("user_id"),
            reference_image=f"data:{reference_file.content_type};base64,{ref_base64}",
            comparison_image=f"data:{comparison_file.content_type};base64,{comp_base64}",
            match_threshold=match_threshold
        )
        
        # Perform matching
        result = await biometric_service.processor.perform_face_matching(match_request)
        
        # Store result
        result_dict = result.dict()
        await biometric_service.db.face_match_results.insert_one(result_dict)
        result_dict.pop("_id", None)
        
        return {
            "success": True,
            "match_result": result_dict,
            "message": "Face matching completed"
        }
        
    except Exception as e:
        logger.error(f"Face matching failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =====================================
# Security & Fraud Detection Endpoints  
# =====================================

@security_router.post("/device/register")
async def register_device(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Register a new device for security monitoring"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        device = await security_service.register_device(vendor_id, request)
        
        return {
            "success": True,
            "device": device.dict(),
            "message": "Device registered successfully"
        }
    except Exception as e:
        logger.error(f"Device registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.get("/dashboard")
async def get_security_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive security dashboard"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        dashboard = await security_service.generate_security_dashboard(vendor_id)
        
        return {
            "success": True,
            "dashboard": dashboard.dict()
        }
    except Exception as e:
        logger.error(f"Failed to get security dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/consent/request")
async def request_consent(
    request: dict,
    ip_address: str = Header(None, alias="x-forwarded-for"),
    user_agent: str = Header(None, alias="user-agent"),
    current_user: dict = Depends(get_current_user)
):
    """Request consent for data processing activities"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        consent_types = [ConsentType(ct) for ct in request.get("consent_types", [])]
        
        consents = await consent_service.request_consent(
            vendor_id, consent_types, ip_address or "unknown", user_agent or "unknown"
        )
        
        return {
            "success": True,
            "consents": [c.dict() for c in consents],
            "message": "Consent requested successfully"
        }
    except Exception as e:
        logger.error(f"Consent request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/consent/grant")
async def grant_consent(
    request: dict,
    ip_address: str = Header(None, alias="x-forwarded-for"),
    user_agent: str = Header(None, alias="user-agent"),
    current_user: dict = Depends(get_current_user)
):
    """Grant consent for specific processing activities"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        consent_ids = request.get("consent_ids", [])
        
        success = await consent_service.grant_consent(
            consent_ids, vendor_id, ip_address or "unknown", user_agent or "unknown"
        )
        
        return {
            "success": success,
            "message": "Consent granted successfully" if success else "Failed to grant consent"
        }
    except Exception as e:
        logger.error(f"Consent granting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/consent/withdraw")
async def withdraw_consent(
    request: dict,
    ip_address: str = Header(None, alias="x-forwarded-for"),
    user_agent: str = Header(None, alias="user-agent"),
    current_user: dict = Depends(get_current_user)
):
    """Withdraw consent and optionally request data deletion"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        withdrawal_request = ConsentWithdrawalRequest(
            vendor_id=vendor_id,
            consent_ids=request.get("consent_ids", []),
            withdrawal_reason=request.get("reason"),
            data_deletion_requested=request.get("delete_data", True),
            deletion_deadline=datetime.now(timezone.utc) + timedelta(days=30),
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown"
        )
        
        withdrawal_id = await consent_service.withdraw_consent(withdrawal_request)
        
        return {
            "success": True,
            "withdrawal_id": withdrawal_id,
            "message": "Consent withdrawn successfully. Data deletion will be processed within 30 days."
        }
    except Exception as e:
        logger.error(f"Consent withdrawal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.get("/compliance/report")
async def get_compliance_report(
    current_user: dict = Depends(get_current_user)
):
    """Generate GDPR compliance report"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        report = await consent_service.generate_compliance_report(vendor_id)
        
        return {
            "success": True,
            "report": report.dict()
        }
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/fraud/check-duplicates")
async def check_duplicate_registration(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Check for duplicate registrations and fraud indicators"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        biometric_templates = request.get("biometric_templates", [])
        documents = request.get("documents", [])
        device_info = request.get("device_info", {})
        
        detection_result = await fraud_detection_service.check_duplicate_registration(
            vendor_id, biometric_templates, documents, device_info
        )
        
        return {
            "success": True,
            "detection_result": detection_result.dict(),
            "message": f"Duplicate check completed. Risk score: {detection_result.risk_score.overall_score:.1f}"
        }
    except Exception as e:
        logger.error(f"Duplicate check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/fraud/analyze-synthetic-identity")
async def analyze_synthetic_identity(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Analyze profile for synthetic identity indicators"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        profile_data = request.get("profile_data", {})
        registration_metadata = request.get("registration_metadata", {})
        
        indicators = await fraud_detection_service.analyze_synthetic_identity(
            vendor_id, profile_data, registration_metadata
        )
        
        return {
            "success": True,
            "synthetic_identity_indicators": indicators.dict(),
            "message": f"Synthetic identity analysis completed. Confidence: {indicators.confidence_score:.2f}"
        }
    except Exception as e:
        logger.error(f"Synthetic identity analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@security_router.post("/fraud/detect-review-manipulation")
async def detect_review_manipulation(
    current_user: dict = Depends(get_current_user)
):
    """Detect review manipulation and fake reviews"""
    try:
        vendor_id = current_user.get("vendor_id") or current_user.get("user_id")
        
        detection = await fraud_detection_service.detect_review_manipulation(vendor_id)
        
        return {
            "success": True,
            "manipulation_detection": detection.dict(),
            "message": f"Review manipulation analysis completed. Confidence: {detection.confidence_score:.2f}"
        }
    except Exception as e:
        logger.error(f"Review manipulation detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request, call_next):
    """Apply rate limiting to API requests"""
    try:
        # Extract vendor ID from JWT token if present
        vendor_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
                vendor_id = payload.get("vendor_id") or payload.get("user_id")
            except:
                pass
        
        if vendor_id:
            # Check rate limit
            endpoint = str(request.url.path)
            ip_address = request.client.host
            
            if not await security_service.check_rate_limit(vendor_id, endpoint, ip_address):
                return Response(
                    content=json.dumps({"error": "Rate limit exceeded"}),
                    status_code=429,
                    media_type="application/json"
                )
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        response = await call_next(request)
        return response

# Enhanced authentication with device trust
async def get_current_user_with_device_check(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Enhanced authentication with device trust verification"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        vendor_id = payload.get("vendor_id") or payload.get("user_id")
        
        if not vendor_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check device trust (optional - can be made mandatory)
        device_id = payload.get("device_id")
        if device_id:
            is_trusted = await security_service.verify_device_trust(device_id, vendor_id)
            if not is_trusted:
                logger.warning(f"Untrusted device access attempt: {device_id}")
                # Could raise exception or just log warning
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Include routers
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(vendor_router)
app.include_router(admin_router)
app.include_router(escrow_router)
app.include_router(ratings_router)
app.include_router(biometric_router)
app.include_router(security_router)
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

@app.on_event("startup")
async def startup_db_setup():
    """Setup database indexes and collections on startup"""
    try:
        await db_setup.setup_database()
        logger.info("Database setup completed on startup")
    except Exception as e:
        logger.error(f"Database setup failed on startup: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()