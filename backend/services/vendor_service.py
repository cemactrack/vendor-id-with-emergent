from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vendor import Vendor, VendorCreate, VendorUpdate
from datetime import datetime
import random
import string

class VendorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.vendors
    
    def generate_vendor_id(self) -> str:
        """Generate unique vendor ID in format VID-NG-XXXX"""
        number = random.randint(1000, 9999)
        return f"VID-NG-{number}"
    
    async def ensure_unique_id(self) -> str:
        """Ensure generated vendor ID is unique"""
        max_attempts = 100
        for _ in range(max_attempts):
            vendor_id = self.generate_vendor_id()
            existing = await self.collection.find_one({"id": vendor_id})
            if not existing:
                return vendor_id
        raise Exception("Unable to generate unique vendor ID")
    
    async def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor"""
        vendor_id = await self.ensure_unique_id()
        now = datetime.utcnow()
        
        vendor_dict = {
            "id": vendor_id,
            "name": vendor_data.name,
            "photo": vendor_data.photo,
            "issueDate": vendor_data.issueDate or now.strftime('%Y-%m-%d'),
            "status": "pending",
            "createdAt": now,
            "updatedAt": now
        }
        
        result = await self.collection.insert_one(vendor_dict)
        if result.inserted_id:
            return Vendor(**vendor_dict)
        else:
            raise Exception("Failed to create vendor")
    
    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        vendor_doc = await self.collection.find_one({"id": vendor_id})
        if vendor_doc:
            vendor_doc.pop('_id', None)  # Remove MongoDB _id
            return Vendor(**vendor_doc)
        return None
    
    async def get_vendors(self, search: Optional[str] = None, status: Optional[str] = None, 
                         limit: int = 50, offset: int = 0) -> tuple[List[Vendor], int]:
        """Get vendors with optional filtering"""
        query = {}
        
        # Build search query
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"id": {"$regex": search, "$options": "i"}}
            ]
        
        if status and status != 'all':
            query["status"] = status
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get vendors with pagination
        cursor = self.collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        vendors_docs = await cursor.to_list(length=limit)
        
        vendors = []
        for doc in vendors_docs:
            doc.pop('_id', None)  # Remove MongoDB _id
            vendors.append(Vendor(**doc))
        
        return vendors, total
    
    async def update_vendor(self, vendor_id: str, vendor_data: VendorUpdate) -> Optional[Vendor]:
        """Update vendor"""
        update_dict = {"updatedAt": datetime.utcnow()}
        
        # Only update provided fields
        if vendor_data.name is not None:
            update_dict["name"] = vendor_data.name
        if vendor_data.photo is not None:
            update_dict["photo"] = vendor_data.photo
        if vendor_data.status is not None:
            update_dict["status"] = vendor_data.status
        
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