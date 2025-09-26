#!/usr/bin/env python3
"""
Backend API Testing Suite for Vendor Verification and Trust Ecosystem
Tests all authentication, vendor profile, document, admin, and public endpoints
"""

import requests
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://vendorsecure.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testvendor@example.com"
TEST_USER_PASSWORD = "SecurePass123"
TEST_ADMIN_EMAIL = "admin@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminPass123"

class VendorEcosystemTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.vendor_token = None
        self.admin_token = None
        self.vendor_id = None
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
            # Test vendor login
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = self.make_request("POST", "/auth/login", login_data)
            
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
            login_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD
            }
            
            response = self.make_request("POST", "/auth/login", login_data)
            
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
            
            response = self.make_request("POST", "/vendors/documents", document_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "document" in data:
                    document = data["document"]
                    self.log_test("Document Upload", True, "Document uploaded successfully", 
                                {"document_id": document["id"], "type": document["document_type"]})
                    return True
                else:
                    self.log_test("Document Upload", False, "Missing document in response", data)
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
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Vendor Ecosystem Backend API Tests")
        print("=" * 60)
        
        # Health check
        self.test_health_check()
        
        # Authentication tests
        self.test_user_registration()
        self.test_admin_registration()
        self.test_user_login()
        self.test_admin_login()
        
        # Vendor profile tests
        self.test_vendor_profile_creation()
        self.test_vendor_dashboard()
        
        # Document management tests
        self.test_document_upload()
        self.test_document_listing()
        
        # Admin functionality tests
        self.test_admin_stats()
        self.test_pending_verifications()
        
        # Public endpoint tests
        self.test_public_vendor_search()
        self.test_public_vendor_verification()
        
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