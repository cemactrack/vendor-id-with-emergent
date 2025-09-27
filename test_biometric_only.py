#!/usr/bin/env python3
"""
Test only biometric verification endpoints
"""

import sys
import os
sys.path.append('/app')

from backend_test import VendorEcosystemTester

def test_biometric_only():
    """Run only biometric tests"""
    tester = VendorEcosystemTester()
    
    print("🚀 Starting Biometric Verification System Tests")
    print("=" * 60)
    
    # Setup authentication first
    print("Setting up authentication...")
    tester.test_user_registration()
    tester.test_user_login()
    
    # Run biometric tests
    print("\n🔐 Biometric Verification System Tests")
    print("-" * 50)
    tester.test_biometric_verification_start()
    tester.test_biometric_verification_status()
    tester.test_biometric_document_analysis()
    tester.test_biometric_liveness_challenge()
    tester.test_biometric_liveness_response()
    tester.test_biometric_face_matching()
    tester.test_biometric_error_handling()
    tester.test_biometric_authentication_security()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 BIOMETRIC TEST SUMMARY")
    print("=" * 60)
    
    biometric_tests = [r for r in tester.test_results if "Biometric" in r["test"]]
    passed = sum(1 for result in biometric_tests if result["success"])
    failed = len(biometric_tests) - passed
    
    print(f"Total Biometric Tests: {len(biometric_tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(biometric_tests)*100):.1f}%")
    
    if failed > 0:
        print("\n🔍 FAILED BIOMETRIC TESTS:")
        for result in biometric_tests:
            if not result["success"]:
                print(f"  • {result['test']}: {result['message']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_biometric_only()