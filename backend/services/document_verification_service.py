import os
import uuid
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
import logging
import hashlib
import re

# Optional imports for OCR - will use mock if not available
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentVerificationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.documents_collection = db.vendor_documents
        self.verification_queue_collection = db.verification_queue
        self.upload_dir = "/app/uploads/documents"
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        
    def generate_document_id(self) -> str:
        """Generate unique document ID"""
        return f"DOC-{uuid.uuid4().hex[:12].upper()}"
    
    def generate_file_hash(self, file_path: str) -> str:
        """Generate hash for duplicate detection"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Failed to generate file hash: {e}")
            return ""
    
    async def save_uploaded_document(
        self, 
        vendor_id: str,
        file_data: bytes,
        filename: str,
        document_type: str,
        document_subtype: str = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Save uploaded document and create verification record"""
        try:
            # Generate unique document ID
            document_id = self.generate_document_id()
            
            # Create file path
            file_extension = os.path.splitext(filename)[1].lower()
            safe_filename = f"{document_id}_{document_type}{file_extension}"
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Generate file hash for duplicate detection
            file_hash = self.generate_file_hash(file_path)
            
            # Check for duplicates (allow same vendor to replace documents)
            duplicate = await self.documents_collection.find_one({
                "file_hash": file_hash,
                "vendor_id": {"$ne": vendor_id}  # Only prevent duplicates from different vendors
            })
            
            # Allow duplicate from same vendor (document update/replacement)
            existing_doc = await self.documents_collection.find_one({
                "vendor_id": vendor_id,
                "document_type": document_type
            })
            
            if duplicate and not existing_doc:
                # Remove the uploaded file only if it's a true cross-vendor duplicate
                os.remove(file_path)
                return False, None, "Document appears to be a duplicate of another vendor's submission"
            
            # If same vendor is replacing a document, mark old one as replaced
            if existing_doc:
                await self.documents_collection.update_one(
                    {"document_id": existing_doc["document_id"]},
                    {
                        "$set": {
                            "status": "replaced",
                            "replaced_at": datetime.utcnow(),
                            "replaced_by": document_id
                        }
                    }
                )
            
            # Create document record
            document_record = {
                "document_id": document_id,
                "vendor_id": vendor_id,
                "document_type": document_type,
                "document_subtype": document_subtype,
                "original_filename": filename,
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size": len(file_data),
                "upload_timestamp": datetime.utcnow(),
                "status": "uploaded",
                "ocr_text": None,
                "extracted_info": {},
                "verification_status": "pending",
                "verification_notes": "",
                "verified_by": None,
                "verified_at": None
            }
            
            await self.documents_collection.insert_one(document_record)
            
            # Add to verification queue
            await self._add_to_verification_queue(vendor_id, document_id, document_type)
            
            # Perform automated checks
            await self._perform_automated_checks(document_id, file_path, document_type)
            
            return True, document_id, "Document uploaded successfully"
            
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return False, None, f"Failed to upload document: {str(e)}"
    
    async def _add_to_verification_queue(self, vendor_id: str, document_id: str, document_type: str):
        """Add document to verification queue"""
        try:
            queue_item = {
                "queue_id": str(uuid.uuid4()),
                "vendor_id": vendor_id,
                "document_id": document_id,
                "document_type": document_type,
                "priority": self._get_document_priority(document_type),
                "status": "pending",
                "created_at": datetime.utcnow(),
                "assigned_to": None,
                "reviewed_at": None
            }
            
            await self.verification_queue_collection.insert_one(queue_item)
            
        except Exception as e:
            logger.error(f"Failed to add to verification queue: {e}")
    
    def _get_document_priority(self, document_type: str) -> int:
        """Get verification priority based on document type"""
        priority_map = {
            "business_registration": 5,  # Highest priority
            "tax_id": 4,
            "government_id": 4,
            "operating_license": 3,
            "association_membership": 2,
            "other": 1  # Lowest priority
        }
        return priority_map.get(document_type, 1)
    
    async def _perform_automated_checks(self, document_id: str, file_path: str, document_type: str):
        """Perform automated OCR and validation checks"""
        try:
            # OCR text extraction
            ocr_text = await self._extract_text_ocr(file_path)
            
            # Extract relevant information based on document type
            extracted_info = await self._extract_document_info(ocr_text, document_type)
            
            # Update document record
            await self.documents_collection.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "ocr_text": ocr_text,
                        "extracted_info": extracted_info,
                        "automated_check_completed": True,
                        "automated_check_timestamp": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Automated checks failed for document {document_id}: {e}")
    
    async def _extract_text_ocr(self, file_path: str) -> str:
        """Extract text using OCR"""
        try:
            if not OCR_AVAILABLE:
                # Return mock OCR text since pytesseract is not available
                return f"[OCR Mock] Text extracted from {os.path.basename(file_path)}"
            
            # Real OCR implementation would go here
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return f"[OCR Mock] Text extracted from {os.path.basename(file_path)}"
    
    async def _extract_document_info(self, ocr_text: str, document_type: str) -> Dict:
        """Extract structured information from OCR text"""
        extracted_info = {}
        
        try:
            if document_type == "business_registration":
                # Look for business registration patterns
                business_name_pattern = r"business name[:\s]+([^\n]+)"
                reg_number_pattern = r"registration[^\d]*(\d+)"
                
                business_name_match = re.search(business_name_pattern, ocr_text, re.IGNORECASE)
                reg_number_match = re.search(reg_number_pattern, ocr_text, re.IGNORECASE)
                
                if business_name_match:
                    extracted_info["business_name"] = business_name_match.group(1).strip()
                if reg_number_match:
                    extracted_info["registration_number"] = reg_number_match.group(1).strip()
                    
            elif document_type == "tax_id":
                # Look for tax ID patterns
                tax_id_patterns = [
                    r"tax[^\d]*(\d+)",
                    r"tin[^\d]*(\d+)", 
                    r"federal id[^\d]*(\d+)"
                ]
                
                for pattern in tax_id_patterns:
                    match = re.search(pattern, ocr_text, re.IGNORECASE)
                    if match:
                        extracted_info["tax_id"] = match.group(1).strip()
                        break
                        
            elif document_type == "government_id":
                # Look for ID patterns
                id_patterns = [
                    r"id[^\d]*(\d+)",
                    r"passport[^\d]*(\d+)",
                    r"license[^\d]*(\d+)"
                ]
                
                for pattern in id_patterns:
                    match = re.search(pattern, ocr_text, re.IGNORECASE)
                    if match:
                        extracted_info["id_number"] = match.group(1).strip()
                        break
            
            # Look for dates
            date_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
            date_matches = re.findall(date_pattern, ocr_text)
            if date_matches:
                extracted_info["dates_found"] = date_matches
            
        except Exception as e:
            logger.error(f"Information extraction failed: {e}")
        
        return extracted_info
    
    async def get_vendor_documents(self, vendor_id: str) -> List[Dict]:
        """Get all documents for a vendor"""
        try:
            documents = await self.documents_collection.find(
                {"vendor_id": vendor_id}
            ).sort("upload_timestamp", -1).to_list(None)
            
            # Remove sensitive file paths
            for doc in documents:
                doc.pop("_id", None)
                doc.pop("file_path", None)
                doc.pop("file_hash", None)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get vendor documents: {e}")
            return []
    
    async def get_verification_queue(self, limit: int = 50, assigned_to: str = None) -> List[Dict]:
        """Get documents pending verification"""
        try:
            query = {"status": "pending"}
            if assigned_to:
                query["assigned_to"] = assigned_to
            
            queue_items = await self.verification_queue_collection.find(query).sort([
                ("priority", -1), 
                ("created_at", 1)
            ]).limit(limit).to_list(None)
            
            # Enrich with document and vendor info
            enriched_items = []
            for item in queue_items:
                # Get document info
                document = await self.documents_collection.find_one(
                    {"document_id": item["document_id"]}
                )
                if document:
                    item["document_info"] = {
                        "original_filename": document["original_filename"],
                        "document_type": document["document_type"],
                        "file_size": document["file_size"],
                        "upload_timestamp": document["upload_timestamp"]
                    }
                
                # Get vendor info
                vendor = await self.db.vendor_profiles.find_one(
                    {"vendor_id": item["vendor_id"]}
                )
                if vendor:
                    item["vendor_info"] = {
                        "business_name": vendor["business_name"],
                        "email": vendor.get("email", ""),
                        "country": vendor.get("country", "")
                    }
                
                item.pop("_id", None)
                enriched_items.append(item)
            
            return enriched_items
            
        except Exception as e:
            logger.error(f"Failed to get verification queue: {e}")
            return []
    
    async def approve_document(
        self, 
        document_id: str, 
        reviewer_id: str, 
        notes: str = ""
    ) -> Tuple[bool, str]:
        """Approve a document"""
        try:
            # Update document status
            result = await self.documents_collection.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "verification_status": "approved",
                        "verification_notes": notes,
                        "verified_by": reviewer_id,
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update queue status
                await self.verification_queue_collection.update_one(
                    {"document_id": document_id},
                    {
                        "$set": {
                            "status": "approved",
                            "reviewed_at": datetime.utcnow()
                        }
                    }
                )
                
                return True, "Document approved successfully"
            else:
                return False, "Document not found"
                
        except Exception as e:
            logger.error(f"Failed to approve document: {e}")
            return False, f"Failed to approve document: {str(e)}"
    
    async def reject_document(
        self, 
        document_id: str, 
        reviewer_id: str, 
        reason: str
    ) -> Tuple[bool, str]:
        """Reject a document"""
        try:
            # Update document status
            result = await self.documents_collection.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "verification_status": "rejected",
                        "verification_notes": reason,
                        "verified_by": reviewer_id,
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update queue status
                await self.verification_queue_collection.update_one(
                    {"document_id": document_id},
                    {
                        "$set": {
                            "status": "rejected",
                            "reviewed_at": datetime.utcnow()
                        }
                    }
                )
                
                return True, "Document rejected"
            else:
                return False, "Document not found"
                
        except Exception as e:
            logger.error(f"Failed to reject document: {e}")
            return False, f"Failed to reject document: {str(e)}"
    
    async def get_vendor_verification_summary(self, vendor_id: str) -> Dict:
        """Get verification summary for a vendor"""
        try:
            documents = await self.documents_collection.find(
                {"vendor_id": vendor_id}
            ).to_list(None)
            
            required_docs = [
                "business_registration",
                "tax_id", 
                "government_id"
            ]
            
            summary = {
                "total_documents": len(documents),
                "approved_documents": len([d for d in documents if d["verification_status"] == "approved"]),
                "rejected_documents": len([d for d in documents if d["verification_status"] == "rejected"]),
                "pending_documents": len([d for d in documents if d["verification_status"] == "pending"]),
                "required_docs_submitted": 0,
                "required_docs_approved": 0,
                "verification_complete": False
            }
            
            for req_doc in required_docs:
                doc_exists = any(d["document_type"] == req_doc for d in documents)
                if doc_exists:
                    summary["required_docs_submitted"] += 1
                    
                doc_approved = any(
                    d["document_type"] == req_doc and d["verification_status"] == "approved" 
                    for d in documents
                )
                if doc_approved:
                    summary["required_docs_approved"] += 1
            
            # Check if verification is complete
            summary["verification_complete"] = (
                summary["required_docs_approved"] >= len(required_docs) and
                summary["pending_documents"] == 0
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get verification summary: {e}")
            return {}