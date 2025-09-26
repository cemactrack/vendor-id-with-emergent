from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Response, Form
from fastapi.responses import StreamingResponse
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

# Import models and services
from models.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, VendorsResponse, 
    BulkVendorCreate, BulkVendorResponse
)
from services.vendor_service import VendorService
from services.qr_barcode_service import QRBarcodeService
from services.upload_service import UploadService
from services.template_service import TemplateService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Enhanced Vendor ID Management API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
vendor_service = VendorService(db)
qr_barcode_service = QRBarcodeService()
upload_service = UploadService()
template_service = TemplateService()

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "Enhanced Vendor ID Management API", "status": "active", "version": "2.0"}

# Vendor endpoints
@api_router.post("/vendors", response_model=VendorResponse)
async def create_vendor(vendor_data: VendorCreate):
    """Create a new vendor with enhanced features"""
    try:
        vendor = await vendor_service.create_vendor(vendor_data)
        return VendorResponse(vendor=vendor, message="Vendor created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/vendors/bulk", response_model=BulkVendorResponse)
async def bulk_create_vendors(bulk_data: BulkVendorCreate):
    """Create multiple vendors at once"""
    try:
        created_vendors, errors = await vendor_service.bulk_create_vendors(bulk_data)
        return BulkVendorResponse(
            created=created_vendors,
            errors=errors,
            total_created=len(created_vendors),
            total_errors=len(errors),
            message=f"Created {len(created_vendors)} vendors with {len(errors)} errors"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/vendors", response_model=VendorsResponse)
async def get_vendors(
    search: Optional[str] = Query(None, description="Search by name, ID, company, or email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    template: Optional[str] = Query(None, description="Filter by template"),
    expired: Optional[bool] = Query(None, description="Filter by expiry status"),
    limit: int = Query(50, ge=1, le=100, description="Number of vendors to return"),
    offset: int = Query(0, ge=0, description="Number of vendors to skip")
):
    """Get all vendors with enhanced filtering"""
    try:
        vendors, total = await vendor_service.get_vendors(search, status, template, expired, limit, offset)
        return VendorsResponse(vendors=vendors, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vendors/stats")
async def get_vendor_stats():
    """Get vendor statistics"""
    try:
        stats = await vendor_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vendors/expiring")
async def get_expiring_vendors(days: int = Query(30, ge=1, le=365)):
    """Get vendors expiring within specified days"""
    try:
        vendors = await vendor_service.get_expiring_vendors(days)
        return {"vendors": vendors, "count": len(vendors)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str):
    """Get a specific vendor by ID"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse(vendor=vendor)

@api_router.put("/vendors/{vendor_id}", response_model=VendorResponse)
async def update_vendor(vendor_id: str, vendor_data: VendorUpdate):
    """Update a vendor"""
    try:
        vendor = await vendor_service.update_vendor(vendor_id, vendor_data)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return VendorResponse(vendor=vendor, message="Vendor updated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str):
    """Delete a vendor"""
    success = await vendor_service.delete_vendor(vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"message": "Vendor deleted successfully"}

# Enhanced card endpoints
@api_router.get("/vendors/{vendor_id}/card-data")
async def get_enhanced_card_data(vendor_id: str):
    """Get enhanced card data with template information"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    card_data = template_service.generate_enhanced_card_data(vendor)
    
    # Add generated patterns
    card_data["patterns"] = {
        "circuit": template_service.create_circuit_pattern(400, 250),
        "holographic": template_service.create_holographic_pattern(400, 250),
        "watermark": template_service.create_security_watermark("VERIFIED VENDOR-ID SECURE TRADE", 400, 250)
    }
    
    return card_data

# Template endpoints
@api_router.get("/templates")
async def get_templates():
    """Get all available card templates"""
    return template_service.get_templates()

@api_router.get("/templates/{template_name}")
async def get_template(template_name: str):
    """Get specific template details"""
    if not template_service.validate_template(template_name):
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service.get_template(template_name)

# QR Code and Barcode endpoints (unchanged)
@api_router.get("/qr-code/{vendor_id}")
async def get_qr_code(vendor_id: str):
    """Generate QR code for vendor"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    qr_image_bytes = qr_barcode_service.get_qr_code_image(vendor_id)
    return StreamingResponse(BytesIO(qr_image_bytes), media_type="image/png")

@api_router.get("/barcode/{vendor_id}")
async def get_barcode(vendor_id: str):
    """Generate barcode for vendor"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    barcode_image_bytes = qr_barcode_service.get_barcode_image(vendor_id)
    return StreamingResponse(BytesIO(barcode_image_bytes), media_type="image/png")

@api_router.get("/qr-code-base64/{vendor_id}")
async def get_qr_code_base64(vendor_id: str):
    """Get QR code as base64 string"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    qr_base64 = qr_barcode_service.generate_qr_code(vendor_id)
    return {"qrCode": f"data:image/png;base64,{qr_base64}"}

@api_router.get("/barcode-base64/{vendor_id}")
async def get_barcode_base64(vendor_id: str):
    """Get barcode as base64 string"""
    vendor = await vendor_service.get_vendor(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    barcode_base64 = qr_barcode_service.generate_barcode(vendor_id)
    return {"barcode": f"data:image/png;base64,{barcode_base64}"}

# Photo upload endpoint
@api_router.post("/upload/photo")
async def upload_photo(file: UploadFile = File(...)):
    """Upload and process vendor photo"""
    try:
        photo_url = await upload_service.process_image(file)
        return {"photoUrl": photo_url, "message": "Photo uploaded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Bulk import/export endpoints
@api_router.post("/vendors/import/csv")
async def import_vendors_csv(file: UploadFile = File(...), template: str = Form("standard")):
    """Import vendors from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(csv_content.splitlines())
        
        vendors_data = []
        for row in csv_reader:
            vendor_data = VendorCreate(
                name=row.get('name', '').strip(),
                email=row.get('email', '').strip() or None,
                phone=row.get('phone', '').strip() or None,
                address=row.get('address', '').strip() or None,
                company=row.get('company', '').strip() or None,
                department=row.get('department', '').strip() or None,
                position=row.get('position', '').strip() or None,
                template=template
            )
            vendors_data.append(vendor_data)
        
        bulk_data = BulkVendorCreate(vendors=vendors_data, template=template)
        created_vendors, errors = await vendor_service.bulk_create_vendors(bulk_data)
        
        return BulkVendorResponse(
            created=created_vendors,
            errors=errors,
            total_created=len(created_vendors),
            total_errors=len(errors),
            message=f"Imported {len(created_vendors)} vendors with {len(errors)} errors"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@api_router.get("/vendors/export/csv")
async def export_vendors_csv():
    """Export all vendors to CSV"""
    try:
        vendors, _ = await vendor_service.get_vendors(limit=1000)
        
        output = BytesIO()
        output.write(b'\xef\xbb\xbf')  # UTF-8 BOM
        
        fieldnames = ['id', 'name', 'email', 'phone', 'address', 'company', 'department', 'position', 'status', 'issueDate', 'expiryDate', 'template']
        
        csv_content = "\n".join([
            ",".join(fieldnames),
            *[
                ",".join([
                    f'"{getattr(vendor, field) or ""}"' for field in fieldnames
                ]) for vendor in vendors
            ]
        ])
        
        output.write(csv_content.encode('utf-8'))
        output.seek(0)
        
        return StreamingResponse(
            BytesIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vendors.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

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