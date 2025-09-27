#!/usr/bin/env python3
"""
Comprehensive Vendor Onboarding & Verification Workflow Testing Suite
Tests complete vendor onboarding process with admin verification workflow and Vendor ID integration
"""

import requests
import json
import base64
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configuration
BACKEND_URL = "https://vendor-verify-3.preview.emergentagent.com/api"
TEST_VENDOR_EMAIL = "vendor.onboarding.test@example.com"
TEST_VENDOR_PASSWORD = "VendorTestPass123!"
TEST_ADMIN_EMAIL = "admin.verification@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminVerifyPass123!"

class VendorOnboardingTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.vendor_token = None
        self.admin_token = None
        self.vendor_id = None
        self.vendor_id_number = None
        self.uploaded_documents = []
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                    headers: Dict[str, str] = None, token: str = None, files: Dict = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {}
        
        if not files:
            request_headers["Content-Type"] = "application/json"
        
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, data=data, files=files, headers=request_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def test_health_check(self):
        """Test API health check"""
        try:
            response = self.make_request("GET", "/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, "API is healthy", data)
                return True
            else:
                self.log_test("Health Check", False, f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")
            return False
    
    def test_vendor_registration(self):
        """Test vendor user registration"""
        try:
            vendor_data = {
                "email": TEST_VENDOR_EMAIL,
                "password": TEST_VENDOR_PASSWORD,
                "full_name": "Onboarding Test Vendor",
                "phone": "+234-801-234-5678",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", vendor_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.log_test("Vendor Registration", True, "Vendor registered successfully", 
                                {"user_id": data["user"]["id"], "email": data["user"]["email"]})
                    return True
                else:
                    self.log_test("Vendor Registration", False, "Missing token or user in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    self.log_test("Vendor Registration", True, "User already exists - proceeding with login")
                    return self.test_vendor_login()
                else:
                    self.log_test("Vendor Registration", False, f"Registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("Vendor Registration", False, f"Registration error: {str(e)}")
            return False
    
    def test_admin_registration(self):
        """Test admin user registration"""
        try:
            admin_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD,
                "full_name": "Verification Admin Officer",
                "phone": "+234-802-987-6543",
                "country": "NG",
                "role": "verification_officer"
            }
            
            response = self.make_request("POST", "/auth/register", admin_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.admin_token = data["token"]
                    self.log_test("Admin Registration", True, "Admin registered successfully")
                    return True
                else:
                    self.log_test("Admin Registration", False, "Missing token in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    self.log_test("Admin Registration", True, "Admin already exists - proceeding with login")
                    return self.test_admin_login()
                else:
                    self.log_test("Admin Registration", False, f"Admin registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("Admin Registration", False, f"Admin registration error: {str(e)}")
            return False
    
    def test_vendor_login(self):
        """Test vendor login"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_VENDOR_EMAIL}&password={TEST_VENDOR_PASSWORD}"
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.log_test("Vendor Login", True, "Vendor login successful", 
                                {"user_id": data["user"]["id"], "role": data["user"]["role"]})
                    return True
                else:
                    self.log_test("Vendor Login", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_test("Vendor Login", False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vendor Login", False, f"Login error: {str(e)}")
            return False
    
    def test_admin_login(self):
        """Test admin login"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_ADMIN_EMAIL}&password={TEST_ADMIN_PASSWORD}"
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.admin_token = data["token"]
                    self.log_test("Admin Login", True, "Admin login successful")
                    return True
                else:
                    self.log_test("Admin Login", False, "Missing token in response", data)
                    return False
            else:
                self.log_test("Admin Login", False, f"Admin login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Admin login error: {str(e)}")
            return False
    
    def test_vendor_profile_creation(self):
        """Test vendor profile creation"""
        if not self.vendor_token:
            self.log_test("Vendor Profile Creation", False, "No vendor token available")
            return False
            
        try:
            profile_data = {
                "business_name": "TechVendor Solutions Nigeria Ltd",
                "business_description": "Leading provider of technology solutions and digital services in West Africa",
                "category": "technology",
                "website": "https://techvendor.ng",
                "business_address": "Plot 15, Technology Drive, Victoria Island, Lagos, Nigeria",
                "registration_number": "RC2024001234",
                "tax_id": "TIN20240987654",
                "established_year": 2020,
                "employee_count": 45
            }
            
            response = self.make_request("POST", "/vendors/profile", profile_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "profile" in data:
                    profile = data["profile"]
                    self.vendor_id = profile["vendor_id"]
                    self.log_test("Vendor Profile Creation", True, "Profile created successfully", 
                                {"vendor_id": self.vendor_id, "business_name": profile["business_name"]})
                    return True
                else:
                    self.log_test("Vendor Profile Creation", False, "Missing profile in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    self.log_test("Vendor Profile Creation", True, "Profile already exists - continuing tests")
                    return self.get_existing_vendor_profile()
                else:
                    self.log_test("Vendor Profile Creation", False, f"Profile creation failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("Vendor Profile Creation", False, f"Profile creation error: {str(e)}")
            return False
    
    def get_existing_vendor_profile(self):
        """Get existing vendor profile to continue tests"""
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data and "profile" in data["dashboard"]:
                    profile = data["dashboard"]["profile"]
                    self.vendor_id = profile["vendor_id"]
                    self.log_test("Get Existing Profile", True, f"Found existing profile: {self.vendor_id}")
                    return True
            return False
        except:
            return False
    
    def create_sample_document(self, doc_type: str, content: str) -> bytes:
        """Create sample document content"""
        if doc_type == "business_registration":
            document_content = f"""
CERTIFICATE OF INCORPORATION
Business Name: TechVendor Solutions Nigeria Ltd
Registration Number: RC2024001234
Date of Incorporation: January 15, 2020
Registered Address: Plot 15, Technology Drive, Victoria Island, Lagos, Nigeria
{content}
"""
        elif doc_type == "tax_id":
            document_content = f"""
TAX IDENTIFICATION NUMBER CERTIFICATE
Business Name: TechVendor Solutions Nigeria Ltd
Tax ID: TIN20240987654
Issue Date: February 1, 2020
Federal Inland Revenue Service
{content}
"""
        elif doc_type == "government_id":
            document_content = f"""
NATIONAL IDENTIFICATION CARD
Full Name: Onboarding Test Vendor
ID Number: 12345678901
Date of Birth: January 1, 1985
Issue Date: March 15, 2018
{content}
"""
        else:
            document_content = f"Sample document content for {doc_type}: {content}"
        
        return document_content.encode('utf-8')
    
    def test_document_upload_business_registration(self):
        """Test business registration document upload"""
        if not self.vendor_token:
            self.log_test("Document Upload - Business Registration", False, "No vendor token available")
            return False
            
        try:
            # Create sample business registration document
            file_content = self.create_sample_document("business_registration", "Official business registration certificate")
            
            # Prepare form data for file upload
            files = {
                'file': ('business_registration.pdf', file_content, 'application/pdf')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            response = self.make_request("POST", "/vendors/documents/upload", data=data, files=files, token=self.vendor_token)
            
            if response.status_code == 200:
                response_data = response.json()
                if "document_id" in response_data:
                    document_id = response_data["document_id"]
                    self.uploaded_documents.append({
                        "document_id": document_id,
                        "document_type": "business_registration"
                    })
                    self.log_test("Document Upload - Business Registration", True, "Business registration document uploaded successfully", 
                                {"document_id": document_id})
                    return True
                else:
                    self.log_test("Document Upload - Business Registration", False, "Missing document_id in response", response_data)
                    return False
            else:
                self.log_test("Document Upload - Business Registration", False, f"Document upload failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload - Business Registration", False, f"Document upload error: {str(e)}")
            return False
    
    def test_document_upload_tax_id(self):
        """Test tax ID document upload"""
        if not self.vendor_token:
            self.log_test("Document Upload - Tax ID", False, "No vendor token available")
            return False
            
        try:
            file_content = self.create_sample_document("tax_id", "Official tax identification certificate")
            
            files = {
                'file': ('tax_id_certificate.pdf', file_content, 'application/pdf')
            }
            data = {
                'document_type': 'tax_id'
            }
            
            response = self.make_request("POST", "/vendors/documents/upload", data=data, files=files, token=self.vendor_token)
            
            if response.status_code == 200:
                response_data = response.json()
                if "document_id" in response_data:
                    document_id = response_data["document_id"]
                    self.uploaded_documents.append({
                        "document_id": document_id,
                        "document_type": "tax_id"
                    })
                    self.log_test("Document Upload - Tax ID", True, "Tax ID document uploaded successfully", 
                                {"document_id": document_id})
                    return True
                else:
                    self.log_test("Document Upload - Tax ID", False, "Missing document_id in response", response_data)
                    return False
            else:
                self.log_test("Document Upload - Tax ID", False, f"Document upload failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload - Tax ID", False, f"Document upload error: {str(e)}")
            return False
    
    def test_document_upload_government_id(self):
        """Test government ID document upload"""
        if not self.vendor_token:
            self.log_test("Document Upload - Government ID", False, "No vendor token available")
            return False
            
        try:
            file_content = self.create_sample_document("government_id", "Official government identification document")
            
            files = {
                'file': ('government_id.pdf', file_content, 'application/pdf')
            }
            data = {
                'document_type': 'government_id'
            }
            
            response = self.make_request("POST", "/vendors/documents/upload", data=data, files=files, token=self.vendor_token)
            
            if response.status_code == 200:
                response_data = response.json()
                if "document_id" in response_data:
                    document_id = response_data["document_id"]
                    self.uploaded_documents.append({
                        "document_id": document_id,
                        "document_type": "government_id"
                    })
                    self.log_test("Document Upload - Government ID", True, "Government ID document uploaded successfully", 
                                {"document_id": document_id})
                    return True
                else:
                    self.log_test("Document Upload - Government ID", False, "Missing document_id in response", response_data)
                    return False
            else:
                self.log_test("Document Upload - Government ID", False, f"Document upload failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload - Government ID", False, f"Document upload error: {str(e)}")
            return False
    
    def test_document_validation(self):
        """Test document validation and OCR processing"""
        if not self.vendor_token:
            self.log_test("Document Validation", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/documents", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "documents" in data:
                    documents = data["documents"]
                    if len(documents) >= 3:  # Should have all 3 required documents
                        validation_passed = True
                        for doc in documents:
                            if doc.get("status") != "uploaded":
                                validation_passed = False
                                break
                        
                        if validation_passed:
                            self.log_test("Document Validation", True, f"All {len(documents)} documents validated successfully")
                            return True
                        else:
                            self.log_test("Document Validation", False, "Some documents failed validation")
                            return False
                    else:
                        self.log_test("Document Validation", False, f"Expected 3 documents, found {len(documents)}")
                        return False
                else:
                    self.log_test("Document Validation", False, "Missing documents in response", data)
                    return False
            else:
                self.log_test("Document Validation", False, f"Document listing failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Validation", False, f"Document validation error: {str(e)}")
            return False
    
    def test_admin_verification_queue(self):
        """Test admin verification queue endpoint"""
        if not self.admin_token:
            self.log_test("Admin Verification Queue", False, "No admin token available")
            return False
            
        try:
            response = self.make_request("GET", "/admin/verification-queue", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "queue" in data:
                    queue = data["queue"]
                    self.log_test("Admin Verification Queue", True, f"Retrieved {len(queue)} items in verification queue")
                    return True
                else:
                    self.log_test("Admin Verification Queue", False, "Missing queue in response", data)
                    return False
            else:
                self.log_test("Admin Verification Queue", False, f"Verification queue failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Verification Queue", False, f"Verification queue error: {str(e)}")
            return False
    
    def test_admin_document_review(self):
        """Test admin document review functionality"""
        if not self.admin_token or not self.uploaded_documents:
            self.log_test("Admin Document Review", False, "No admin token or uploaded documents available")
            return False
            
        try:
            # Test reviewing the first uploaded document
            document_id = self.uploaded_documents[0]["document_id"]
            
            response = self.make_request("GET", f"/admin/documents/{document_id}/review", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "document" in data and "vendor" in data:
                    document = data["document"]
                    vendor = data["vendor"]
                    self.log_test("Admin Document Review", True, "Document review data retrieved successfully", 
                                {"document_id": document["document_id"], "vendor_business": vendor.get("business_name", "Unknown")})
                    return True
                else:
                    self.log_test("Admin Document Review", False, "Missing document or vendor in response", data)
                    return False
            else:
                self.log_test("Admin Document Review", False, f"Document review failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Document Review", False, f"Document review error: {str(e)}")
            return False
    
    def test_admin_document_approval(self):
        """Test admin document approval process"""
        if not self.admin_token or not self.uploaded_documents:
            self.log_test("Admin Document Approval", False, "No admin token or uploaded documents available")
            return False
            
        try:
            approved_count = 0
            
            # Approve all uploaded documents
            for doc in self.uploaded_documents:
                document_id = doc["document_id"]
                doc_type = doc["document_type"]
                
                approval_data = {
                    "notes": f"Document {doc_type} approved after thorough review. All information verified."
                }
                
                response = self.make_request("POST", f"/admin/documents/{document_id}/approve", 
                                           approval_data, token=self.admin_token)
                
                if response.status_code == 200:
                    approved_count += 1
                    self.log_test(f"Document Approval - {doc_type}", True, f"Document {document_id} approved successfully")
                else:
                    self.log_test(f"Document Approval - {doc_type}", False, f"Document approval failed: {response.text}")
            
            if approved_count == len(self.uploaded_documents):
                self.log_test("Admin Document Approval", True, f"All {approved_count} documents approved successfully")
                return True
            else:
                self.log_test("Admin Document Approval", False, f"Only {approved_count}/{len(self.uploaded_documents)} documents approved")
                return False
                
        except Exception as e:
            self.log_test("Admin Document Approval", False, f"Document approval error: {str(e)}")
            return False
    
    def test_vendor_id_generation(self):
        """Test automatic Vendor ID generation after document approval"""
        if not self.vendor_token:
            self.log_test("Vendor ID Generation", False, "No vendor token available")
            return False
            
        try:
            # Wait a moment for the system to process approvals
            time.sleep(2)
            
            response = self.make_request("GET", "/vendors/vendor-id", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "vendor_id" in data and data["vendor_id"]:
                    vendor_id_info = data["vendor_id"]
                    self.vendor_id_number = vendor_id_info["vendor_id_number"]
                    
                    # Verify the ID format (should be VID-NG-XXXX for Nigeria)
                    if self.vendor_id_number.startswith("VID-NG-"):
                        self.log_test("Vendor ID Generation", True, f"Vendor ID generated successfully: {self.vendor_id_number}", 
                                    {"vendor_id_number": self.vendor_id_number, "trust_score": vendor_id_info.get("trust_score", 0)})
                        return True
                    else:
                        self.log_test("Vendor ID Generation", False, f"Invalid Vendor ID format: {self.vendor_id_number}")
                        return False
                else:
                    self.log_test("Vendor ID Generation", False, "Vendor ID not yet generated", data)
                    return False
            else:
                self.log_test("Vendor ID Generation", False, f"Vendor ID retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vendor ID Generation", False, f"Vendor ID generation error: {str(e)}")
            return False
    
    def test_qr_code_generation(self):
        """Test QR code generation for Vendor ID"""
        if not self.vendor_id_number:
            self.log_test("QR Code Generation", False, "No Vendor ID number available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/vendor-id", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "vendor_id" in data and data["vendor_id"]:
                    vendor_id_info = data["vendor_id"]
                    if "qr_code_url" in vendor_id_info and vendor_id_info["qr_code_url"]:
                        qr_code_url = vendor_id_info["qr_code_url"]
                        # Check if it's a valid base64 data URL
                        if qr_code_url.startswith("data:image/png;base64,"):
                            self.log_test("QR Code Generation", True, "QR code generated successfully", 
                                        {"qr_code_length": len(qr_code_url)})
                            return True
                        else:
                            self.log_test("QR Code Generation", False, "Invalid QR code format")
                            return False
                    else:
                        self.log_test("QR Code Generation", False, "QR code not generated")
                        return False
                else:
                    self.log_test("QR Code Generation", False, "Vendor ID info not available")
                    return False
            else:
                self.log_test("QR Code Generation", False, f"Failed to retrieve vendor ID info: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("QR Code Generation", False, f"QR code generation error: {str(e)}")
            return False
    
    def test_digital_card_creation(self):
        """Test digital card creation"""
        if not self.vendor_id_number:
            self.log_test("Digital Card Creation", False, "No Vendor ID number available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/vendor-id", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "vendor_id" in data and data["vendor_id"]:
                    vendor_id_info = data["vendor_id"]
                    required_fields = ["vendor_id_number", "business_name", "country", "trust_score", "verification_level"]
                    missing_fields = [field for field in required_fields if field not in vendor_id_info]
                    
                    if not missing_fields:
                        self.log_test("Digital Card Creation", True, "Digital card data available", 
                                    {"vendor_id": vendor_id_info["vendor_id_number"], 
                                     "business_name": vendor_id_info["business_name"]})
                        return True
                    else:
                        self.log_test("Digital Card Creation", False, f"Missing digital card fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Digital Card Creation", False, "Vendor ID info not available")
                    return False
            else:
                self.log_test("Digital Card Creation", False, f"Failed to retrieve vendor ID info: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Digital Card Creation", False, f"Digital card creation error: {str(e)}")
            return False
    
    def test_physical_card_request(self):
        """Test physical card request functionality"""
        if not self.vendor_id_number:
            self.log_test("Physical Card Request", False, "No Vendor ID number available")
            return False
            
        try:
            shipping_address = {
                "full_name": "Onboarding Test Vendor",
                "address_line_1": "Plot 15, Technology Drive",
                "address_line_2": "Victoria Island",
                "city": "Lagos",
                "state": "Lagos State",
                "postal_code": "101001",
                "country": "Nigeria",
                "phone": "+234-801-234-5678"
            }
            
            response = self.make_request("POST", "/vendors/vendor-id/request-physical-card", 
                                       {"shipping_address": shipping_address}, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Physical Card Request", True, "Physical card requested successfully", 
                                {"message": data["message"]})
                    return True
                else:
                    self.log_test("Physical Card Request", False, "Missing message in response", data)
                    return False
            else:
                self.log_test("Physical Card Request", False, f"Physical card request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Physical Card Request", False, f"Physical card request error: {str(e)}")
            return False
    
    def test_trust_score_update(self):
        """Test trust score updates"""
        if not self.vendor_token:
            self.log_test("Trust Score Update", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/vendor-id", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "vendor_id" in data and data["vendor_id"]:
                    vendor_id_info = data["vendor_id"]
                    trust_score = vendor_id_info.get("trust_score", 0)
                    
                    # Trust score should be updated after verification
                    if trust_score >= 50:  # Starting trust score
                        self.log_test("Trust Score Update", True, f"Trust score properly set: {trust_score}")
                        return True
                    else:
                        self.log_test("Trust Score Update", False, f"Trust score too low: {trust_score}")
                        return False
                else:
                    self.log_test("Trust Score Update", False, "Vendor ID info not available")
                    return False
            else:
                self.log_test("Trust Score Update", False, f"Failed to retrieve vendor ID info: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Trust Score Update", False, f"Trust score update error: {str(e)}")
            return False
    
    def test_verification_status_updates(self):
        """Test verification status updates throughout process"""
        if not self.vendor_token:
            self.log_test("Verification Status Updates", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    verification_status = dashboard.get("verification_status", "unknown")
                    
                    # After all documents are approved, status should be verified
                    if verification_status == "verified":
                        self.log_test("Verification Status Updates", True, f"Verification status correctly updated: {verification_status}")
                        return True
                    else:
                        self.log_test("Verification Status Updates", False, f"Unexpected verification status: {verification_status}")
                        return False
                else:
                    self.log_test("Verification Status Updates", False, "Missing dashboard in response", data)
                    return False
            else:
                self.log_test("Verification Status Updates", False, f"Dashboard request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Verification Status Updates", False, f"Verification status error: {str(e)}")
            return False
    
    def test_dashboard_data_updates(self):
        """Test dashboard data updates after verification"""
        if not self.vendor_token:
            self.log_test("Dashboard Data Updates", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    
                    # Check for updated fields after verification
                    required_fields = ["profile", "analytics", "verification_status"]
                    missing_fields = [field for field in required_fields if field not in dashboard]
                    
                    if not missing_fields:
                        profile = dashboard["profile"]
                        if profile.get("vendor_id_number"):
                            self.log_test("Dashboard Data Updates", True, "Dashboard data properly updated with Vendor ID", 
                                        {"vendor_id_number": profile["vendor_id_number"]})
                            return True
                        else:
                            self.log_test("Dashboard Data Updates", False, "Vendor ID number not in dashboard profile")
                            return False
                    else:
                        self.log_test("Dashboard Data Updates", False, f"Missing dashboard fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Dashboard Data Updates", False, "Missing dashboard in response", data)
                    return False
            else:
                self.log_test("Dashboard Data Updates", False, f"Dashboard request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Data Updates", False, f"Dashboard data error: {str(e)}")
            return False
    
    def test_public_verification_with_vendor_id(self):
        """Test public verification using generated Vendor ID"""
        if not self.vendor_id_number:
            self.log_test("Public Verification with Vendor ID", False, "No Vendor ID number available")
            return False
            
        try:
            response = self.make_request("GET", f"/public/verify/{self.vendor_id_number}")
            
            if response.status_code == 200:
                data = response.json()
                if "verification" in data:
                    verification = data["verification"]
                    required_fields = ["vendor_id", "business_name", "verification_status", "trust_score"]
                    missing_fields = [field for field in required_fields if field not in verification]
                    
                    if not missing_fields:
                        self.log_test("Public Verification with Vendor ID", True, "Public verification working with Vendor ID", 
                                    {"vendor_id": verification["vendor_id"], "status": verification["verification_status"]})
                        return True
                    else:
                        self.log_test("Public Verification with Vendor ID", False, f"Missing verification fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Public Verification with Vendor ID", False, "Missing verification in response", data)
                    return False
            else:
                self.log_test("Public Verification with Vendor ID", False, f"Public verification failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Public Verification with Vendor ID", False, f"Public verification error: {str(e)}")
            return False
    
    def test_document_rejection_flow(self):
        """Test document rejection and resubmission process"""
        if not self.admin_token:
            self.log_test("Document Rejection Flow", False, "No admin token available")
            return False
            
        try:
            # Upload a test document to reject
            file_content = self.create_sample_document("business_registration", "Test document for rejection")
            
            files = {
                'file': ('test_rejection.pdf', file_content, 'application/pdf')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            upload_response = self.make_request("POST", "/vendors/documents/upload", data=data, files=files, token=self.vendor_token)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                document_id = upload_data["document_id"]
                
                # Reject the document
                rejection_data = {
                    "reason": "Document quality is poor and text is not clearly visible. Please resubmit with a clearer copy."
                }
                
                reject_response = self.make_request("POST", f"/admin/documents/{document_id}/reject", 
                                                  rejection_data, token=self.admin_token)
                
                if reject_response.status_code == 200:
                    self.log_test("Document Rejection Flow", True, "Document rejection process working correctly")
                    return True
                else:
                    self.log_test("Document Rejection Flow", False, f"Document rejection failed: {reject_response.text}")
                    return False
            else:
                self.log_test("Document Rejection Flow", False, f"Test document upload failed: {upload_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Rejection Flow", False, f"Document rejection flow error: {str(e)}")
            return False
    
    def test_admin_permission_protection(self):
        """Test admin endpoint permission protection"""
        try:
            # Try to access admin endpoint with vendor token
            response = self.make_request("GET", "/admin/verification-queue", token=self.vendor_token)
            
            if response.status_code == 403:
                self.log_test("Admin Permission Protection", True, "Admin endpoints properly protected from vendor access")
                return True
            else:
                self.log_test("Admin Permission Protection", False, f"Admin endpoint accessible with vendor token: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Permission Protection", False, f"Permission protection test error: {str(e)}")
            return False
    
    def run_comprehensive_onboarding_tests(self):
        """Run comprehensive vendor onboarding and verification workflow tests"""
        print("🚀 Starting Comprehensive Vendor Onboarding & Verification Workflow Tests")
        print("=" * 80)
        
        # Phase 1: Setup and Authentication
        print("\n📋 PHASE 1: SETUP AND AUTHENTICATION")
        print("-" * 50)
        self.test_health_check()
        self.test_vendor_registration()
        self.test_admin_registration()
        
        # Phase 2: Vendor Profile Creation
        print("\n👤 PHASE 2: VENDOR PROFILE CREATION")
        print("-" * 50)
        self.test_vendor_profile_creation()
        
        # Phase 3: Document Upload System
        print("\n📄 PHASE 3: DOCUMENT UPLOAD SYSTEM")
        print("-" * 50)
        self.test_document_upload_business_registration()
        self.test_document_upload_tax_id()
        self.test_document_upload_government_id()
        self.test_document_validation()
        
        # Phase 4: Admin Verification Workflow
        print("\n🔍 PHASE 4: ADMIN VERIFICATION WORKFLOW")
        print("-" * 50)
        self.test_admin_verification_queue()
        self.test_admin_document_review()
        self.test_admin_document_approval()
        
        # Phase 5: Vendor ID Generation System
        print("\n🆔 PHASE 5: VENDOR ID GENERATION SYSTEM")
        print("-" * 50)
        self.test_vendor_id_generation()
        self.test_qr_code_generation()
        self.test_digital_card_creation()
        
        # Phase 6: Vendor ID Management
        print("\n💳 PHASE 6: VENDOR ID MANAGEMENT")
        print("-" * 50)
        self.test_physical_card_request()
        self.test_trust_score_update()
        
        # Phase 7: Status Updates and Integration
        print("\n🔄 PHASE 7: STATUS UPDATES AND INTEGRATION")
        print("-" * 50)
        self.test_verification_status_updates()
        self.test_dashboard_data_updates()
        self.test_public_verification_with_vendor_id()
        
        # Phase 8: Edge Cases and Security
        print("\n🛡️ PHASE 8: EDGE CASES AND SECURITY")
        print("-" * 50)
        self.test_document_rejection_flow()
        self.test_admin_permission_protection()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        # Group results by phase
        phases = {
            "Setup and Authentication": ["Health Check", "Vendor Registration", "Admin Registration"],
            "Vendor Profile": ["Vendor Profile Creation", "Get Existing Profile"],
            "Document Upload": ["Document Upload - Business Registration", "Document Upload - Tax ID", "Document Upload - Government ID", "Document Validation"],
            "Admin Verification": ["Admin Verification Queue", "Admin Document Review", "Admin Document Approval"],
            "Vendor ID System": ["Vendor ID Generation", "QR Code Generation", "Digital Card Creation"],
            "ID Management": ["Physical Card Request", "Trust Score Update"],
            "Status Updates": ["Verification Status Updates", "Dashboard Data Updates", "Public Verification with Vendor ID"],
            "Security & Edge Cases": ["Document Rejection Flow", "Admin Permission Protection"]
        }
        
        print("\n📋 RESULTS BY PHASE:")
        for phase, test_names in phases.items():
            phase_results = [r for r in self.test_results if any(name in r["test"] for name in test_names)]
            if phase_results:
                phase_passed = sum(1 for r in phase_results if r["success"])
                phase_total = len(phase_results)
                print(f"  {phase}: {phase_passed}/{phase_total} ({'✅' if phase_passed == phase_total else '❌'})")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Final assessment
        if passed == len(self.test_results):
            print("🎉 ALL TESTS PASSED! Vendor onboarding and verification workflow is fully functional.")
        elif passed >= len(self.test_results) * 0.8:
            print("⚠️  Most tests passed, but some issues need attention.")
        else:
            print("❌ Multiple critical issues found. System needs significant fixes.")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = VendorOnboardingTester()
    tester.run_comprehensive_onboarding_tests()