#!/usr/bin/env python3
"""
Enhanced Authentication Testing Suite for Vendor Verification and Trust Ecosystem
Tests all enhanced authentication features: email verification, password reset, 2FA, security management
"""

import requests
import json
import base64
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://vendor-verify-3.preview.emergentagent.com/api"
TEST_USER_EMAIL = "enhanced.auth.test@example.com"
TEST_USER_PASSWORD = "SecureTestPass123!"
TEST_ADMIN_EMAIL = "admin.enhanced@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminSecurePass123!"
TEST_2FA_USER_EMAIL = "twofa.test@example.com"
TEST_2FA_PASSWORD = "TwoFATestPass123!"

class EnhancedAuthTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.vendor_token = None
        self.admin_token = None
        self.twofa_token = None
        self.vendor_id = None
        self.test_results = []
        self.email_verification_token = None
        self.password_reset_token = None
        self.twofa_secret = None
        self.backup_codes = []
        self.twofa_user_id = None
        
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
    
    def extract_token_from_logs(self, log_output: str, token_type: str) -> Optional[str]:
        """Extract token from mock email logs"""
        patterns = {
            "verification": r"Verification token for .+?: ([A-Za-z0-9]+)",
            "reset": r"Password reset token for .+?: ([A-Za-z0-9]+)"
        }
        
        pattern = patterns.get(token_type)
        if pattern:
            match = re.search(pattern, log_output)
            if match:
                return match.group(1)
        return None
    
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
    
    # Enhanced Authentication Tests
    
    def test_user_registration_with_email_verification(self):
        """Test user registration with email verification"""
        try:
            user_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "full_name": "Enhanced Auth Test User",
                "phone": "1234567890",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data and "email_verification_sent" in data:
                    self.vendor_token = data["token"]
                    email_sent = data["email_verification_sent"]
                    self.log_test("User Registration with Email Verification", True, 
                                f"User registered successfully, email verification sent: {email_sent}", 
                                {"user_id": data["user"]["id"], "email": data["user"]["email"]})
                    return True
                else:
                    self.log_test("User Registration with Email Verification", False, 
                                "Missing required fields in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    # Try to login instead
                    return self.test_user_login()
                else:
                    self.log_test("User Registration with Email Verification", False, 
                                f"Registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("User Registration with Email Verification", False, 
                        f"Registration error: {str(e)}")
            return False
    
    def test_resend_email_verification(self):
        """Test resend email verification"""
        if not self.vendor_token:
            self.log_test("Resend Email Verification", False, "No vendor token available")
            return False
            
        try:
            response = self.make_request("POST", "/auth/resend-verification", token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Resend Email Verification", True, 
                                f"Verification email resent: {data['message']}")
                    return True
                else:
                    self.log_test("Resend Email Verification", False, 
                                "Missing message in response", data)
                    return False
            else:
                self.log_test("Resend Email Verification", False, 
                            f"Resend verification failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Resend Email Verification", False, 
                        f"Resend verification error: {str(e)}")
            return False
    
    def test_email_verification_with_invalid_token(self):
        """Test email verification with invalid token"""
        try:
            invalid_token = "invalid_token_12345"
            verification_data = {"token": invalid_token}
            
            response = self.make_request("POST", "/auth/verify-email", verification_data)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test("Email Verification (Invalid Token)", True, 
                            f"Correctly rejected invalid token: {data.get('detail', 'Invalid token')}")
                return True
            else:
                self.log_test("Email Verification (Invalid Token)", False, 
                            f"Should have rejected invalid token, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Email Verification (Invalid Token)", False, 
                        f"Email verification error: {str(e)}")
            return False
    
    def test_password_reset_request(self):
        """Test password reset request"""
        try:
            reset_data = {"email": TEST_USER_EMAIL}
            
            response = self.make_request("POST", "/auth/forgot-password", reset_data)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Password Reset Request", True, 
                                f"Password reset requested: {data['message']}")
                    return True
                else:
                    self.log_test("Password Reset Request", False, 
                                "Missing message in response", data)
                    return False
            else:
                self.log_test("Password Reset Request", False, 
                            f"Password reset request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Password Reset Request", False, 
                        f"Password reset request error: {str(e)}")
            return False
    
    def test_password_reset_with_invalid_token(self):
        """Test password reset with invalid token"""
        try:
            invalid_token = "invalid_reset_token_12345"
            reset_data = {
                "token": invalid_token,
                "new_password": "NewSecurePassword123!"
            }
            
            response = self.make_request("POST", "/auth/reset-password", reset_data)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test("Password Reset (Invalid Token)", True, 
                            f"Correctly rejected invalid reset token: {data.get('detail', 'Invalid token')}")
                return True
            else:
                self.log_test("Password Reset (Invalid Token)", False, 
                            f"Should have rejected invalid token, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Password Reset (Invalid Token)", False, 
                        f"Password reset error: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password={TEST_USER_PASSWORD}"
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.vendor_token = data["token"]
                    self.log_test("User Login", True, "User login successful", 
                                {"user_id": data["user"]["id"], "role": data["user"]["role"]})
                    return True
                else:
                    self.log_test("User Login", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_test("User Login", False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Login error: {str(e)}")
            return False
    
    def test_2fa_user_registration(self):
        """Test 2FA user registration"""
        try:
            user_data = {
                "email": TEST_2FA_USER_EMAIL,
                "password": TEST_2FA_PASSWORD,
                "full_name": "Two Factor Test User",
                "phone": "9876543210",
                "country": "NG",
                "role": "vendor"
            }
            
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.twofa_token = data["token"]
                    self.twofa_user_id = data["user"]["id"]
                    self.log_test("2FA User Registration", True, "2FA test user registered successfully", 
                                {"user_id": data["user"]["id"], "email": data["user"]["email"]})
                    return True
                else:
                    self.log_test("2FA User Registration", False, "Missing token or user in response", data)
                    return False
            else:
                error_msg = response.text
                if response.status_code == 400 and "already exists" in error_msg:
                    # Try to login instead
                    return self.test_2fa_user_login()
                else:
                    self.log_test("2FA User Registration", False, f"Registration failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.log_test("2FA User Registration", False, f"Registration error: {str(e)}")
            return False
    
    def test_2fa_user_login(self):
        """Test 2FA user login"""
        try:
            url = f"{self.base_url}/auth/login?email={TEST_2FA_USER_EMAIL}&password={TEST_2FA_PASSWORD}"
            
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data and "user" in data:
                    self.twofa_token = data["token"]
                    self.twofa_user_id = data["user"]["id"]
                    self.log_test("2FA User Login", True, "2FA user login successful", 
                                {"user_id": data["user"]["id"], "role": data["user"]["role"]})
                    return True
                else:
                    self.log_test("2FA User Login", False, "Missing token or user in response", data)
                    return False
            else:
                self.log_test("2FA User Login", False, f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("2FA User Login", False, f"Login error: {str(e)}")
            return False
    
    def test_2fa_setup(self):
        """Test 2FA setup"""
        if not self.twofa_token:
            self.log_test("2FA Setup", False, "No 2FA user token available")
            return False
            
        try:
            setup_data = {"password": TEST_2FA_PASSWORD}
            
            response = self.make_request("POST", "/auth/2fa/setup", setup_data, token=self.twofa_token)
            
            if response.status_code == 200:
                data = response.json()
                if "setup_data" in data and "message" in data:
                    setup_info = data["setup_data"]
                    required_fields = ["qr_code", "setup_key", "backup_codes", "issuer"]
                    missing_fields = [field for field in required_fields if field not in setup_info]
                    
                    if not missing_fields:
                        self.twofa_secret = setup_info["setup_key"]
                        self.backup_codes = setup_info["backup_codes"]
                        self.log_test("2FA Setup", True, 
                                    f"2FA setup successful: {data['message']}", 
                                    {"backup_codes_count": len(self.backup_codes)})
                        return True
                    else:
                        self.log_test("2FA Setup", False, f"Missing setup fields: {missing_fields}")
                        return False
                else:
                    self.log_test("2FA Setup", False, "Missing setup_data or message in response", data)
                    return False
            else:
                self.log_test("2FA Setup", False, f"2FA setup failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("2FA Setup", False, f"2FA setup error: {str(e)}")
            return False
    
    def test_2fa_enable_with_invalid_token(self):
        """Test 2FA enable with invalid token"""
        if not self.twofa_token:
            self.log_test("2FA Enable (Invalid Token)", False, "No 2FA user token available")
            return False
            
        try:
            enable_data = {"token": "123456"}  # Invalid TOTP token
            
            response = self.make_request("POST", "/auth/2fa/enable", enable_data, token=self.twofa_token)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test("2FA Enable (Invalid Token)", True, 
                            f"Correctly rejected invalid TOTP token: {data.get('detail', 'Invalid token')}")
                return True
            else:
                self.log_test("2FA Enable (Invalid Token)", False, 
                            f"Should have rejected invalid token, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("2FA Enable (Invalid Token)", False, f"2FA enable error: {str(e)}")
            return False
    
    def test_2fa_verify_without_setup(self):
        """Test 2FA verification without setup"""
        if not self.vendor_token:
            self.log_test("2FA Verify (No Setup)", False, "No vendor token available")
            return False
            
        try:
            verify_data = {"token": "123456"}
            
            response = self.make_request("POST", "/auth/2fa/verify", verify_data, token=self.vendor_token)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test("2FA Verify (No Setup)", True, 
                            f"Correctly rejected verification without setup: {data.get('detail', 'No 2FA setup')}")
                return True
            else:
                self.log_test("2FA Verify (No Setup)", False, 
                            f"Should have rejected verification without setup, got status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("2FA Verify (No Setup)", False, f"2FA verify error: {str(e)}")
            return False
    
    def test_2fa_disable_without_setup(self):
        """Test 2FA disable without setup"""
        if not self.vendor_token:
            self.log_test("2FA Disable (No Setup)", False, "No vendor token available")
            return False
            
        try:
            disable_data = {"password": TEST_USER_PASSWORD}
            
            response = self.make_request("POST", "/auth/2fa/disable", disable_data, token=self.vendor_token)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("2FA Disable (No Setup)", True, 
                            f"2FA disable handled correctly: {data.get('message', 'Disabled')}")
                return True
            else:
                self.log_test("2FA Disable (No Setup)", False, 
                            f"2FA disable failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("2FA Disable (No Setup)", False, f"2FA disable error: {str(e)}")
            return False
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials and account lockout"""
        try:
            # Test with wrong password multiple times to trigger lockout
            for attempt in range(3):
                url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password=wrongpassword"
                response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
                
                if response.status_code == 401:
                    continue
                else:
                    self.log_test("Login Invalid Credentials", False, 
                                f"Expected 401 for wrong password, got {response.status_code}")
                    return False
            
            self.log_test("Login Invalid Credentials", True, 
                        "Invalid credentials correctly rejected multiple times")
            return True
                
        except Exception as e:
            self.log_test("Login Invalid Credentials", False, f"Login test error: {str(e)}")
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
                        self.log_test("Security Info", True, 
                                    "Security info retrieved successfully", 
                                    {"2fa_enabled": security_info["two_factor_enabled"], 
                                     "email_verified": security_info["email_verified"]})
                        return True
                    else:
                        self.log_test("Security Info", False, f"Missing security fields: {missing_fields}")
                        return False
                else:
                    self.log_test("Security Info", False, "Missing security in response", data)
                    return False
            else:
                self.log_test("Security Info", False, f"Security info failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Security Info", False, f"Security info error: {str(e)}")
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
                    self.log_test("Security Events", True, 
                                f"Security events retrieved successfully: {len(events)} events")
                    return True
                else:
                    self.log_test("Security Events", False, "Missing events in response", data)
                    return False
            else:
                self.log_test("Security Events", False, f"Security events failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Security Events", False, f"Security events error: {str(e)}")
            return False
    
    def test_enhanced_login_flow(self):
        """Test complete enhanced login flow"""
        try:
            # Test normal login first
            url = f"{self.base_url}/auth/login?email={TEST_USER_EMAIL}&password={TEST_USER_PASSWORD}"
            response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "requires_2fa" in data:
                    self.log_test("Enhanced Login Flow", True, 
                                "Login correctly requires 2FA when enabled")
                    return True
                elif "token" in data:
                    self.log_test("Enhanced Login Flow", True, 
                                "Login successful without 2FA (not enabled)")
                    return True
                else:
                    self.log_test("Enhanced Login Flow", False, 
                                "Unexpected login response format", data)
                    return False
            else:
                self.log_test("Enhanced Login Flow", False, 
                            f"Enhanced login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Login Flow", False, f"Enhanced login error: {str(e)}")
            return False
    
    def run_enhanced_auth_tests(self):
        """Run all enhanced authentication tests"""
        print("🔐 Starting Enhanced Authentication Tests")
        print("=" * 60)
        
        # Health check
        self.test_health_check()
        
        # Enhanced Authentication Tests
        print("\n📧 Email Verification Tests")
        self.test_user_registration_with_email_verification()
        self.test_resend_email_verification()
        self.test_email_verification_with_invalid_token()
        
        print("\n🔑 Password Reset Tests")
        self.test_password_reset_request()
        self.test_password_reset_with_invalid_token()
        
        print("\n🔒 Two-Factor Authentication Tests")
        self.test_2fa_user_registration()
        self.test_2fa_setup()
        self.test_2fa_enable_with_invalid_token()
        self.test_2fa_verify_without_setup()
        self.test_2fa_disable_without_setup()
        
        print("\n🛡️ Enhanced Login & Security Tests")
        self.test_enhanced_login_flow()
        self.test_login_with_invalid_credentials()
        self.test_security_info_endpoint()
        self.test_security_events_endpoint()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ENHANCED AUTHENTICATION TEST SUMMARY")
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
    tester = EnhancedAuthTester()
    tester.run_enhanced_auth_tests()