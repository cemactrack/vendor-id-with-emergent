from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import re

class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    photo: Optional[str] = None
    issueDate: Optional[str] = None
    expiryDate: Optional[str] = None
    template: Optional[str] = "standard"
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip().upper()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                raise ValueError('Phone number must be between 10-15 digits')
            return phone_digits
        return v
    
    @validator('company', 'department', 'position')
    def validate_text_fields(cls, v):
        if v:
            return v.strip().upper()
        return v
    
    @validator('issueDate', 'expiryDate')
    def validate_dates(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v
    
    @validator('template')
    def validate_template(cls, v):
        allowed_templates = ['standard', 'premium', 'executive']
        if v not in allowed_templates:
            raise ValueError(f'Template must be one of {allowed_templates}')
        return v

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    photo: Optional[str] = None
    status: Optional[str] = None
    expiryDate: Optional[str] = None
    template: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip().upper()
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['verified', 'pending', 'expired', 'suspended']:
            raise ValueError('Status must be one of: verified, pending, expired, suspended')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v:
            phone_digits = re.sub(r'\D', '', v)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                raise ValueError('Phone number must be between 10-15 digits')
            return phone_digits
        return v

class Vendor(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    photo: Optional[str] = None
    issueDate: str
    expiryDate: Optional[str] = None
    status: str = 'pending'
    template: str = 'standard'
    digitalSignature: Optional[str] = None
    securityCode: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def is_expired(self) -> bool:
        if not self.expiryDate:
            return False
        try:
            expiry = datetime.strptime(self.expiryDate, '%Y-%m-%d')
            return datetime.now() > expiry
        except ValueError:
            return False

class BulkVendorCreate(BaseModel):
    vendors: List[VendorCreate]
    template: str = 'standard'
    defaultExpiryMonths: int = 12

class VendorResponse(BaseModel):
    vendor: Vendor
    message: str = "Success"

class VendorsResponse(BaseModel):
    vendors: List[Vendor]
    total: int
    message: str = "Success"

class BulkVendorResponse(BaseModel):
    created: List[Vendor]
    errors: List[dict]
    total_created: int
    total_errors: int
    message: str = "Bulk operation completed"