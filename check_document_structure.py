#!/usr/bin/env python3
"""
Check Document Structure
"""

import requests
import json

BACKEND_URL = "https://vendor-verify-3.preview.emergentagent.com/api"
TEST_ADMIN_EMAIL = "admin.test@vendorsecure.com"
TEST_ADMIN_PASSWORD = "AdminTest123!"

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

def check_document_structure():
    """Check the structure of documents in the system"""
    admin_token = get_admin_token()
    
    if not admin_token:
        print("❌ Could not get admin token")
        return
    
    print("🔍 CHECKING DOCUMENT STRUCTURE")
    print("=" * 50)
    
    # Get verification queue to see document structure
    try:
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        response = requests.get(f"{BACKEND_URL}/admin/verification-queue", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            queue = data.get("queue", [])
            print(f"Found {len(queue)} items in queue")
            
            if queue:
                # Show structure of first item
                first_item = queue[0]
                print(f"\n📄 SAMPLE QUEUE ITEM STRUCTURE:")
                print(json.dumps(first_item, indent=2, default=str))
        else:
            print(f"❌ Failed to get verification queue: {response.text}")
    except Exception as e:
        print(f"Error getting verification queue: {e}")
    
    # Get a specific document for review to see its structure
    try:
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        # Use a known document ID from our previous tests
        document_id = "DOC-D99A07FCC718"  # The trigger document we just created
        response = requests.get(f"{BACKEND_URL}/admin/documents/{document_id}/review", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📄 DOCUMENT REVIEW STRUCTURE:")
            print(json.dumps(data, indent=2, default=str))
        else:
            print(f"❌ Failed to get document review: {response.text}")
    except Exception as e:
        print(f"Error getting document review: {e}")

if __name__ == "__main__":
    check_document_structure()