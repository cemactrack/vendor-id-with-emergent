#!/usr/bin/env python3
"""
Debug Verification Status
"""

import requests
import json

BACKEND_URL = "https://vendor-verify-3.preview.emergentagent.com/api"
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
            return data.get("token")
    except Exception as e:
        print(f"Error getting vendor token: {e}")
    return None

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

def debug_verification_status():
    """Debug current verification status"""
    vendor_token = get_vendor_token()
    admin_token = get_admin_token()
    
    if not vendor_token:
        print("❌ Could not get vendor token")
        return
    
    if not admin_token:
        print("❌ Could not get admin token")
        return
    
    print("🔍 DEBUGGING VERIFICATION STATUS")
    print("=" * 50)
    
    # Get vendor documents
    try:
        headers = {"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/vendors/documents", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            print(f"\n📄 VENDOR DOCUMENTS ({len(documents)} total):")
            
            for doc in documents:
                print(f"  • {doc['document_type']}: {doc['verification_status']} (ID: {doc['document_id']})")
                print(f"    Uploaded: {doc['upload_timestamp']}")
                if doc.get('verified_at'):
                    print(f"    Verified: {doc['verified_at']}")
                print()
        else:
            print(f"❌ Failed to get vendor documents: {response.text}")
    except Exception as e:
        print(f"Error getting vendor documents: {e}")
    
    # Get verification summary
    try:
        headers = {"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/vendors/documents/summary", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get("summary", {})
            print(f"📊 VERIFICATION SUMMARY:")
            print(f"  Total documents: {summary.get('total_documents', 0)}")
            print(f"  Approved documents: {summary.get('approved_documents', 0)}")
            print(f"  Rejected documents: {summary.get('rejected_documents', 0)}")
            print(f"  Pending documents: {summary.get('pending_documents', 0)}")
            print(f"  Required docs submitted: {summary.get('required_docs_submitted', 0)}")
            print(f"  Required docs approved: {summary.get('required_docs_approved', 0)}")
            print(f"  Verification complete: {summary.get('verification_complete', False)}")
        else:
            print(f"❌ Failed to get verification summary: {response.text}")
    except Exception as e:
        print(f"Error getting verification summary: {e}")
    
    # Get verification queue
    try:
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/admin/verification-queue", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            queue = data.get("queue", [])
            print(f"\n🔄 VERIFICATION QUEUE ({len(queue)} items):")
            
            for item in queue:
                print(f"  • {item['document_type']}: {item['status']} (ID: {item['document_id']})")
                if item.get('vendor_info'):
                    print(f"    Vendor: {item['vendor_info'].get('business_name', 'Unknown')}")
                print()
        else:
            print(f"❌ Failed to get verification queue: {response.text}")
    except Exception as e:
        print(f"Error getting verification queue: {e}")
    
    # Get vendor dashboard
    try:
        headers = {"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/vendors/dashboard", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            dashboard = data.get("dashboard", {})
            profile = dashboard.get("profile", {})
            print(f"🏢 VENDOR PROFILE STATUS:")
            print(f"  Business name: {profile.get('business_name', 'Unknown')}")
            print(f"  Vendor ID: {profile.get('vendor_id', 'Unknown')}")
            print(f"  Vendor ID Number: {profile.get('vendor_id_number', 'Not assigned')}")
            print(f"  Verification status: {profile.get('verification_status', 'Unknown')}")
            print(f"  Trust score: {profile.get('trust_score', 'Unknown')}")
        else:
            print(f"❌ Failed to get vendor dashboard: {response.text}")
    except Exception as e:
        print(f"Error getting vendor dashboard: {e}")
    
    # Get vendor ID info
    try:
        headers = {"Authorization": f"Bearer {vendor_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/vendors/vendor-id", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            vendor_id_info = data.get("vendor_id")
            print(f"\n🆔 VENDOR ID INFO:")
            if vendor_id_info:
                print(f"  Vendor ID Number: {vendor_id_info.get('vendor_id_number', 'Not assigned')}")
                print(f"  Country: {vendor_id_info.get('country', 'Unknown')}")
                print(f"  Status: {vendor_id_info.get('status', 'Unknown')}")
                print(f"  Trust Score: {vendor_id_info.get('trust_score', 'Unknown')}")
                print(f"  Issued Date: {vendor_id_info.get('issued_date', 'Unknown')}")
            else:
                print(f"  No Vendor ID assigned yet")
        else:
            print(f"❌ Failed to get vendor ID info: {response.text}")
    except Exception as e:
        print(f"Error getting vendor ID info: {e}")

if __name__ == "__main__":
    debug_verification_status()