from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import Optional
from io import BytesIO

# Import models and services
from models.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorsResponse
from services.vendor_service import VendorService
from services.qr_barcode_service import QRBarcodeService
from services.upload_service import UploadService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Vendor ID Management API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
vendor_service = VendorService(db)
qr_barcode_service = QRBarcodeService()
upload_service = UploadService()

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "Vendor ID Management API", "status": "active"}

# Vendor endpoints
@api_router.post("/vendors", response_model=VendorResponse)
async def create_vendor(vendor_data: VendorCreate):
    """Create a new vendor"""
    try:
        vendor = await vendor_service.create_vendor(vendor_data)
        return VendorResponse(vendor=vendor, message="Vendor created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/vendors", response_model=VendorsResponse)
async def get_vendors(
    search: Optional[str] = Query(None, description="Search by name or ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of vendors to return"),
    offset: int = Query(0, ge=0, description="Number of vendors to skip")
):
    """Get all vendors with optional filtering"""
    try:
        vendors, total = await vendor_service.get_vendors(search, status, limit, offset)
        return VendorsResponse(vendors=vendors, total=total)
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

# QR Code and Barcode endpoints
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