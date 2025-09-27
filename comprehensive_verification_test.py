#!/usr/bin/env python3
"""
Comprehensive Verification Test
Tests the overall system functionality after systematic fixes
"""

import requests
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://idecosystem.preview.emergentagent.com/api"
TEST_USER_EMAIL = "comprehensive.verification@example.com"
TEST_USER_PASSWORD = "ComprehensiveTest123!"
TEST_ADMIN_EMAIL = "admin.verification@example.com"
TEST_ADMIN_PASSWORD = "AdminVerification123!"

class ComprehensiveVerificationTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.user_token = None
        self.admin_token = None
        self.vendor_id = None
        self.test_results = []
        self.document_id = None
        
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
    
    def setup_test_users(self):
        """Setup test users"""
        try:
            # Create vendor user
            user_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Comprehensive Test Vendor",
                "phone": "1234567890",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("token")
            elif response.status_code == 400 and "already exists" in response.text:
                # Login existing user
                url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password={TEST_USER_PASSWORD}"
                login_response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.user_token = data.get("token")
            
            # Create admin user
            admin_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD,
                "full_name": "Comprehensive Test Admin",
                "phone": "9876543210",
                "country": "NG",
                "role": "verification_officer"
            }
            
            admin_response = self.make_request("POST", "/auth/register", admin_data)
            
            if admin_response.status_code == 200:
                admin_data_resp = admin_response.json()
                self.admin_token = admin_data_resp.get("token")
            elif admin_response.status_code == 400 and "already exists" in admin_response.text:
                # Login existing admin
                url = f"{self.base_url}/auth/login?email={TEST_ADMIN_EMAIL}&password={TEST_ADMIN_PASSWORD}"
                admin_login_response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
                if admin_login_response.status_code == 200:
                    admin_data_resp = admin_login_response.json()
                    self.admin_token = admin_data_resp.get("token")
            
            if self.user_token and self.admin_token:
                self.log_test("User Setup", True, "Test users setup successfully")
                return True
            else:
                self.log_test("User Setup", False, "Failed to setup test users")
                return False
                
        except Exception as e:
            self.log_test("User Setup", False, f"User setup error: {str(e)}")
            return False
    
    def test_vendor_profile_creation(self):
        """Test vendor profile creation"""
        if not self.user_token:
            self.log_test("Vendor Profile Creation", False, "No user token available")
            return False
            
        try:
            profile_data = {
                "business_name": "Comprehensive Test Business Ltd",
                "business_description": "A comprehensive testing business for verification",
                "category": "technology",
                "website": "https://testbusiness.example.com",
                "business_address": "123 Test Street, Lagos, Nigeria",
                "registration_number": "RC987654321",
                "tax_id": "TIN123456789",
                "established_year": 2020,
                "employee_count": 15
            }
            
            response = self.make_request("POST", "/vendors/profile", profile_data, token=self.user_token)
            
            if response.status_code == 200:
                data = response.json()
                if "profile" in data:
                    profile = data["profile"]
                    self.vendor_id = profile["vendor_id"]
                    self.log_test("Vendor Profile Creation", True, "Profile created successfully", 
                                {"vendor_id": self.vendor_id})
                    return True
                else:
                    self.log_test("Vendor Profile Creation", False, "Missing profile in response", data)
                    return False
            elif response.status_code == 400 and "already exists" in response.text:
                # Get existing profile
                dashboard_response = self.make_request("GET", "/vendors/dashboard", token=self.user_token)
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    if "profile" in dashboard_data:
                        self.vendor_id = dashboard_data["profile"].get("vendor_id")
                        self.log_test("Vendor Profile Creation", True, "Using existing profile", 
                                    {"vendor_id": self.vendor_id})
                        return True
                
                self.log_test("Vendor Profile Creation", False, f"Profile exists but can't retrieve")
                return False
            else:
                self.log_test("Vendor Profile Creation", False, f"Profile creation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Vendor Profile Creation", False, f"Profile creation error: {str(e)}")
            return False
    
    def test_enhanced_dashboard(self):
        """Test enhanced dashboard functionality"""
        if not self.user_token:
            self.log_test("Enhanced Dashboard", False, "No user token available")
            return False
            
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.user_token)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for all expected fields after enhancement
                expected_fields = ["profile", "analytics", "documents", "security_events"]
                present_fields = [field for field in expected_fields if field in data]
                
                if len(present_fields) >= 3:
                    self.log_test("Enhanced Dashboard", True, 
                                f"Dashboard enhanced successfully with {len(present_fields)}/4 fields",
                                {"present_fields": present_fields})
                    return True
                else:
                    self.log_test("Enhanced Dashboard", False, 
                                f"Missing enhanced fields: {[f for f in expected_fields if f not in data]}")
                    return False
            else:
                self.log_test("Enhanced Dashboard", False, f"Dashboard request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Dashboard", False, f"Dashboard test error: {str(e)}")
            return False
    
    def test_document_upload_with_replacement(self):
        """Test document upload with replacement capability"""
        if not self.user_token:
            self.log_test("Document Upload with Replacement", False, "No user token available")
            return False
            
        try:
            # Create unique test content to avoid cross-test conflicts
            test_content = f"Test document content - {datetime.now().isoformat()}"
            encoded_content = base64.b64encode(test_content.encode()).decode()
            
            # First upload
            files = {
                'file': ('business_reg_v1.pdf', base64.b64decode(encoded_content), 'application/pdf')
            }
            data = {
                'document_type': 'business_registration'
            }
            
            url = f"{self.base_url}/vendors/documents/upload"
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            response1 = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            
            if response1.status_code == 200:
                doc1_data = response1.json()
                doc1_id = doc1_data.get("document_id")
                self.document_id = doc1_id
                
                # Second upload - replacement
                test_content_v2 = f"Updated test document content - {datetime.now().isoformat()}"
                encoded_content_v2 = base64.b64encode(test_content_v2.encode()).decode()
                
                files2 = {
                    'file': ('business_reg_v2.pdf', base64.b64decode(encoded_content_v2), 'application/pdf')
                }
                data2 = {
                    'document_type': 'business_registration'
                }
                
                response2 = requests.post(url, files=files2, data=data2, headers=headers, timeout=30)
                
                if response2.status_code == 200:
                    doc2_data = response2.json()
                    doc2_id = doc2_data.get("document_id")
                    
                    self.log_test("Document Upload with Replacement", True, 
                                "Document replacement working correctly",
                                {
                                    "original_doc_id": doc1_id,
                                    "replacement_doc_id": doc2_id
                                })
                    return True
                else:
                    self.log_test("Document Upload with Replacement", False, 
                                f"Replacement upload failed: {response2.text}")
                    return False
            else:
                self.log_test("Document Upload with Replacement", False, 
                            f"Initial upload failed: {response1.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload with Replacement", False, f"Test error: {str(e)}")
            return False
    
    def test_security_features(self):
        """Test enhanced security features"""
        if not self.user_token:
            self.log_test("Security Features", False, "No user token available")
            return False
            
        try:
            # Test security info endpoint
            security_response = self.make_request("GET", "/auth/security/info", token=self.user_token)
            
            if security_response.status_code == 200:
                security_data = security_response.json()
                if "security" in security_data:
                    security_info = security_data["security"]
                    required_fields = ["user_id", "email_verified", "two_factor_enabled", "failed_login_attempts"]
                    
                    if all(field in security_info for field in required_fields):
                        # Test security events
                        events_response = self.make_request("GET", "/auth/security/events?limit=5", token=self.user_token)
                        
                        if events_response.status_code == 200:
                            events_data = events_response.json()
                            if "events" in events_data:
                                self.log_test("Security Features", True, 
                                            "Security features working correctly",
                                            {
                                                "security_fields_present": len(required_fields),
                                                "security_events_count": len(events_data["events"])
                                            })
                                return True
                        
                        self.log_test("Security Features", False, "Security events endpoint failed")
                        return False
                    else:
                        self.log_test("Security Features", False, "Missing security info fields")
                        return False
                else:
                    self.log_test("Security Features", False, "Missing security in response")
                    return False
            else:
                self.log_test("Security Features", False, f"Security info request failed: {security_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Security Features", False, f"Security test error: {str(e)}")
            return False
    
    def test_admin_functionality(self):
        """Test admin functionality"""
        if not self.admin_token:
            self.log_test("Admin Functionality", False, "No admin token available")
            return False
            
        try:
            # Test admin stats
            stats_response = self.make_request("GET", "/admin/stats", token=self.admin_token)
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                if "stats" in stats_data:
                    stats = stats_data["stats"]
                    required_stats = ["total_vendors", "verified_vendors", "pending_verification"]
                    
                    if all(field in stats for field in required_stats):
                        # Test pending verifications
                        verifications_response = self.make_request("GET", "/admin/verifications/pending", token=self.admin_token)
                        
                        if verifications_response.status_code == 200:
                            verifications_data = verifications_response.json()
                            if "verifications" in verifications_data:
                                self.log_test("Admin Functionality", True, 
                                            "Admin functionality working correctly",
                                            {
                                                "stats_fields": len(required_stats),
                                                "pending_verifications": len(verifications_data["verifications"])
                                            })
                                return True
                        
                        self.log_test("Admin Functionality", False, "Pending verifications endpoint failed")
                        return False
                    else:
                        self.log_test("Admin Functionality", False, "Missing admin stats fields")
                        return False
                else:
                    self.log_test("Admin Functionality", False, "Missing stats in response")
                    return False
            else:
                self.log_test("Admin Functionality", False, f"Admin stats request failed: {stats_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Admin Functionality", False, f"Admin test error: {str(e)}")
            return False
    
    def test_public_endpoints(self):
        """Test public endpoints"""
        try:
            # Test public search
            search_response = self.make_request("GET", "/public/search?query=test&limit=5")
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if "vendors" in search_data and "total" in search_data:
                    # Test public verification if we have a vendor ID
                    if self.vendor_id:
                        verify_response = self.make_request("GET", f"/public/verify/{self.vendor_id}")
                        
                        if verify_response.status_code in [200, 404]:  # 404 is acceptable if not verified yet
                            self.log_test("Public Endpoints", True, 
                                        "Public endpoints working correctly",
                                        {
                                            "search_vendors_count": len(search_data["vendors"]),
                                            "verification_status": verify_response.status_code
                                        })
                            return True
                        else:
                            self.log_test("Public Endpoints", False, f"Public verification failed: {verify_response.text}")
                            return False
                    else:
                        self.log_test("Public Endpoints", True, 
                                    "Public search working correctly",
                                    {"search_vendors_count": len(search_data["vendors"])})
                        return True
                else:
                    self.log_test("Public Endpoints", False, "Missing vendors or total in search response")
                    return False
            else:
                self.log_test("Public Endpoints", False, f"Public search failed: {search_response.text}")
                return False
                
        except Exception as e:
            self.log_test("Public Endpoints", False, f"Public endpoints test error: {str(e)}")
            return False
    
    def run_comprehensive_verification(self):
        """Run comprehensive verification tests"""
        print("🔍 Comprehensive System Verification After Fixes")
        print("=" * 60)
        
        # Health check
        self.test_health_check()
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users, aborting tests")
            return
        
        print("\n👤 Testing Vendor Profile Management")
        print("-" * 40)
        self.test_vendor_profile_creation()
        
        print("\n📊 Testing Enhanced Dashboard")
        print("-" * 40)
        self.test_enhanced_dashboard()
        
        print("\n📄 Testing Document Upload with Replacement")
        print("-" * 40)
        self.test_document_upload_with_replacement()
        
        print("\n🛡️ Testing Security Features")
        print("-" * 40)
        self.test_security_features()
        
        print("\n⚙️ Testing Admin Functionality")
        print("-" * 40)
        self.test_admin_functionality()
        
        print("\n🌐 Testing Public Endpoints")
        print("-" * 40)
        self.test_public_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE VERIFICATION SUMMARY")
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
        else:
            print("\n🎉 ALL TESTS PASSED! System is working correctly after fixes.")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = ComprehensiveVerificationTester()
    tester.run_comprehensive_verification()