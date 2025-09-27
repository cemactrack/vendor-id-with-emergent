from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Query, Response, Depends, status
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
from services.enhanced_vendor_ecosystem_service import VendorEcosystemService
from services.auth_enhancement_service import AuthEnhancementService
from services.document_verification_service import DocumentVerificationService
from services.vendor_id_service import VendorIDService
from services.qr_barcode_service import QRBarcodeService
from services.upload_service import UploadService
from services.template_service import TemplateService
from services.ocr_service import DocumentOCRService
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
        dashboard_data = await ecosystem_service.get_vendor_dashboard(current_user["user_id"])
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard data")

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