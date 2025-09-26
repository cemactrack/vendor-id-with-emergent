#!/usr/bin/env python3
"""
Complete End-to-End Vendor Onboarding Workflow Test
Tests the full vendor onboarding process from registration to Vendor ID assignment
"""

import requests
import json
import base64
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://vendorsecure.preview.emergentagent.com/api"
TEST_VENDOR_EMAIL = "complete-test@example.com"
TEST_VENDOR_PASSWORD = "CompleteTest123!"
TEST_ADMIN_EMAIL = "admin.test@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminTest123!"

class CompleteOnboardingTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.vendor_token = None
        self.admin_token = None
        self.vendor_id = None
        self.vendor_user_id = None
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
                    headers: Dict[str, str] = None, token: str = None, files=None) -> requests.Response:
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
    
    def test_1_vendor_registration(self):
        """Step 1: Register new vendor user"""
        try:
            vendor_data = {
                "email": TEST_VENDOR_EMAIL,
                "password": TEST_VENDOR_PASSWORD,
                "full_name": "Complete Test Vendor",
                "phone": "+234-800-123-4567",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", vendor_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.vendor_user_id = data["user"]["id"]
                    self.log_test("1. Vendor Registration", True, "Vendor registered successfully", 
                                {"user_id": self.vendor_user_id, "email": data["user"]["email"]})
                    return True
                else:
                    self.log_test("1. Vendor Registration", False, "Missing token or user in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    # Try to login instead
                    return self.login_existing_vendor()
                else:
                    self.log_test("1. Vendor Registration", False, f"Registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("1. Vendor Registration", False, f"Registration error: {str(e)}")
            return False
    
    def login_existing_vendor(self):
        """Login existing vendor if registration fails"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_VENDOR_EMAIL}&password={TEST_VENDOR_PASSWORD}"
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.vendor_user_id = data["user"]["id"]
                    self.log_test("1. Vendor Registration", True, "Existing vendor logged in successfully")
                    return True
            
            self.log_test("1. Vendor Registration", False, "Failed to login existing vendor")
            return False
        except Exception as e:
            self.log_test("1. Vendor Registration", False, f"Login error: {str(e)}")
            return False
    
    def test_2_vendor_profile_creation(self):
        """Step 2: Create vendor profile with business information"""
        if not self.vendor_token:
            self.log_test("2. Vendor Profile Creation", False, "No vendor token available")
            return False
            
        try:
            profile_data = {
                "business_name": "Complete Test Business Ltd",
                "business_description": "A comprehensive testing business for complete vendor onboarding validation in Nigeria",
                "category": "technology",
                "website": "https://completetest.ng",
                "business_address": "123 Victoria Island, Lagos, Nigeria",
                "registration_number": "RC-COMPLETE-123456",
                "tax_id": "TIN-NG-987654321",
                "established_year": 2020,
                "employee_count": 15
            }
            
            response = self.make_request("POST", "/vendors/profile", profile_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "profile" in data:
                    profile = data["profile"]
                    self.vendor_id = profile["vendor_id"]
                    # Check for temporary "unverified" status
                    verification_status = profile.get("verification_status", "pending")
                    self.log_test("2. Vendor Profile Creation", True, 
                                f"Profile created with temporary status: {verification_status}", 
                                {"vendor_id": self.vendor_id, "business_name": profile["business_name"]})
                    return True
                else:
                    self.log_test("2. Vendor Profile Creation", False, "Missing profile in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    # Get existing profile
                    return self.get_existing_vendor_profile()
                else:
                    self.log_test("2. Vendor Profile Creation", False, f"Profile creation failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("2. Vendor Profile Creation", False, f"Profile creation error: {str(e)}")
            return False
    
    def get_existing_vendor_profile(self):
        """Get existing vendor profile"""
        try:
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data and "profile" in data["dashboard"]:
                    profile = data["dashboard"]["profile"]
                    self.vendor_id = profile["vendor_id"]
                    self.log_test("2. Vendor Profile Creation", True, f"Using existing profile: {self.vendor_id}")
                    return True
            return False
        except:
            return False
    
    def test_3_document_upload_process(self):
        """Step 3: Upload all required documents"""
        if not self.vendor_token:
            self.log_test("3. Document Upload Process", False, "No vendor token available")
            return False
        
        # Document types to upload
        documents_to_upload = [
            {
                "type": "business_registration",
                "filename": "business_registration_certificate.pdf",
                "content": "BUSINESS REGISTRATION CERTIFICATE\n\nBusiness Name: Complete Test Business Ltd\nRegistration Number: RC-COMPLETE-123456\nDate of Incorporation: 2020-01-15\nRegistered Address: 123 Victoria Island, Lagos, Nigeria\n\nThis certificate confirms the registration of the above business entity."
            },
            {
                "type": "tax_id",
                "filename": "tax_identification_document.pdf", 
                "content": "TAX IDENTIFICATION DOCUMENT\n\nTaxpayer Name: Complete Test Business Ltd\nTax Identification Number: TIN-NG-987654321\nTax Office: Lagos State Internal Revenue Service\nIssue Date: 2020-02-01\n\nThis document certifies the tax registration of the business entity."
            },
            {
                "type": "government_id",
                "filename": "government_issued_id.pdf",
                "content": "GOVERNMENT ISSUED IDENTIFICATION\n\nDocument Type: National Identity Card\nID Number: NIN-12345678901\nFull Name: Complete Test Vendor\nDate of Birth: 1985-06-15\nIssue Date: 2020-03-01\nExpiry Date: 2030-03-01\n\nThis is a valid government-issued identification document."
            }
        ]
        
        upload_success = True
        
        for doc in documents_to_upload:
            try:
                # Create multipart form data for file upload
                files = {
                    'file': (doc["filename"], doc["content"].encode(), 'application/pdf')
                }
                data = {
                    'document_type': doc["type"]
                }
                
                response = self.make_request("POST", "/vendors/documents/upload", 
                                           data=data, files=files, token=self.vendor_token)
                
                if response.status_code == 200:
                    result = response.json()
                    if "document_id" in result:
                        self.uploaded_documents.append({
                            "document_id": result["document_id"],
                            "type": doc["type"],
                            "filename": doc["filename"]
                        })
                        self.log_test(f"3a. Upload {doc['type']}", True, 
                                    f"Document uploaded successfully: {doc['filename']}")
                    else:
                        self.log_test(f"3a. Upload {doc['type']}", False, 
                                    f"Missing document_id in response for {doc['type']}")
                        upload_success = False
                else:
                    self.log_test(f"3a. Upload {doc['type']}", False, 
                                f"Upload failed for {doc['type']}: {response.text}")
                    upload_success = False
                    
            except Exception as e:
                self.log_test(f"3a. Upload {doc['type']}", False, 
                            f"Upload error for {doc['type']}: {str(e)}")
                upload_success = False
        
        # Verify all documents are in verification queue
        if upload_success:
            self.log_test("3. Document Upload Process", True, 
                        f"All {len(documents_to_upload)} documents uploaded successfully")
        else:
            self.log_test("3. Document Upload Process", False, 
                        "Some document uploads failed")
        
        return upload_success
    
    def test_4_admin_setup(self):
        """Step 4: Setup admin user for verification"""
        try:
            admin_data = {
                "email": TEST_ADMIN_EMAIL,
                "password": TEST_ADMIN_PASSWORD,
                "full_name": "Admin Verification Officer",
                "phone": "+234-800-987-6543",
                "country": "NG",
                "role": "verification_officer"
            }
            
            response = self.make_request("POST", "/auth/register", admin_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.admin_token = data["token"]
                    self.log_test("4. Admin Setup", True, "Admin user registered successfully")
                    return True
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    # Try to login
                    return self.login_admin()
                else:
                    self.log_test("4. Admin Setup", False, f"Admin registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("4. Admin Setup", False, f"Admin setup error: {str(e)}")
            return False
    
    def login_admin(self):
        """Login existing admin"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_ADMIN_EMAIL}&password={TEST_ADMIN_PASSWORD}"
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    self.admin_token = data["token"]
                    self.log_test("4. Admin Setup", True, "Admin logged in successfully")
                    return True
            
            self.log_test("4. Admin Setup", False, "Failed to login admin")
            return False
        except Exception as e:
            self.log_test("4. Admin Setup", False, f"Admin login error: {str(e)}")
            return False
    
    def test_5_admin_verification_workflow(self):
        """Step 5: Admin verification workflow"""
        if not self.admin_token:
            self.log_test("5. Admin Verification Workflow", False, "No admin token available")
            return False
        
        try:
            # Get verification queue
            response = self.make_request("GET", "/admin/verification-queue", token=self.admin_token)
            
            if response.status_code == 200:
                data = response.json()
                if "queue" in data:
                    queue = data["queue"]
                    self.log_test("5a. Get Verification Queue", True, 
                                f"Retrieved {len(queue)} documents in queue")
                    
                    # Find our vendor's documents
                    vendor_documents = [doc for doc in queue if doc.get("vendor_id") == self.vendor_user_id]
                    
                    if len(vendor_documents) >= 3:
                        self.log_test("5b. Verify Documents in Queue", True, 
                                    f"Found {len(vendor_documents)} documents for our vendor")
                        
                        # Approve each document
                        approval_success = True
                        for doc in vendor_documents:
                            doc_id = doc.get("document_id")
                            if doc_id:
                                approve_response = self.make_request("POST", f"/admin/documents/{doc_id}/approve", 
                                                                   token=self.admin_token)
                                if approve_response.status_code == 200:
                                    approve_data = approve_response.json()
                                    self.log_test(f"5c. Approve {doc.get('document_type', 'Document')}", True, 
                                                approve_data.get("message", "Document approved"))
                                else:
                                    self.log_test(f"5c. Approve {doc.get('document_type', 'Document')}", False, 
                                                f"Approval failed: {approve_response.text}")
                                    approval_success = False
                            else:
                                approval_success = False
                        
                        if approval_success:
                            self.log_test("5. Admin Verification Workflow", True, 
                                        "All documents approved successfully")
                            return True
                        else:
                            self.log_test("5. Admin Verification Workflow", False, 
                                        "Some document approvals failed")
                            return False
                    else:
                        self.log_test("5. Admin Verification Workflow", False, 
                                    f"Expected 3 documents, found {len(vendor_documents)}")
                        return False
                else:
                    self.log_test("5. Admin Verification Workflow", False, 
                                "Missing queue in response", data)
                    return False
            else:
                self.log_test("5. Admin Verification Workflow", False, 
                            f"Failed to get verification queue: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("5. Admin Verification Workflow", False, 
                        f"Admin verification error: {str(e)}")
            return False
    
    def test_6_vendor_id_generation(self):
        """Step 6: Verify Vendor ID generation and assignment"""
        if not self.vendor_token:
            self.log_test("6. Vendor ID Generation", False, "No vendor token available")
            return False
        
        try:
            # Check vendor ID info
            response = self.make_request("GET", "/vendors/vendor-id", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "vendor_id" in data and data["vendor_id"]:
                    vendor_id_info = data["vendor_id"]
                    vendor_id_number = vendor_id_info.get("vendor_id_number")
                    
                    if vendor_id_number:
                        # Check format VID-NG-XXXX
                        if re.match(r"VID-NG-\d{4}", vendor_id_number):
                            self.log_test("6a. Vendor ID Format", True, 
                                        f"Vendor ID follows correct format: {vendor_id_number}")
                            
                            # Check QR code generation
                            if "qr_code" in vendor_id_info:
                                self.log_test("6b. QR Code Generation", True, 
                                            "QR code generated successfully")
                            else:
                                self.log_test("6b. QR Code Generation", False, 
                                            "QR code not found in vendor ID info")
                            
                            self.log_test("6. Vendor ID Generation", True, 
                                        f"Vendor ID generated and assigned: {vendor_id_number}")
                            return True
                        else:
                            self.log_test("6. Vendor ID Generation", False, 
                                        f"Vendor ID format incorrect: {vendor_id_number}")
                            return False
                    else:
                        self.log_test("6. Vendor ID Generation", False, 
                                    "Vendor ID number not found in response")
                        return False
                else:
                    self.log_test("6. Vendor ID Generation", False, 
                                "Vendor ID not yet assigned - verification may not be complete")
                    return False
            else:
                self.log_test("6. Vendor ID Generation", False, 
                            f"Failed to get vendor ID info: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("6. Vendor ID Generation", False, 
                        f"Vendor ID generation error: {str(e)}")
            return False
    
    def test_7_profile_activation(self):
        """Step 7: Verify profile activation and status changes"""
        if not self.vendor_token:
            self.log_test("7. Profile Activation", False, "No vendor token available")
            return False
        
        try:
            # Get updated dashboard
            response = self.make_request("GET", "/vendors/dashboard", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "dashboard" in data:
                    dashboard = data["dashboard"]
                    profile = dashboard.get("profile", {})
                    
                    # Check verification status
                    verification_status = profile.get("verification_status")
                    if verification_status == "verified":
                        self.log_test("7a. Verification Status", True, 
                                    f"Vendor status changed to: {verification_status}")
                        
                        # Check trust score initialization
                        trust_score = profile.get("trust_score")
                        if trust_score is not None:
                            self.log_test("7b. Trust Score Initialization", True, 
                                        f"Trust score initialized: {trust_score}")
                        else:
                            self.log_test("7b. Trust Score Initialization", False, 
                                        "Trust score not initialized")
                        
                        # Check vendor ID in profile
                        vendor_id_number = profile.get("vendor_id_number")
                        if vendor_id_number:
                            self.log_test("7c. Vendor ID in Profile", True, 
                                        f"Vendor ID updated in profile: {vendor_id_number}")
                        else:
                            self.log_test("7c. Vendor ID in Profile", False, 
                                        "Vendor ID not found in profile")
                        
                        self.log_test("7. Profile Activation", True, 
                                    "Profile successfully activated with verified status")
                        return True
                    else:
                        self.log_test("7. Profile Activation", False, 
                                    f"Verification status not 'verified': {verification_status}")
                        return False
                else:
                    self.log_test("7. Profile Activation", False, 
                                "Missing dashboard in response", data)
                    return False
            else:
                self.log_test("7. Profile Activation", False, 
                            f"Failed to get dashboard: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("7. Profile Activation", False, 
                        f"Profile activation error: {str(e)}")
            return False
    
    def test_8_integration_verification(self):
        """Step 8: Verify integration points"""
        success = True
        
        # Test public verification endpoint
        if self.vendor_id:
            try:
                response = self.make_request("GET", f"/public/verify/{self.vendor_id}")
                if response.status_code == 200:
                    data = response.json()
                    if "verification" in data:
                        verification = data["verification"]
                        if verification.get("verification_status") == "verified":
                            self.log_test("8a. Public Verification Integration", True, 
                                        "Public verification endpoint working correctly")
                        else:
                            self.log_test("8a. Public Verification Integration", False, 
                                        "Public verification shows incorrect status")
                            success = False
                    else:
                        self.log_test("8a. Public Verification Integration", False, 
                                    "Missing verification in public response")
                        success = False
                else:
                    self.log_test("8a. Public Verification Integration", False, 
                                f"Public verification failed: {response.text}")
                    success = False
            except Exception as e:
                self.log_test("8a. Public Verification Integration", False, 
                            f"Public verification error: {str(e)}")
                success = False
        
        # Test verification summary
        if self.vendor_token:
            try:
                response = self.make_request("GET", "/vendors/documents/summary", token=self.vendor_token)
                if response.status_code == 200:
                    data = response.json()
                    if "summary" in data:
                        summary = data["summary"]
                        if summary.get("verification_complete"):
                            self.log_test("8b. Verification Summary Integration", True, 
                                        "Verification summary shows complete status")
                        else:
                            self.log_test("8b. Verification Summary Integration", False, 
                                        "Verification summary not showing complete")
                            success = False
                    else:
                        self.log_test("8b. Verification Summary Integration", False, 
                                    "Missing summary in response")
                        success = False
                else:
                    self.log_test("8b. Verification Summary Integration", False, 
                                f"Verification summary failed: {response.text}")
                    success = False
            except Exception as e:
                self.log_test("8b. Verification Summary Integration", False, 
                            f"Verification summary error: {str(e)}")
                success = False
        
        if success:
            self.log_test("8. Integration Verification", True, 
                        "All integration points working correctly")
        else:
            self.log_test("8. Integration Verification", False, 
                        "Some integration points failed")
        
        return success
    
    def run_complete_onboarding_test(self):
        """Run complete end-to-end onboarding test"""
        print("🚀 Starting Complete End-to-End Vendor Onboarding Test")
        print("=" * 70)
        print("Testing complete workflow from registration to Vendor ID assignment")
        print("=" * 70)
        
        # Run all test steps in sequence
        steps = [
            self.test_1_vendor_registration,
            self.test_2_vendor_profile_creation,
            self.test_3_document_upload_process,
            self.test_4_admin_setup,
            self.test_5_admin_verification_workflow,
            self.test_6_vendor_id_generation,
            self.test_7_profile_activation,
            self.test_8_integration_verification
        ]
        
        for step in steps:
            step()
            time.sleep(1)  # Small delay between steps
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPLETE ONBOARDING TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        # Group results by main steps
        main_steps = {}
        for result in self.test_results:
            step_num = result["test"].split(".")[0]
            if step_num not in main_steps:
                main_steps[step_num] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                main_steps[step_num]["passed"] += 1
            else:
                main_steps[step_num]["failed"] += 1
            main_steps[step_num]["tests"].append(result)
        
        print("\n📋 WORKFLOW STEP RESULTS:")
        for step, data in sorted(main_steps.items()):
            total = data["passed"] + data["failed"]
            status = "✅" if data["failed"] == 0 else "❌"
            print(f"  {status} Step {step}: {data['passed']}/{total} passed")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        # Final assessment
        critical_steps = ["1", "2", "3", "5", "6", "7"]
        critical_failures = [step for step in critical_steps if step in main_steps and main_steps[step]["failed"] > 0]
        
        if not critical_failures:
            print("\n🎉 COMPLETE ONBOARDING WORKFLOW: SUCCESS!")
            print("All critical steps completed successfully.")
        else:
            print(f"\n⚠️  COMPLETE ONBOARDING WORKFLOW: PARTIAL FAILURE")
            print(f"Critical step failures in: {', '.join(critical_failures)}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    tester = CompleteOnboardingTester()
    tester.run_complete_onboarding_test()