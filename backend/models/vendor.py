from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    photo: Optional[str] = None
    issueDate: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        # Convert to uppercase
        return v.strip().upper()
    
    @validator('issueDate')
    def validate_issue_date(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError('Issue date must be in YYYY-MM-DD format')
        return datetime.now().strftime('%Y-%m-%d')

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    photo: Optional[str] = None
    status: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip().upper()
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ['verified', 'pending']:
            raise ValueError('Status must be either "verified" or "pending"')
        return v

class Vendor(BaseModel):
    id: str
    name: str
    photo: Optional[str] = None
    issueDate: str
    status: str = 'pending'
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class VendorResponse(BaseModel):
    vendor: Vendor
    message: str = "Success"

class VendorsResponse(BaseModel):
    vendors: list[Vendor]
    total: int
    message: str = "Success"