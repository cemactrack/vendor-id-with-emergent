from typing import List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vendor import Vendor, VendorCreate, VendorUpdate, BulkVendorCreate
from datetime import datetime, timedelta
import random
import string
import hashlib
import secrets

class VendorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.vendors
    
    def generate_vendor_id(self) -> str:
        """Generate unique vendor ID in format VID-NG-XXXX"""
        number = random.randint(1000, 9999)
        return f"VID-NG-{number}"
    
    def generate_security_code(self) -> str:
        """Generate 6-digit security code"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    def generate_digital_signature(self, vendor_data: dict) -> str:
        """Generate digital signature for security"""
        # Create signature from vendor data + timestamp + secret
        secret_key = secrets.token_hex(16)
        signature_data = f"{vendor_data.get('id')}{vendor_data.get('name')}{vendor_data.get('issueDate')}{secret_key}"
        return hashlib.sha256(signature_data.encode()).hexdigest()[:16].upper()
    
    async def ensure_unique_id(self) -> str:
        """Ensure generated vendor ID is unique"""
        max_attempts = 100
        for _ in range(max_attempts):
            vendor_id = self.generate_vendor_id()
            existing = await self.collection.find_one({"id": vendor_id})
            if not existing:
                return vendor_id
        raise Exception("Unable to generate unique vendor ID")
    
    def calculate_expiry_date(self, issue_date: str, months: int = 12) -> str:
        """Calculate expiry date based on issue date"""
        issue_dt = datetime.strptime(issue_date, '%Y-%m-%d')
        expiry_dt = issue_dt + timedelta(days=365 * months // 12)
        return expiry_dt.strftime('%Y-%m-%d')
    
    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor"""
        vendor_id = await self.ensure_unique_id()
        now = datetime.utcnow()
        issue_date = vendor_data.issueDate or now.strftime('%Y-%m-%d')
        
        # Calculate expiry date if not provided
        expiry_date = vendor_data.expiryDate
        if not expiry_date:
            expiry_date = self.calculate_expiry_date(issue_date)
        
        vendor_dict = {
            "id": vendor_id,
            "name": vendor_data.name,
            "email": vendor_data.email,
            "phone": vendor_data.phone,
            "address": vendor_data.address,
            "company": vendor_data.company,
            "department": vendor_data.department,
            "position": vendor_data.position,
            "photo": vendor_data.photo,
            "issueDate": issue_date,
            "expiryDate": expiry_date,
            "status": "pending",
            "template": vendor_data.template or "standard",
            "securityCode": self.generate_security_code(),
            "createdAt": now,
            "updatedAt": now
        }
        
        # Generate digital signature
        vendor_dict["digitalSignature"] = self.generate_digital_signature(vendor_dict)
        
        result = await self.collection.insert_one(vendor_dict)
        if result.inserted_id:
            return Vendor(**vendor_dict)
        else:
            raise Exception("Failed to create vendor")
    
    async def bulk_create_vendors(self, bulk_data: BulkVendorCreate) -> Tuple[List[Vendor], List[dict]]:
        """Create multiple vendors at once"""
        created_vendors = []
        errors = []
        
        for i, vendor_data in enumerate(bulk_data.vendors):
            try:
                # Set default template and expiry
                if not vendor_data.template:
                    vendor_data.template = bulk_data.template
                if not vendor_data.expiryDate and not vendor_data.issueDate:
                    issue_date = datetime.now().strftime('%Y-%m-%d')
                    vendor_data.issueDate = issue_date
                    vendor_data.expiryDate = self.calculate_expiry_date(issue_date, bulk_data.defaultExpiryMonths)
                
                vendor = await self.create_vendor(vendor_data)
                created_vendors.append(vendor)
            except Exception as e:
                errors.append({
                    "index": i,
                    "name": vendor_data.name if hasattr(vendor_data, 'name') else 'Unknown',
                    "error": str(e)
                })
        
        return created_vendors, errors
    
    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        vendor_doc = await self.collection.find_one({"id": vendor_id})
        if vendor_doc:
            vendor_doc.pop('_id', None)
            return Vendor(**vendor_doc)
        return None
    
    async def get_vendors(self, search: Optional[str] = None, status: Optional[str] = None, 
                         template: Optional[str] = None, expired: Optional[bool] = None,
                         limit: int = 50, offset: int = 0) -> Tuple[List[Vendor], int]:
        """Get vendors with enhanced filtering"""
        query = {}
        
        # Build search query
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"id": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        if status and status != 'all':
            query["status"] = status
        
        if template and template != 'all':
            query["template"] = template
        
        # Handle expiry filter
        if expired is not None:
            current_date = datetime.now().strftime('%Y-%m-%d')
            if expired:
                query["expiryDate"] = {"$lt": current_date}
            else:
                query["$or"] = [
                    {"expiryDate": {"$gte": current_date}},
                    {"expiryDate": None}
                ]
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get vendors with pagination
        cursor = self.collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        vendors_docs = await cursor.to_list(length=limit)
        
        vendors = []
        for doc in vendors_docs:
            doc.pop('_id', None)
            vendor = Vendor(**doc)
            # Auto-update expired status
            if vendor.is_expired and vendor.status != 'expired':
                await self.update_vendor(vendor.id, VendorUpdate(status='expired'))
                vendor.status = 'expired'
            vendors.append(vendor)
        
        return vendors, total
    
    async def update_vendor(self, vendor_id: str, vendor_data: VendorUpdate) -> Optional[Vendor]:
        """Update vendor"""
        update_dict = {"updatedAt": datetime.utcnow()}
        
        # Only update provided fields
        for field in ['name', 'email', 'phone', 'address', 'company', 'department', 'position', 'photo', 'status', 'expiryDate', 'template']:
            value = getattr(vendor_data, field)
            if value is not None:
                update_dict[field] = value
        
        result = await self.collection.update_one(
            {"id": vendor_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await self.get_vendor(vendor_id)
        return None
    
    async def delete_vendor(self, vendor_id: str) -> bool:
        """Delete vendor"""
        result = await self.collection.delete_one({"id": vendor_id})
        return result.deleted_count > 0
    
    async def get_expiring_vendors(self, days_ahead: int = 30) -> List[Vendor]:
        """Get vendors expiring within specified days"""
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        query = {
            "expiryDate": {"$gte": current_date, "$lte": future_date},
            "status": {"$ne": "expired"}
        }
        
        cursor = self.collection.find(query).sort("expiryDate", 1)
        vendors_docs = await cursor.to_list(length=100)
        
        vendors = []
        for doc in vendors_docs:
            doc.pop('_id', None)
            vendors.append(Vendor(**doc))
        
        return vendors
    
    async def get_stats(self) -> dict:
        """Get vendor statistics"""
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_stats = {}
        async for result in self.collection.aggregate(pipeline):
            status_stats[result["_id"]] = result["count"]
        
        # Count expired vendors
        current_date = datetime.now().strftime('%Y-%m-%d')
        expired_count = await self.collection.count_documents({
            "expiryDate": {"$lt": current_date},
            "status": {"$ne": "expired"}
        })
        
        total = sum(status_stats.values())
        
        return {
            "total": total,
            "verified": status_stats.get("verified", 0),
            "pending": status_stats.get("pending", 0),
            "expired": status_stats.get("expired", 0) + expired_count,
            "suspended": status_stats.get("suspended", 0),
            "expiring_soon": len(await self.get_expiring_vendors(30))
        }