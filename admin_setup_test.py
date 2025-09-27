#!/usr/bin/env python3
"""
Admin Setup and Verification Test
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://vendor-verify-3.preview.emergentagent.com/api"

def test_admin_setup():
    """Test admin user creation and login"""
    
    # Try different admin credentials
    admin_configs = [
        {
            "email": "admin.verification@vendorsecure.com",
            "password": "AdminVerify123!",
            "full_name": "Admin Verification Officer",
            "phone": "+234-800-987-6543",
            "country": "NG",
            "role": "verification_officer"
        },
        {
            "email": "admin.test@vendorsecure.com", 
            "password": "AdminTest123!",
            "full_name": "Test Admin User",
            "phone": "+234-800-111-2222",
            "country": "NG",
            "role": "verification_officer"
        },
        {
            "email": "verification.officer@vendorsecure.com",
            "password": "VerifyOfficer123!",
            "full_name": "Verification Officer",
            "phone": "+234-800-333-4444", 
            "country": "NG",
            "role": "verification_officer"
        }
    ]
    
    for i, admin_data in enumerate(admin_configs):
        print(f"\n--- Testing Admin Config {i+1} ---")
        print(f"Email: {admin_data['email']}")
        
        # Try registration
        try:
            response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_data, timeout=30)
            print(f"Registration Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "token" in data:
                    print("✅ Registration successful - token received")
                    token = data["token"]
                    
                    # Test admin endpoints
                    test_admin_endpoints(token, admin_data["email"])
                    return token
                else:
                    print("❌ Registration successful but no token")
            else:
                print(f"Registration failed: {response.text}")
                
                # Try login if user exists
                if "already exists" in response.text:
                    print("User exists, trying login...")
                    login_url = f"{BACKEND_URL}/auth/login?email={admin_data['email']}&password={admin_data['password']}"
                    login_response = requests.post(login_url, headers={"Content-Type": "application/json"}, timeout=30)
                    
                    print(f"Login Status: {login_response.status_code}")
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        if "token" in login_data:
                            print("✅ Login successful - token received")
                            token = login_data["token"]
                            test_admin_endpoints(token, admin_data["email"])
                            return token
                        else:
                            print("❌ Login successful but no token")
                    else:
                        print(f"Login failed: {login_response.text}")
                        
        except Exception as e:
            print(f"Error with admin config {i+1}: {e}")
    
    return None

def test_admin_endpoints(token, email):
    """Test admin endpoints with token"""
    print(f"\nTesting admin endpoints for {email}...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test verification queue
    try:
        response = requests.get(f"{BACKEND_URL}/admin/verification-queue", headers=headers, timeout=30)
        print(f"Verification Queue Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            queue_size = len(data.get("queue", []))
            print(f"✅ Verification queue accessible - {queue_size} items")
        else:
            print(f"❌ Verification queue failed: {response.text}")
    except Exception as e:
        print(f"Error accessing verification queue: {e}")
    
    # Test admin stats
    try:
        response = requests.get(f"{BACKEND_URL}/admin/stats", headers=headers, timeout=30)
        print(f"Admin Stats Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin stats accessible")
        else:
            print(f"❌ Admin stats failed: {response.text}")
    except Exception as e:
        print(f"Error accessing admin stats: {e}")

if __name__ == "__main__":
    print("🔧 Admin Setup and Testing")
    print("=" * 50)
    
    admin_token = test_admin_setup()
    
    if admin_token:
        print(f"\n✅ Successfully created/logged in admin user")
        print(f"Token: {admin_token[:20]}...")
    else:
        print(f"\n❌ Failed to create/login admin user")