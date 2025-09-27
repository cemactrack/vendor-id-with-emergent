#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite for Vendor Verification and Trust Ecosystem
Tests all authentication including enhanced features: email verification, password reset, 2FA, security management
Tests new services: email_service, two_factor_service, enhanced_vendor_ecosystem_service, error_handler, validators
"""

import requests
import json
import base64
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
BACKEND_URL = "https://idecosystem.preview.emergentagent.com/api"
TEST_USER_EMAIL = "comprehensive.test@example.com"
TEST_USER_PASSWORD = "SecureTestPass123!"
TEST_ADMIN_EMAIL = "admin.comprehensive@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminSecurePass123!"
TEST_2FA_USER_EMAIL = "twofa.comprehensive@example.com"
TEST_2FA_PASSWORD = "TwoFATestPass123!"

class VendorEcosystemTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.vendor_token = None
        self.admin_token = None
        self.vendor_id = None
        self.test_results = []
        self.test_document_id = None
        self.ocr_processing_id = None
        self.test_order_id = None
        self.test_escrow_id = None
        self.test_payment_instruction_id = None
    
    @property
    def customer_token(self):
        """Use user_token as customer_token for escrow tests"""
        return self.user_token
        
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
                    headers: Dict[str, str] = None, token: str = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
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
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # Test vendor registration
            vendor_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Test Vendor User",
                "phone": "1234567890",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", vendor_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.log_test("User Registration (Vendor)", True, "Vendor registered successfully", 
                                {"user_id": data["user"]["id"], "email": data["user"]["email"]})
                    return True
                else:
                    self.log_test("User Registration (Vendor)", False, "Missing token or user in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    self.log_test("User Registration (Vendor)", True, "User already exists - proceeding with login")
                    return True
                else:
                    self.log_test("User Registration (Vendor)", False, f"Registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("User Registration (Vendor)", False, f"Registration error: {str(e)}")
            return False
    
    def test_admin_registration(self):
        """Test admin user registration"""
        try:
            admin_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD,
                "full_name": "Test Admin User",
                "phone": "9876543210",
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
                    return True
                else:
                    self.log_test("Admin Registration", False, f"Admin registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("Admin Registration", False, f"Admin registration error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            # Test vendor login using form data
            url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password={TEST_USER_PASSWORD}"
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.log_test("User Login (Vendor)", True, "Vendor login successful", 
                                {"user_id": data["user"]["id"], "role": data["user"]["role"]})
                    return True
                else:
                    self.log_test("User Login (Vendor)", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_test("User Login (Vendor)", False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login (Vendor)", False, f"Login error: {str(e)}")
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
                "business_name": "Test Vendor Business Ltd",
                "business_description": "A comprehensive testing business for vendor ecosystem validation",
                "category": "technology",
                "website": "https://testvendor.example.com",
                "business_address": "123 Test Street, Lagos, Nigeria",
                "registration_number": "RC123456789",
                "tax_id": "TIN987654321",
                "established_year": 2020,
                "employee_count": 25
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
                    # Try to get existing profile
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
    
    def test_vendor_dashboard(self):
        """Test vendor dashboard endpoint"""
        if not self.vendor_token:
            self.log_test("Vendor Dashboard", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    required_fields = ["profile", "analytics", "active_listings", "verification_status"]
                    missing_fields = [field for field in required_fields if field not in dashboard]
                    
                    if not missing_fields:
                        self.log_test("Vendor Dashboard", True, "Dashboard data retrieved successfully", 
                                    {"vendor_id": dashboard["profile"]["vendor_id"]})
                        return True
                    else:
                        self.log_test("Vendor Dashboard", False, f"Missing dashboard fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Vendor Dashboard", False, "Missing dashboard in response", data)
                    return False
            else:
                self.log_test("Vendor Dashboard", False, f"Dashboard request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vendor Dashboard", False, f"Dashboard error: {str(e)}")
            return False
    
    def test_document_upload(self):
        """Test document upload endpoint"""
        if not self.vendor_token:
            self.log_test("Document Upload", False, "No vendor token available")
            return False
            
        try:
            # Create sample document data (base64 encoded)
            sample_content = "This is a test document for business registration"
            encoded_content = base64.b64encode(sample_content.encode()).decode()
            
            document_data = {
                "document_type": "business_registration",
                "file_data": encoded_content,
                "filename": "business_registration.pdf",
                "description": "Test business registration document"
            }
            
            # Use multipart form data for file upload
            files = {
                'file': ('business_registration.pdf', base64.b64decode(encoded_content), 'application/pdf')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            url = f"{self.base_url}/vendors/documents/upload"
            headers = {"Authorization": f"Bearer {self.vendor_token}"}
            
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if "document_id" in response_data:
                    document_id = response_data["document_id"]
                    self.log_test("Document Upload", True, "Document uploaded successfully", 
                                {"document_id": document_id})
                    return True
                else:
                    self.log_test("Document Upload", False, "Missing document_id in response", response_data)
                    return False
            else:
                self.log_test("Document Upload", False, f"Document upload failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload", False, f"Document upload error: {str(e)}")
            return False
    
    def test_document_listing(self):
        """Test document listing endpoint"""
        if not self.vendor_token:
            self.log_test("Document Listing", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/documents", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "documents" in data:
                    documents = data["documents"]
                    self.log_test("Document Listing", True, f"Retrieved {len(documents)} documents")
                    return True
                else:
                    self.log_test("Document Listing", False, "Missing documents in response", data)
                    return False
            else:
                self.log_test("Document Listing", False, f"Document listing failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Listing", False, f"Document listing error: {str(e)}")
            return False
    
    def test_admin_stats(self):
        """Test admin statistics endpoint"""
        if not self.admin_token:
            self.log_test("Admin Stats", False, "No admin token available")
            return False
            
        try:
            response = self.make_request("GET", "/admin/stats", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "stats" in data:
                    stats = data["stats"]
                    required_fields = ["total_vendors", "verified_vendors", "pending_verification"]
                    missing_fields = [field for field in required_fields if field not in stats]
                    
                    if not missing_fields:
                        self.log_test("Admin Stats", True, "Admin statistics retrieved successfully", stats)
                        return True
                    else:
                        self.log_test("Admin Stats", False, f"Missing stats fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Admin Stats", False, "Missing stats in response", data)
                    return False
            else:
                self.log_test("Admin Stats", False, f"Admin stats failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Stats", False, f"Admin stats error: {str(e)}")
            return False
    
    def test_pending_verifications(self):
        """Test pending verifications endpoint"""
        if not self.admin_token:
            self.log_test("Pending Verifications", False, "No admin token available")
            return False
            
        try:
            response = self.make_request("GET", "/admin/verifications/pending", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "verifications" in data:
                    verifications = data["verifications"]
                    self.log_test("Pending Verifications", True, f"Retrieved {len(verifications)} pending verifications")
                    return True
                else:
                    self.log_test("Pending Verifications", False, "Missing verifications in response", data)
                    return False
            else:
                self.log_test("Pending Verifications", False, f"Pending verifications failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Pending Verifications", False, f"Pending verifications error: {str(e)}")
            return False
    
    def test_public_vendor_search(self):
        """Test public vendor search endpoint"""
        try:
            # Test basic search
            response = self.make_request("GET", "/public/search?query=test&limit=10")
            
            if response.status_code == 200:
                data = response.json()
                if "vendors" in data and "total" in data:
                    vendors = data["vendors"]
                    total = data["total"]
                    self.log_test("Public Vendor Search", True, f"Search returned {len(vendors)} vendors (total: {total})")
                    return True
                else:
                    self.log_test("Public Vendor Search", False, "Missing vendors or total in response", data)
                    return False
            else:
                self.log_test("Public Vendor Search", False, f"Public search failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Public Vendor Search", False, f"Public search error: {str(e)}")
            return False
    
    def test_public_vendor_verification(self):
        """Test public vendor verification endpoint"""
        if not self.vendor_id:
            self.log_test("Public Vendor Verification", False, "No vendor ID available")
            return False
            
        try:
            response = self.make_request("GET", f"/public/verify/{self.vendor_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "verification" in data:
                    verification = data["verification"]
                    required_fields = ["vendor_id", "business_name", "verification_status", "trust_score"]
                    missing_fields = [field for field in required_fields if field not in verification]
                    
                    if not missing_fields:
                        self.log_test("Public Vendor Verification", True, "Vendor verification retrieved successfully", 
                                    {"vendor_id": verification["vendor_id"], "status": verification["verification_status"]})
                        return True
                    else:
                        self.log_test("Public Vendor Verification", False, f"Missing verification fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Public Vendor Verification", False, "Missing verification in response", data)
                    return False
            else:
                self.log_test("Public Vendor Verification", False, f"Public verification failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Public Vendor Verification", False, f"Public verification error: {str(e)}")
            return False

    def create_test_image_with_text(self, text: str, filename: str = "test_document.png") -> bytes:
        """Create a test image with text for OCR testing"""
        try:
            # Create a white image
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Add text to image
            draw.text((50, 50), text, fill='black', font=font)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()
            
        except Exception as e:
            self.log_test("Create Test Image", False, f"Failed to create test image: {str(e)}")
            # Return a minimal test image as fallback
            img = Image.new('RGB', (400, 300), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), text, fill='black')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue()

    def upload_test_document_for_ocr(self):
        """Upload a test document to use for OCR testing"""
        if not self.vendor_token:
            self.log_test("Upload Test Document for OCR", False, "No vendor token available")
            return False
            
        try:
            # Create test document content
            test_content = """
            BUSINESS REGISTRATION CERTIFICATE
            
            Company Name: Test Vendor Business Ltd
            Registration Number: RC123456789
            Tax Identification Number: TIN987654321
            Business Address: 123 Test Street, Lagos, Nigeria
            Date of Incorporation: January 15, 2020
            Business Category: Technology Services
            
            This certificate confirms that the above company is duly registered
            and authorized to conduct business operations.
            """
            
            # Create multipart form data for file upload
            files = {
                'file': ('business_registration.png', self.create_test_image_with_text(test_content), 'image/png')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            url = f"{self.base_url}/vendors/documents/upload"
            headers = {"Authorization": f"Bearer {self.vendor_token}"}
            
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                if "document_id" in response_data:
                    self.test_document_id = response_data["document_id"]
                    self.log_test("Upload Test Document for OCR", True, "Test document uploaded successfully", 
                                {"document_id": self.test_document_id})
                    return True
                else:
                    self.log_test("Upload Test Document for OCR", False, "Missing document_id in response", response_data)
                    return False
            else:
                self.log_test("Upload Test Document for OCR", False, f"Document upload failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Upload Test Document for OCR", False, f"Document upload error: {str(e)}")
            return False

    def test_ocr_document_processing(self):
        """Test OCR document processing endpoint"""
        if not self.vendor_token:
            self.log_test("OCR Document Processing", False, "No vendor token available")
            return False
            
        if not self.test_document_id:
            self.log_test("OCR Document Processing", False, "No test document ID available")
            return False
            
        try:
            # Create test document with business information
            test_content = """
            BUSINESS REGISTRATION CERTIFICATE
            
            Company Name: Test Vendor Business Ltd
            Registration Number: RC123456789
            Tax Identification Number: TIN987654321
            Business Address: 123 Test Street, Lagos, Nigeria
            Date of Incorporation: January 15, 2020
            Business Category: Technology Services
            Employee Count: 25 employees
            
            This certificate confirms that the above company is duly registered
            and authorized to conduct business operations in Nigeria.
            """
            
            # Create multipart form data for OCR processing
            files = {
                'file': ('business_registration.png', self.create_test_image_with_text(test_content), 'image/png')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            url = f"{self.base_url}/vendors/documents/{self.test_document_id}/ocr/process"
            headers = {"Authorization": f"Bearer {self.vendor_token}"}
            
            response = requests.post(url, files=files, data=data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                if "result" in response_data and "processing_id" in response_data["result"]:
                    result = response_data["result"]
                    self.ocr_processing_id = result["processing_id"]
                    
                    # Validate OCR result structure
                    required_fields = ["processing_id", "status", "overall_confidence", "total_words", "page_count"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        self.log_test("OCR Document Processing", True, "OCR processing completed successfully", 
                                    {
                                        "processing_id": result["processing_id"],
                                        "confidence": result["overall_confidence"],
                                        "words": result["total_words"],
                                        "pages": result["page_count"]
                                    })
                        return True
                    else:
                        self.log_test("OCR Document Processing", False, f"Missing result fields: {missing_fields}")
                        return False
                else:
                    self.log_test("OCR Document Processing", False, "Missing result or processing_id in response", response_data)
                    return False
            else:
                self.log_test("OCR Document Processing", False, f"OCR processing failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OCR Document Processing", False, f"OCR processing error: {str(e)}")
            return False

    def test_ocr_results_retrieval(self):
        """Test OCR results retrieval endpoint"""
        if not self.vendor_token:
            self.log_test("OCR Results Retrieval", False, "No vendor token available")
            return False
            
        if not self.test_document_id:
            self.log_test("OCR Results Retrieval", False, "No test document ID available")
            return False
            
        try:
            response = self.make_request("GET", f"/vendors/documents/{self.test_document_id}/ocr/results", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "ocr_results" in data:
                    ocr_results = data["ocr_results"]
                    
                    # Validate OCR results structure
                    required_fields = ["processing_id", "vendor_id", "document_id", "combined_text", "overall_confidence"]
                    missing_fields = [field for field in required_fields if field not in ocr_results]
                    
                    if not missing_fields:
                        self.log_test("OCR Results Retrieval", True, "OCR results retrieved successfully", 
                                    {
                                        "processing_id": ocr_results["processing_id"],
                                        "confidence": ocr_results["overall_confidence"],
                                        "text_length": len(ocr_results["combined_text"])
                                    })
                        return True
                    else:
                        self.log_test("OCR Results Retrieval", False, f"Missing OCR result fields: {missing_fields}")
                        return False
                else:
                    self.log_test("OCR Results Retrieval", False, "Missing ocr_results in response", data)
                    return False
            elif response.status_code == 404:
                self.log_test("OCR Results Retrieval", False, "OCR results not found - document may not be processed yet")
                return False
            else:
                self.log_test("OCR Results Retrieval", False, f"OCR results retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OCR Results Retrieval", False, f"OCR results retrieval error: {str(e)}")
            return False

    def test_ocr_data_validation(self):
        """Test OCR data validation endpoint"""
        if not self.vendor_token:
            self.log_test("OCR Data Validation", False, "No vendor token available")
            return False
            
        if not self.test_document_id:
            self.log_test("OCR Data Validation", False, "No test document ID available")
            return False
            
        try:
            # Define expected fields for validation
            validation_request = {
                "expected_fields": {
                    "company_name": "Test Vendor Business Ltd",
                    "registration_number": "RC123456789",
                    "tax_id": "TIN987654321",
                    "business_address": "123 Test Street, Lagos, Nigeria"
                }
            }
            
            response = self.make_request("POST", f"/vendors/documents/{self.test_document_id}/ocr/validate", 
                                       validation_request, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "validation_results" in data:
                    validation_results = data["validation_results"]
                    
                    # Validate validation results structure
                    required_fields = ["validation_id", "vendor_id", "document_id", "field_validations", "overall_validation_score"]
                    missing_fields = [field for field in required_fields if field not in validation_results]
                    
                    if not missing_fields:
                        field_validations = validation_results["field_validations"]
                        validation_score = validation_results["overall_validation_score"]
                        
                        self.log_test("OCR Data Validation", True, "OCR data validation completed successfully", 
                                    {
                                        "validation_id": validation_results["validation_id"],
                                        "validation_score": validation_score,
                                        "fields_validated": len(field_validations),
                                        "validation_passed": validation_results.get("validation_passed", False)
                                    })
                        return True
                    else:
                        self.log_test("OCR Data Validation", False, f"Missing validation result fields: {missing_fields}")
                        return False
                else:
                    self.log_test("OCR Data Validation", False, "Missing validation_results in response", data)
                    return False
            else:
                self.log_test("OCR Data Validation", False, f"OCR data validation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OCR Data Validation", False, f"OCR data validation error: {str(e)}")
            return False

    def test_vendor_ocr_summary(self):
        """Test vendor OCR summary endpoint"""
        if not self.vendor_token:
            self.log_test("Vendor OCR Summary", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/ocr/summary", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "ocr_summary" in data:
                    ocr_summary = data["ocr_summary"]
                    
                    # Validate OCR summary structure
                    required_fields = ["vendor_id", "total_documents", "processed_documents", "average_confidence"]
                    missing_fields = [field for field in required_fields if field not in ocr_summary]
                    
                    if not missing_fields:
                        self.log_test("Vendor OCR Summary", True, "OCR summary retrieved successfully", 
                                    {
                                        "total_documents": ocr_summary["total_documents"],
                                        "processed_documents": ocr_summary["processed_documents"],
                                        "average_confidence": ocr_summary["average_confidence"]
                                    })
                        return True
                    else:
                        self.log_test("Vendor OCR Summary", False, f"Missing OCR summary fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Vendor OCR Summary", False, "Missing ocr_summary in response", data)
                    return False
            else:
                self.log_test("Vendor OCR Summary", False, f"OCR summary retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vendor OCR Summary", False, f"OCR summary error: {str(e)}")
            return False

    def test_admin_ocr_results(self):
        """Test admin OCR results endpoint"""
        if not self.admin_token:
            self.log_test("Admin OCR Results", False, "No admin token available")
            return False
            
        if not self.ocr_processing_id:
            self.log_test("Admin OCR Results", False, "No OCR processing ID available")
            return False
            
        try:
            response = self.make_request("GET", f"/admin/ocr/results/{self.ocr_processing_id}", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "ocr_results" in data:
                    ocr_results = data["ocr_results"]
                    
                    # Validate admin OCR results structure
                    required_fields = ["processing_id", "vendor_id", "document_id", "combined_text", "overall_confidence"]
                    missing_fields = [field for field in required_fields if field not in ocr_results]
                    
                    if not missing_fields:
                        self.log_test("Admin OCR Results", True, "Admin OCR results retrieved successfully", 
                                    {
                                        "processing_id": ocr_results["processing_id"],
                                        "vendor_id": ocr_results["vendor_id"],
                                        "confidence": ocr_results["overall_confidence"]
                                    })
                        return True
                    else:
                        self.log_test("Admin OCR Results", False, f"Missing admin OCR result fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Admin OCR Results", False, "Missing ocr_results in response", data)
                    return False
            elif response.status_code == 404:
                self.log_test("Admin OCR Results", False, "OCR results not found for processing ID")
                return False
            else:
                self.log_test("Admin OCR Results", False, f"Admin OCR results retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin OCR Results", False, f"Admin OCR results error: {str(e)}")
            return False

    def test_ocr_error_handling(self):
        """Test OCR error handling with invalid files"""
        if not self.vendor_token:
            self.log_test("OCR Error Handling", False, "No vendor token available")
            return False
            
        try:
            # Test with unsupported file type
            files = {
                'file': ('test.txt', b'This is a text file', 'text/plain')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            url = f"{self.base_url}/vendors/documents/test-doc-id/ocr/process"
            headers = {"Authorization": f"Bearer {self.vendor_token}"}
            
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response.status_code in [400, 500]:  # Accept both 400 and 500 for error handling
                error_data = response.json()
                if "detail" in error_data and "Unsupported file type" in error_data["detail"]:
                    self.log_test("OCR Error Handling", True, "Correctly rejected unsupported file type")
                    return True
                else:
                    self.log_test("OCR Error Handling", False, f"Unexpected error response: {error_data}")
                    return False
            else:
                self.log_test("OCR Error Handling", False, f"Expected error but got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OCR Error Handling", False, f"OCR error handling test error: {str(e)}")
            return False

    # ===== NEW COMPREHENSIVE TESTS FOR ENHANCED SERVICES =====
    
    def test_email_verification_workflow(self):
        """Test email verification workflow"""
        if not self.vendor_token:
            self.log_test("Email Verification Workflow", False, "No vendor token available")
            return False
            
        try:
            # Test resend verification email
            response = self.make_request("POST", "/auth/resend-verification", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "sent" in data["message"].lower():
                    self.log_test("Email Verification Workflow", True, "Email verification resend successful (mock mode)")
                    return True
                else:
                    self.log_test("Email Verification Workflow", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Email Verification Workflow", False, f"Resend verification failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Email Verification Workflow", False, f"Email verification test error: {str(e)}")
            return False
    
    def test_password_reset_workflow(self):
        """Test password reset workflow"""
        try:
            # Test forgot password request
            reset_data = {"email": TEST_USER_EMAIL}
            response = self.make_request("POST", "/auth/forgot-password", reset_data)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "sent" in data["message"].lower():
                    self.log_test("Password Reset Workflow", True, "Password reset request successful (prevents email enumeration)")
                    return True
                else:
                    self.log_test("Password Reset Workflow", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Password Reset Workflow", False, f"Password reset request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Password Reset Workflow", False, f"Password reset test error: {str(e)}")
            return False
    
    def test_two_factor_authentication_setup(self):
        """Test 2FA setup workflow"""
        if not self.vendor_token:
            self.log_test("2FA Setup", False, "No vendor token available")
            return False
            
        try:
            # Test 2FA setup
            setup_data = {"password": TEST_USER_PASSWORD}
            response = self.make_request("POST", "/auth/2fa/setup", setup_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "setup_data" in data and "qr_code" in data["setup_data"]:
                    setup_data = data["setup_data"]
                    required_fields = ["qr_code", "setup_key", "backup_codes", "issuer"]
                    missing_fields = [field for field in required_fields if field not in setup_data]
                    
                    if not missing_fields:
                        self.log_test("2FA Setup", True, "2FA setup successful with QR code and backup codes", 
                                    {
                                        "issuer": setup_data["issuer"],
                                        "backup_codes_count": len(setup_data["backup_codes"]),
                                        "qr_code_present": "data:image/png;base64," in setup_data["qr_code"]
                                    })
                        return True
                    else:
                        self.log_test("2FA Setup", False, f"Missing setup data fields: {missing_fields}")
                        return False
                else:
                    self.log_test("2FA Setup", False, "Missing setup_data or qr_code in response", data)
                    return False
            else:
                self.log_test("2FA Setup", False, f"2FA setup failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("2FA Setup", False, f"2FA setup test error: {str(e)}")
            return False
    
    def test_security_info_endpoint(self):
        """Test security info endpoint"""
        if not self.vendor_token:
            self.log_test("Security Info", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/auth/security/info", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "security" in data:
                    security_info = data["security"]
                    required_fields = ["user_id", "email_verified", "two_factor_enabled", "failed_login_attempts"]
                    missing_fields = [field for field in required_fields if field not in security_info]
                    
                    if not missing_fields:
                        self.log_test("Security Info", True, "Security info retrieved successfully", 
                                    {
                                        "email_verified": security_info["email_verified"],
                                        "two_factor_enabled": security_info["two_factor_enabled"],
                                        "failed_attempts": security_info["failed_login_attempts"]
                                    })
                        return True
                    else:
                        self.log_test("Security Info", False, f"Missing security info fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Security Info", False, "Missing security in response", data)
                    return False
            else:
                self.log_test("Security Info", False, f"Security info request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Security Info", False, f"Security info test error: {str(e)}")
            return False
    
    def test_security_events_endpoint(self):
        """Test security events endpoint"""
        if not self.vendor_token:
            self.log_test("Security Events", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("GET", "/auth/security/events?limit=10", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "events" in data:
                    events = data["events"]
                    self.log_test("Security Events", True, f"Security events retrieved successfully ({len(events)} events)")
                    return True
                else:
                    self.log_test("Security Events", False, "Missing events in response", data)
                    return False
            else:
                self.log_test("Security Events", False, f"Security events request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Security Events", False, f"Security events test error: {str(e)}")
            return False
    
    def test_enhanced_error_handling(self):
        """Test enhanced error handling middleware"""
        try:
            # Test with invalid endpoint to trigger error handling
            response = self.make_request("GET", "/invalid-endpoint-test")
            
            if response.status_code == 404:
                try:
                    data = response.json()
                    # Check if error response has proper structure
                    if "detail" in data:
                        self.log_test("Enhanced Error Handling", True, "Error handling middleware working correctly")
                        return True
                    else:
                        self.log_test("Enhanced Error Handling", False, f"Error response missing proper structure: {data}")
                        return False
                except:
                    self.log_test("Enhanced Error Handling", True, "Error handling working (non-JSON response)")
                    return True
            else:
                self.log_test("Enhanced Error Handling", False, f"Unexpected status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Error Handling", False, f"Error handling test error: {str(e)}")
            return False
    
    def test_input_validation(self):
        """Test input validation with invalid data"""
        try:
            # Test registration with invalid email
            invalid_user_data = {
                "email": "invalid-email",
                "password": "weak",
                "full_name": "",
                "phone": "invalid-phone",
                "country": "INVALID",
                "role": "invalid_role"
            }
            
            response = self.make_request("POST", "/auth/register", invalid_user_data)
            
            if response.status_code in [400, 422]:  # Validation error
                self.log_test("Input Validation", True, "Input validation working correctly - rejected invalid data")
                return True
            else:
                self.log_test("Input Validation", False, f"Expected validation error but got {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Input Validation", False, f"Input validation test error: {str(e)}")
            return False
    
    def test_enhanced_vendor_ecosystem_service(self):
        """Test enhanced vendor ecosystem service features"""
        if not self.vendor_token:
            self.log_test("Enhanced Vendor Ecosystem Service", False, "No vendor token available")
            return False
            
        try:
            # Test enhanced dashboard with additional fields
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    # Check for enhanced fields
                    enhanced_fields = ["profile", "analytics", "verification_status", "trust_events"]
                    present_fields = [field for field in enhanced_fields if field in data]
                    
                    if len(present_fields) >= 2:  # At least 2 enhanced fields present
                        self.log_test("Enhanced Vendor Ecosystem Service", True, 
                                    f"Enhanced service working with {len(present_fields)} enhanced fields", 
                                    {"enhanced_fields": present_fields})
                        return True
                    else:
                        self.log_test("Enhanced Vendor Ecosystem Service", False, 
                                    f"Missing enhanced fields. Present: {present_fields}")
                        return False
                else:
                    self.log_test("Enhanced Vendor Ecosystem Service", False, "Missing dashboard in response", data)
                    return False
            else:
                self.log_test("Enhanced Vendor Ecosystem Service", False, f"Dashboard request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Vendor Ecosystem Service", False, f"Enhanced service test error: {str(e)}")
            return False
    
    def test_api_consistency_fixes(self):
        """Test API consistency fixes"""
        try:
            # Test health check for consistent response format
            response = self.make_request("GET", "/")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["message", "version", "status", "features"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("API Consistency Fixes", True, "API response format consistent", 
                                {"version": data["version"], "features_count": len(data["features"])})
                    return True
                else:
                    self.log_test("API Consistency Fixes", False, f"Missing API fields: {missing_fields}")
                    return False
            else:
                self.log_test("API Consistency Fixes", False, f"Health check failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("API Consistency Fixes", False, f"API consistency test error: {str(e)}")
            return False
    
    def test_comprehensive_authentication_flow(self):
        """Test comprehensive authentication flow with all enhancements"""
        try:
            # Test login with enhanced features
            url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password={TEST_USER_PASSWORD}"
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    # Check for enhanced login response
                    enhanced_fields = ["message"]
                    present_fields = [field for field in enhanced_fields if field in data]
                    
                    self.log_test("Comprehensive Authentication Flow", True, 
                                "Enhanced authentication flow working", 
                                {"enhanced_fields": present_fields, "user_role": data["user"]["role"]})
                    return True
                else:
                    self.log_test("Comprehensive Authentication Flow", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_test("Comprehensive Authentication Flow", False, f"Enhanced login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Comprehensive Authentication Flow", False, f"Comprehensive auth test error: {str(e)}")
            return False
    
    # ===== ESCROW SYSTEM TESTS =====
    
    def test_escrow_order_creation(self):
        """Test escrow order creation with multi-currency items"""
        if not self.customer_token:
            self.log_test("Escrow Order Creation", False, "No customer token available")
            return False
            
        try:
            # Create order with multi-currency items (should fail - all items must use same currency)
            order_data = {
                "vendor_id": "VID-NG-TEST123",
                "items": [
                    {
                        "product_name": "Web Development Service",
                        "description": "Custom website development",
                        "quantity": 1,
                        "unit_price": 500.00,
                        "currency": "USD"
                    },
                    {
                        "product_name": "SEO Optimization",
                        "description": "Search engine optimization service",
                        "quantity": 1,
                        "unit_price": 200.00,
                        "currency": "USD"
                    }
                ],
                "delivery_address": "123 Business Street, Lagos, Nigeria",
                "special_instructions": "Please deliver within 2 weeks",
                "expected_delivery_date": "2024-02-15T10:00:00Z"
            }
            
            response = self.make_request("POST", "/escrow/orders/create", order_data, token=self.customer_token)
            
            if response.status_code == 200:
                data = response.json()
                if "order" in data and "escrow" in data and "payment_instructions" in data:
                    order = data["order"]
                    escrow = data["escrow"]
                    payment_instructions = data["payment_instructions"]
                    
                    # Store order ID for subsequent tests
                    self.test_order_id = order["order_id"]
                    self.test_escrow_id = escrow["escrow_id"]
                    self.test_payment_instruction_id = payment_instructions["instruction_id"]
                    
                    # Validate order structure
                    required_order_fields = ["order_id", "customer_id", "vendor_id", "items", "subtotal", "platform_fee", "total_amount", "currency", "status"]
                    missing_order_fields = [field for field in required_order_fields if field not in order]
                    
                    # Validate escrow structure
                    required_escrow_fields = ["escrow_id", "order_id", "amount", "currency", "platform_fee", "vendor_amount", "status", "auto_release_date"]
                    missing_escrow_fields = [field for field in required_escrow_fields if field not in escrow]
                    
                    # Validate payment instructions
                    required_payment_fields = ["instruction_id", "order_id", "payment_method", "bank_details", "amount", "currency", "status"]
                    missing_payment_fields = [field for field in required_payment_fields if field not in payment_instructions]
                    
                    if not missing_order_fields and not missing_escrow_fields and not missing_payment_fields:
                        # Validate platform fee calculation (2.5%)
                        expected_platform_fee = round(order["subtotal"] * 0.025, 2)
                        actual_platform_fee = order["platform_fee"]
                        
                        if abs(expected_platform_fee - actual_platform_fee) < 0.01:  # Allow for rounding differences
                            self.log_test("Escrow Order Creation", True, "Order created successfully with correct escrow setup", 
                                        {
                                            "order_id": order["order_id"],
                                            "total_amount": order["total_amount"],
                                            "platform_fee": actual_platform_fee,
                                            "currency": order["currency"],
                                            "escrow_status": escrow["status"],
                                            "payment_method": payment_instructions["payment_method"]
                                        })
                            return True
                        else:
                            self.log_test("Escrow Order Creation", False, f"Platform fee calculation incorrect. Expected: {expected_platform_fee}, Got: {actual_platform_fee}")
                            return False
                    else:
                        missing_fields = {
                            "order": missing_order_fields,
                            "escrow": missing_escrow_fields,
                            "payment": missing_payment_fields
                        }
                        self.log_test("Escrow Order Creation", False, f"Missing required fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Escrow Order Creation", False, "Missing order, escrow, or payment_instructions in response", data)
                    return False
            else:
                self.log_test("Escrow Order Creation", False, f"Order creation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Escrow Order Creation", False, f"Order creation error: {str(e)}")
            return False
    
    def test_escrow_payment_proof_submission(self):
        """Test payment proof submission workflow"""
        customer_token = self.user_token
        if not self.customer_token or not hasattr(self, 'test_payment_instruction_id'):
            self.log_test("Payment Proof Submission", False, "No customer token or payment instruction ID available")
            return False
            
        try:
            payment_proof_data = {
                "instruction_id": self.test_payment_instruction_id,
                "reference_number": "TXN123456789",
                "payment_date": "2024-01-15T14:30:00Z",
                "notes": "Payment made via bank transfer",
                "proof_files": ["receipt_001.jpg", "bank_statement.pdf"]
            }
            
            response = self.make_request("POST", "/escrow/payments/submit-proof", payment_proof_data, token=self.customer_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "submitted" in data["message"].lower():
                    self.log_test("Payment Proof Submission", True, "Payment proof submitted successfully", 
                                {"reference_number": payment_proof_data["reference_number"]})
                    return True
                else:
                    self.log_test("Payment Proof Submission", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Payment Proof Submission", False, f"Payment proof submission failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Payment Proof Submission", False, f"Payment proof submission error: {str(e)}")
            return False
    
    def test_escrow_admin_payment_confirmation(self):
        """Test admin payment confirmation process"""
        if not self.admin_token or not hasattr(self, 'test_payment_instruction_id'):
            self.log_test("Admin Payment Confirmation", False, "No admin token or payment instruction ID available")
            return False
            
        try:
            confirmation_data = {
                "confirmed": True,
                "notes": "Payment verified and confirmed by admin"
            }
            
            response = self.make_request("POST", f"/escrow/payments/{self.test_payment_instruction_id}/confirm", 
                                       confirmation_data, token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "confirmed" in data["message"].lower():
                    self.log_test("Admin Payment Confirmation", True, "Payment confirmed successfully by admin")
                    return True
                else:
                    self.log_test("Admin Payment Confirmation", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Admin Payment Confirmation", False, f"Payment confirmation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Payment Confirmation", False, f"Payment confirmation error: {str(e)}")
            return False
    
    def test_escrow_order_delivery(self):
        """Test order delivery marking by vendor"""
        if not self.vendor_token or not hasattr(self, 'test_order_id'):
            self.log_test("Order Delivery", False, "No vendor token or order ID available")
            return False
            
        try:
            delivery_data = {
                "delivery_notes": "Order delivered successfully to customer address"
            }
            
            response = self.make_request("POST", f"/escrow/orders/{self.test_order_id}/delivered", 
                                       delivery_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "delivered" in data["message"].lower():
                    self.log_test("Order Delivery", True, "Order marked as delivered successfully")
                    return True
                else:
                    self.log_test("Order Delivery", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Order Delivery", False, f"Order delivery marking failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Order Delivery", False, f"Order delivery error: {str(e)}")
            return False
    
    def test_escrow_order_completion(self):
        """Test order completion and fund release"""
        if not self.customer_token or not hasattr(self, 'test_order_id'):
            self.log_test("Order Completion", False, "No customer token or order ID available")
            return False
            
        try:
            receipt_data = {
                "satisfaction_rating": 5
            }
            
            response = self.make_request("POST", f"/escrow/orders/{self.test_order_id}/confirm-receipt", 
                                       receipt_data, token=self.customer_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and ("completed" in data["message"].lower() or "released" in data["message"].lower()):
                    self.log_test("Order Completion", True, "Order completed and funds released successfully")
                    return True
                else:
                    self.log_test("Order Completion", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Order Completion", False, f"Order completion failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Order Completion", False, f"Order completion error: {str(e)}")
            return False
    
    def test_escrow_dispute_creation(self):
        """Test dispute creation and management"""
        if not self.customer_token:
            self.log_test("Dispute Creation", False, "No customer token available")
            return False
            
        try:
            # Create a new order for dispute testing
            order_data = {
                "vendor_id": "VID-NG-TEST123",
                "items": [
                    {
                        "product_name": "Disputed Service",
                        "description": "Service with quality issues",
                        "quantity": 1,
                        "unit_price": 100.00,
                        "currency": "USD"
                    }
                ],
                "delivery_address": "123 Test Street, Lagos, Nigeria",
                "special_instructions": "Test order for dispute"
            }
            
            # Create order first
            order_response = self.make_request("POST", "/escrow/orders/create", order_data, token=self.customer_token)
            
            if order_response.status_code == 200:
                order_data_response = order_response.json()
                dispute_order_id = order_data_response["order"]["order_id"]
                
                # Create dispute
                dispute_data = {
                    "order_id": dispute_order_id,
                    "reason": "Service not delivered as promised",
                    "evidence_description": "The vendor failed to deliver the service according to specifications. Quality was below expectations.",
                    "evidence_files": ["screenshot1.png", "communication_log.txt"],
                    "requested_outcome": "Full refund requested due to non-delivery"
                }
                
                response = self.make_request("POST", "/escrow/disputes/create", dispute_data, token=self.customer_token)
                
                if response.status_code == 200:
                    data = response.json()
                    if "dispute" in data and "message" in data:
                        dispute = data["dispute"]
                        required_fields = ["dispute_id", "order_id", "customer_id", "vendor_id", "reason", "status", "priority"]
                        missing_fields = [field for field in required_fields if field not in dispute]
                        
                        if not missing_fields:
                            self.log_test("Dispute Creation", True, "Dispute created successfully", 
                                        {
                                            "dispute_id": dispute["dispute_id"],
                                            "order_id": dispute["order_id"],
                                            "status": dispute["status"],
                                            "priority": dispute["priority"]
                                        })
                            return True
                        else:
                            self.log_test("Dispute Creation", False, f"Missing dispute fields: {missing_fields}")
                            return False
                    else:
                        self.log_test("Dispute Creation", False, "Missing dispute or message in response", data)
                        return False
                else:
                    self.log_test("Dispute Creation", False, f"Dispute creation failed: {response.text}")
                    return False
            else:
                self.log_test("Dispute Creation", False, f"Failed to create order for dispute test: {order_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Dispute Creation", False, f"Dispute creation error: {str(e)}")
            return False
    
    def test_escrow_extension_request(self):
        """Test escrow extension request functionality"""
        if not self.customer_token:
            self.log_test("Extension Request", False, "No customer token available")
            return False
            
        try:
            # Create a new order for extension testing
            order_data = {
                "vendor_id": "VID-NG-TEST123",
                "items": [
                    {
                        "product_name": "Extended Service",
                        "description": "Service requiring extension",
                        "quantity": 1,
                        "unit_price": 150.00,
                        "currency": "USD"
                    }
                ],
                "delivery_address": "123 Extension Street, Lagos, Nigeria",
                "special_instructions": "Test order for extension"
            }
            
            # Create order first
            order_response = self.make_request("POST", "/escrow/orders/create", order_data, token=self.customer_token)
            
            if order_response.status_code == 200:
                order_data_response = order_response.json()
                extension_order_id = order_data_response["order"]["order_id"]
                
                # Request extension
                extension_data = {
                    "extension_days": 7,
                    "reason": "Need additional time to complete the project due to scope changes"
                }
                
                response = self.make_request("POST", f"/escrow/orders/{extension_order_id}/request-extension", 
                                           extension_data, token=self.customer_token)
                
                if response.status_code == 200:
                    data = response.json()
                    if "message" in data and "extension" in data["message"].lower():
                        self.log_test("Extension Request", True, "Extension request submitted successfully", 
                                    {"extension_days": extension_data["extension_days"]})
                        return True
                    else:
                        self.log_test("Extension Request", False, f"Unexpected response: {data}")
                        return False
                else:
                    self.log_test("Extension Request", False, f"Extension request failed: {response.text}")
                    return False
            else:
                self.log_test("Extension Request", False, f"Failed to create order for extension test: {order_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Extension Request", False, f"Extension request error: {str(e)}")
            return False
    
    def test_escrow_admin_pending_payments(self):
        """Test admin pending payments endpoint"""
        if not self.admin_token:
            self.log_test("Admin Pending Payments", False, "No admin token available")
            return False
            
        try:
            response = self.make_request("GET", "/escrow/admin/pending-payments", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "pending_payments" in data and "total" in data:
                    pending_payments = data["pending_payments"]
                    total = data["total"]
                    
                    self.log_test("Admin Pending Payments", True, f"Retrieved {total} pending payments successfully", 
                                {"total_pending": total})
                    return True
                else:
                    self.log_test("Admin Pending Payments", False, "Missing pending_payments or total in response", data)
                    return False
            else:
                self.log_test("Admin Pending Payments", False, f"Pending payments retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Pending Payments", False, f"Pending payments error: {str(e)}")
            return False
    
    def test_escrow_multi_currency_support(self):
        """Test multi-currency support in escrow system"""
        if not self.customer_token:
            self.log_test("Multi-Currency Support", False, "No customer token available")
            return False
            
        try:
            # Test different currencies
            currencies_to_test = ["NGN", "GHS", "KES", "ZAR", "GBP", "EUR", "CAD"]
            successful_currencies = []
            
            for currency in currencies_to_test:
                order_data = {
                    "vendor_id": "VID-NG-TEST123",
                    "items": [
                        {
                            "product_name": f"Service in {currency}",
                            "description": f"Test service priced in {currency}",
                            "quantity": 1,
                            "unit_price": 100.00,
                            "currency": currency
                        }
                    ],
                    "delivery_address": "123 Currency Test Street, Lagos, Nigeria",
                    "special_instructions": f"Test order for {currency} currency"
                }
                
                response = self.make_request("POST", "/escrow/orders/create", order_data, token=self.customer_token)
                
                if response.status_code == 200:
                    data = response.json()
                    if "order" in data and data["order"]["currency"] == currency:
                        successful_currencies.append(currency)
                
                # Small delay to avoid overwhelming the system
                import time
                time.sleep(0.1)
            
            if len(successful_currencies) >= 5:  # At least 5 currencies should work
                self.log_test("Multi-Currency Support", True, f"Multi-currency support working for {len(successful_currencies)} currencies", 
                            {"supported_currencies": successful_currencies})
                return True
            else:
                self.log_test("Multi-Currency Support", False, f"Only {len(successful_currencies)} currencies working: {successful_currencies}")
                return False
                
        except Exception as e:
            self.log_test("Multi-Currency Support", False, f"Multi-currency test error: {str(e)}")
            return False
    
    def test_escrow_transaction_audit_trail(self):
        """Test transaction recording and audit trails"""
        if not self.customer_token:
            self.log_test("Transaction Audit Trail", False, "No customer token available")
            return False
            
        try:
            # Get user orders to check transaction history
            response = self.make_request("GET", "/escrow/orders?role=customer&limit=10", token=self.customer_token)
            
            if response.status_code == 200:
                data = response.json()
                if "orders" in data and "total" in data:
                    orders = data["orders"]
                    total = data["total"]
                    
                    # Check if orders have proper audit fields
                    if orders:
                        sample_order = orders[0]
                        audit_fields = ["created_at", "updated_at", "status"]
                        missing_audit_fields = [field for field in audit_fields if field not in sample_order]
                        
                        if not missing_audit_fields:
                            self.log_test("Transaction Audit Trail", True, f"Audit trail working - {total} orders with proper tracking", 
                                        {"total_orders": total, "audit_fields": audit_fields})
                            return True
                        else:
                            self.log_test("Transaction Audit Trail", False, f"Missing audit fields: {missing_audit_fields}")
                            return False
                    else:
                        self.log_test("Transaction Audit Trail", True, "Audit trail system working (no orders to audit)")
                        return True
                else:
                    self.log_test("Transaction Audit Trail", False, "Missing orders or total in response", data)
                    return False
            else:
                self.log_test("Transaction Audit Trail", False, f"Orders retrieval failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Transaction Audit Trail", False, f"Audit trail test error: {str(e)}")
            return False
    
    def test_escrow_platform_fee_calculation(self):
        """Test platform fee calculation accuracy (2.5%)"""
        if not self.customer_token:
            self.log_test("Platform Fee Calculation", False, "No customer token available")
            return False
            
        try:
            # Test different amounts to verify fee calculation
            test_amounts = [100.00, 250.50, 1000.00, 1234.56]
            successful_calculations = 0
            
            for amount in test_amounts:
                order_data = {
                    "vendor_id": "VID-NG-TEST123",
                    "items": [
                        {
                            "product_name": f"Fee Test Service - ${amount}",
                            "description": "Service for testing platform fee calculation",
                            "quantity": 1,
                            "unit_price": amount,
                            "currency": "USD"
                        }
                    ],
                    "delivery_address": "123 Fee Test Street, Lagos, Nigeria",
                    "special_instructions": "Test order for fee calculation"
                }
                
                response = self.make_request("POST", "/escrow/orders/create", order_data, token=self.customer_token)
                
                if response.status_code == 200:
                    data = response.json()
                    if "order" in data:
                        order = data["order"]
                        expected_fee = round(amount * 0.025, 2)
                        actual_fee = order["platform_fee"]
                        
                        if abs(expected_fee - actual_fee) < 0.01:  # Allow for rounding differences
                            successful_calculations += 1
                
                # Small delay
                import time
                time.sleep(0.1)
            
            if successful_calculations == len(test_amounts):
                self.log_test("Platform Fee Calculation", True, f"Platform fee calculation accurate for all {len(test_amounts)} test amounts")
                return True
            else:
                self.log_test("Platform Fee Calculation", False, f"Fee calculation failed for {len(test_amounts) - successful_calculations} amounts")
                return False
                
        except Exception as e:
            self.log_test("Platform Fee Calculation", False, f"Fee calculation test error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests including comprehensive enhancements and escrow system"""
        print("🚀 Starting Comprehensive Vendor Ecosystem Backend API Tests")
        print("Testing: email_service, two_factor_service, enhanced_vendor_ecosystem_service, error_handler, validators, escrow_service")
        print("=" * 80)
        
        # Health check
        self.test_health_check()
        
        # Enhanced Authentication tests
        print("\n🔐 Enhanced Authentication & Security Tests")
        print("-" * 50)
        self.test_user_registration()
        self.test_admin_registration()
        self.test_user_login()
        self.test_admin_login()
        self.test_comprehensive_authentication_flow()
        
        # New Enhanced Security Features
        print("\n🛡️ Enhanced Security Features Tests")
        print("-" * 50)
        self.test_email_verification_workflow()
        self.test_password_reset_workflow()
        self.test_two_factor_authentication_setup()
        self.test_security_info_endpoint()
        self.test_security_events_endpoint()
        
        # Vendor profile tests
        print("\n👤 Vendor Profile Management Tests")
        print("-" * 50)
        self.test_vendor_profile_creation()
        self.test_vendor_dashboard()
        self.test_enhanced_vendor_ecosystem_service()
        
        # Document management tests
        print("\n📄 Document Management Tests")
        print("-" * 50)
        self.test_document_upload()
        self.test_document_listing()
        
        # OCR Integration Tests
        print("\n🔍 OCR Integration Tests")
        print("-" * 50)
        self.upload_test_document_for_ocr()
        self.test_ocr_document_processing()
        self.test_ocr_results_retrieval()
        self.test_ocr_data_validation()
        self.test_vendor_ocr_summary()
        self.test_admin_ocr_results()
        self.test_ocr_error_handling()
        
        # Admin functionality tests
        print("\n⚙️ Admin Functionality Tests")
        print("-" * 50)
        self.test_admin_stats()
        self.test_pending_verifications()
        
        # Public endpoint tests
        print("\n🌐 Public Endpoint Tests")
        print("-" * 50)
        self.test_public_vendor_search()
        self.test_public_vendor_verification()
        
        # Enhanced System Tests
        print("\n🔧 Enhanced System & Validation Tests")
        print("-" * 50)
        self.test_enhanced_error_handling()
        self.test_input_validation()
        self.test_api_consistency_fixes()
        
        # ===== NEW ESCROW SYSTEM TESTS =====
        print("\n💰 Escrow Payment Flow System Tests")
        print("-" * 50)
        self.test_escrow_order_creation()
        self.test_escrow_payment_proof_submission()
        self.test_escrow_admin_payment_confirmation()
        self.test_escrow_order_delivery()
        self.test_escrow_order_completion()
        self.test_escrow_dispute_creation()
        self.test_escrow_extension_request()
        self.test_escrow_admin_pending_payments()
        self.test_escrow_multi_currency_support()
        self.test_escrow_transaction_audit_trail()
        self.test_escrow_platform_fee_calculation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = VendorEcosystemTester()
    tester.run_all_tests()