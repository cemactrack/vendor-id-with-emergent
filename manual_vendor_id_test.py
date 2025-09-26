#!/usr/bin/env python3
"""
Manual Vendor ID Generation Test
"""

import requests
import json

BACKEND_URL = "https://idecosystem.preview.emergentagent.com/api"
TEST_VENDOR_EMAIL = "complete-test@example.com"
TEST_VENDOR_PASSWORD = "CompleteTest123!"
TEST_ADMIN_EMAIL = "admin.test@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminTest123!"

def get_vendor_token():
    """Get vendor token"""
    try:
        url = f"{BACKEND_URL}/auth/login?email={TEST_VENDOR_EMAIL}&password={TEST_VENDOR_PASSWORD}"
        response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), data.get("user", {}).get("id")
    except Exception as e:
        print(f"Error getting vendor token: {e}")
    return None, None

def test_manual_vendor_id_generation():
    """Test manual vendor ID generation by calling the backend service directly"""
    vendor_token, vendor_user_id = get_vendor_token()
    
    if not vendor_token:
        print("❌ Could not get vendor token")
        return
    
    print("🔧 MANUAL VENDOR ID GENERATION TEST")
    print("=" * 50)
    print(f"Vendor User ID: {vendor_user_id}")
    
    # Get vendor profile to find vendor_id
    try:
        headers = {"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/vendors/dashboard", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            dashboard = data.get("dashboard", {})
            profile = dashboard.get("profile", {})
            vendor_id = profile.get("vendor_id")
            country = profile.get("country", "NG")
            
            print(f"Vendor ID (internal): {vendor_id}")
            print(f"Country: {country}")
            
            # Check if vendor ID already exists
            if profile.get("vendor_id_number"):
                print(f"✅ Vendor ID already exists: {profile.get('vendor_id_number')}")
                return
            
            # Since we can't directly call the service, let's try to trigger it by approving a document again
            # First, let's upload a new document and then approve it to trigger the generation
            
            print("\n🔄 Attempting to trigger Vendor ID generation...")
            
            # Upload a new document
            files = {
                'file': ('test_trigger_document.pdf', b'Test document to trigger vendor ID generation', 'application/pdf')
            }
            data_form = {
                'document_type': 'other'
            }
            
            upload_response = requests.post(f"{BACKEND_URL}/vendors/documents/upload", 
                                          data=data_form, files=files, headers={"Authorization": f"Bearer {vendor_token}"}, timeout=30)
            
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                new_document_id = upload_data.get("document_id")
                print(f"✅ Uploaded trigger document: {new_document_id}")
                
                # Now approve it with admin
                admin_token = get_admin_token()
                if admin_token:
                    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
                    approve_response = requests.post(f"{BACKEND_URL}/admin/documents/{new_document_id}/approve", 
                                                   headers=admin_headers, timeout=30)
                    
                    if approve_response.status_code == 200:
                        approve_data = approve_response.json()
                        print(f"✅ Approved trigger document: {approve_data.get('message', 'Success')}")
                        
                        # Check if Vendor ID was generated
                        check_response = requests.get(f"{BACKEND_URL}/vendors/vendor-id", headers=headers, timeout=30)
                        if check_response.status_code == 200:
                            check_data = check_response.json()
                            vendor_id_info = check_data.get("vendor_id")
                            if vendor_id_info:
                                print(f"🎉 SUCCESS! Vendor ID generated: {vendor_id_info.get('vendor_id_number')}")
                            else:
                                print("❌ Vendor ID still not generated after trigger")
                        else:
                            print(f"❌ Failed to check vendor ID: {check_response.text}")
                    else:
                        print(f"❌ Failed to approve trigger document: {approve_response.text}")
                else:
                    print("❌ Could not get admin token")
            else:
                print(f"❌ Failed to upload trigger document: {upload_response.text}")
                
        else:
            print(f"❌ Failed to get vendor dashboard: {response.text}")
    except Exception as e:
        print(f"Error in manual vendor ID generation: {e}")

def get_admin_token():
    """Get admin token"""
    try:
        url = f"{BACKEND_URL}/auth/login?email={TEST_ADMIN_EMAIL}&password={TEST_ADMIN_PASSWORD}"
        response = requests.post(url, headers={"Content-Type": "application/json"}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
    except Exception as e:
        print(f"Error getting admin token: {e}")
    return None

if __name__ == "__main__":
    test_manual_vendor_id_generation()