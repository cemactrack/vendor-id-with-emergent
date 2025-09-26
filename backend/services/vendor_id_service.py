import uuid
import secrets
import string
from typing import Dict, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

class VendorIDService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.vendor_ids_collection = db.vendor_ids
        self.vendors_collection = db.vendor_profiles
        
        # Country code mapping
        self.country_codes = {
            "NG": "Nigeria",
            "CM": "Cameroon", 
            "GH": "Ghana",
            "KE": "Kenya",
            "ZA": "South Africa",
            "US": "United States",
            "GB": "United Kingdom",
            "CA": "Canada",
            "IN": "India",
            "AU": "Australia",
            "DE": "Germany",
            "FR": "France",
            "JP": "Japan",
            "CN": "China",
            "BR": "Brazil",
            "MX": "Mexico"
        }
    
    async def generate_vendor_id(self, vendor_id: str, country: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Generate unique Vendor ID number"""
        try:
            # Get country code
            country_code = country.upper() if len(country) == 2 else self._get_country_code(country)
            
            if not country_code:
                return False, None, "Invalid country"
            
            # Check if vendor already has an ID
            existing_id = await self.vendor_ids_collection.find_one({"vendor_id": vendor_id})
            if existing_id:
                return False, None, "Vendor ID already exists"
            
            # Generate unique ID number
            vendor_id_number = await self._generate_unique_id_number(country_code)
            
            # Create vendor ID record
            vendor_id_record = {
                "vendor_id": vendor_id,
                "vendor_id_number": vendor_id_number,
                "country_code": country_code,
                "country_name": self.country_codes.get(country_code, "Unknown"),
                "issued_date": datetime.utcnow(),
                "status": "active",
                "verification_level": 1,
                "trust_score": 50.0,  # Starting trust score
                "qr_code_url": "",
                "digital_card_url": "",
                "physical_card_requested": False,
                "physical_card_issued": False,
                "card_serial_number": None
            }
            
            # Generate QR code
            qr_code_data = await self._generate_qr_code(vendor_id_number)
            vendor_id_record["qr_code_url"] = qr_code_data
            
            # Generate digital card
            digital_card_data = await self._generate_digital_card(vendor_id_record, vendor_id)
            vendor_id_record["digital_card_url"] = digital_card_data
            
            # Save to database
            await self.vendor_ids_collection.insert_one(vendor_id_record)
            
            # Update vendor profile
            await self.vendors_collection.update_one(
                {"vendor_id": vendor_id},
                {
                    "$set": {
                        "vendor_id_number": vendor_id_number,
                        "verification_status": "verified",
                        "verification_level": 1,
                        "trust_score": 50.0,
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            return True, vendor_id_number, "Vendor ID generated successfully"
            
        except Exception as e:
            logger.error(f"Failed to generate vendor ID: {e}")
            return False, None, f"Failed to generate vendor ID: {str(e)}"
    
    def _get_country_code(self, country_name: str) -> Optional[str]:
        """Get country code from country name"""
        country_name_lower = country_name.lower()
        for code, name in self.country_codes.items():
            if name.lower() == country_name_lower:
                return code
        return None
    
    async def _generate_unique_id_number(self, country_code: str) -> str:
        """Generate unique ID number for the country"""
        max_attempts = 10
        
        for _ in range(max_attempts):
            # Generate 4-digit random number
            random_number = ''.join(secrets.choice(string.digits) for _ in range(4))
            vendor_id_number = f"VID-{country_code}-{random_number}"
            
            # Check if it already exists
            existing = await self.vendor_ids_collection.find_one({
                "vendor_id_number": vendor_id_number
            })
            
            if not existing:
                return vendor_id_number
        
        # Fallback: use timestamp if all attempts fail
        timestamp = str(int(datetime.utcnow().timestamp()))[-4:]
        return f"VID-{country_code}-{timestamp}"
    
    async def _generate_qr_code(self, vendor_id_number: str) -> str:
        """Generate QR code for vendor ID"""
        try:
            # Create verification URL
            verification_url = f"https://idecosystem.preview.emergentagent.com/verify/{vendor_id_number}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{qr_code_base64}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return ""
    
    async def _generate_digital_card(self, vendor_id_record: Dict, vendor_id: str) -> str:
        """Generate digital vendor ID card"""
        try:
            # Get vendor profile for additional info
            vendor_profile = await self.vendors_collection.find_one({"vendor_id": vendor_id})
            
            # Create a simple digital card (text-based for now)
            card_data = {
                "vendor_id_number": vendor_id_record["vendor_id_number"],
                "business_name": vendor_profile.get("business_name", "Unknown Business") if vendor_profile else "Unknown Business",
                "country": vendor_id_record["country_name"],
                "issued_date": vendor_id_record["issued_date"].strftime("%Y-%m-%d"),
                "verification_level": vendor_id_record["verification_level"],
                "trust_score": vendor_id_record["trust_score"],
                "status": vendor_id_record["status"]
            }
            
            # For now, return JSON data. In production, this would generate an actual card image
            import json
            return json.dumps(card_data)
            
        except Exception as e:
            logger.error(f"Failed to generate digital card: {e}")
            return "{}"
    
    async def get_vendor_id_info(self, vendor_id_number: str) -> Optional[Dict]:
        """Get vendor ID information"""
        try:
            vendor_id_record = await self.vendor_ids_collection.find_one({
                "vendor_id_number": vendor_id_number
            })
            
            if not vendor_id_record:
                return None
            
            # Get vendor profile
            vendor_profile = await self.vendors_collection.find_one({
                "vendor_id": vendor_id_record["vendor_id"]
            })
            
            # Combine information
            result = {
                "vendor_id_number": vendor_id_record["vendor_id_number"],
                "country": vendor_id_record["country_name"],
                "issued_date": vendor_id_record["issued_date"],
                "status": vendor_id_record["status"],
                "verification_level": vendor_id_record["verification_level"],
                "trust_score": vendor_id_record["trust_score"],
                "qr_code_url": vendor_id_record["qr_code_url"],
                "business_name": vendor_profile.get("business_name", "") if vendor_profile else "",
                "business_category": vendor_profile.get("category", "") if vendor_profile else "",
                "location": vendor_profile.get("business_address", "") if vendor_profile else "",
                "verified_since": vendor_id_record["issued_date"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get vendor ID info: {e}")
            return None
    
    async def update_trust_score(
        self, 
        vendor_id_number: str, 
        new_score: float, 
        reason: str = ""
    ) -> Tuple[bool, str]:
        """Update vendor trust score"""
        try:
            if not (0 <= new_score <= 100):
                return False, "Trust score must be between 0 and 100"
            
            result = await self.vendor_ids_collection.update_one(
                {"vendor_id_number": vendor_id_number},
                {
                    "$set": {
                        "trust_score": new_score,
                        "trust_score_updated": datetime.utcnow(),
                        "trust_score_reason": reason
                    }
                }
            )
            
            if result.modified_count > 0:
                # Also update in vendor profile
                vendor_record = await self.vendor_ids_collection.find_one({
                    "vendor_id_number": vendor_id_number
                })
                if vendor_record:
                    await self.vendors_collection.update_one(
                        {"vendor_id": vendor_record["vendor_id"]},
                        {"$set": {"trust_score": new_score}}
                    )
                
                return True, "Trust score updated successfully"
            else:
                return False, "Vendor ID not found"
                
        except Exception as e:
            logger.error(f"Failed to update trust score: {e}")
            return False, f"Failed to update trust score: {str(e)}"
    
    async def request_physical_card(self, vendor_id_number: str, shipping_address: Dict) -> Tuple[bool, str]:
        """Request physical Vendor ID card"""
        try:
            # Generate card serial number
            card_serial = f"CARD-{secrets.token_hex(6).upper()}"
            
            result = await self.vendor_ids_collection.update_one(
                {"vendor_id_number": vendor_id_number},
                {
                    "$set": {
                        "physical_card_requested": True,
                        "physical_card_request_date": datetime.utcnow(),
                        "shipping_address": shipping_address,
                        "card_serial_number": card_serial,
                        "card_status": "requested"
                    }
                }
            )
            
            if result.modified_count > 0:
                return True, f"Physical card requested. Serial number: {card_serial}"
            else:
                return False, "Vendor ID not found"
                
        except Exception as e:
            logger.error(f"Failed to request physical card: {e}")
            return False, f"Failed to request physical card: {str(e)}"
    
    async def suspend_vendor_id(self, vendor_id_number: str, reason: str, suspended_by: str) -> Tuple[bool, str]:
        """Suspend vendor ID"""
        try:
            result = await self.vendor_ids_collection.update_one(
                {"vendor_id_number": vendor_id_number},
                {
                    "$set": {
                        "status": "suspended",
                        "suspension_reason": reason,
                        "suspended_by": suspended_by,
                        "suspended_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update vendor profile status
                vendor_record = await self.vendor_ids_collection.find_one({
                    "vendor_id_number": vendor_id_number
                })
                if vendor_record:
                    await self.vendors_collection.update_one(
                        {"vendor_id": vendor_record["vendor_id"]},
                        {"$set": {"verification_status": "suspended"}}
                    )
                
                return True, "Vendor ID suspended successfully"
            else:
                return False, "Vendor ID not found"
                
        except Exception as e:
            logger.error(f"Failed to suspend vendor ID: {e}")
            return False, f"Failed to suspend vendor ID: {str(e)}"
    
    async def reactivate_vendor_id(self, vendor_id_number: str, reactivated_by: str) -> Tuple[bool, str]:
        """Reactivate suspended vendor ID"""
        try:
            result = await self.vendor_ids_collection.update_one(
                {"vendor_id_number": vendor_id_number, "status": "suspended"},
                {
                    "$set": {
                        "status": "active",
                        "reactivated_by": reactivated_by,
                        "reactivated_at": datetime.utcnow()
                    },
                    "$unset": {
                        "suspension_reason": "",
                        "suspended_by": "",
                        "suspended_at": ""
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update vendor profile status
                vendor_record = await self.vendor_ids_collection.find_one({
                    "vendor_id_number": vendor_id_number
                })
                if vendor_record:
                    await self.vendors_collection.update_one(
                        {"vendor_id": vendor_record["vendor_id"]},
                        {"$set": {"verification_status": "verified"}}
                    )
                
                return True, "Vendor ID reactivated successfully"
            else:
                return False, "Vendor ID not found or not suspended"
                
        except Exception as e:
            logger.error(f"Failed to reactivate vendor ID: {e}")
            return False, f"Failed to reactivate vendor ID: {str(e)}"