#!/usr/bin/env python3
"""
Test script to debug authentication flow issues.
Tests the complete login -> token verification -> API access flow.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_auth_flow():
    """Test the complete authentication flow."""
    print("Testing Authentication Flow")
    print("=" * 50)
    
    # Test credentials (use existing user from logs)
    credentials = {
        "username": "Alio",
        "password": "XmP6_6afz:NqTzT"
    }
    
    print(f"Testing with user: {credentials['username']}")
    
    # Step 1: Login
    print("\n1. Testing Login...")
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json=credentials,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('token')
            user = login_data.get('user', {})
            
            print(f"[OK] Login successful!")
            print(f"   User ID: {user.get('id')}")
            print(f"   Username: {user.get('username')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Token length: {len(token) if token else 0}")
            print(f"   Token starts with: {token[:20] if token else 'None'}...")
            
            # Step 2: Verify token
            print("\n2. Testing Token Verification...")
            verify_response = requests.post(
                f"{BASE_URL}/auth/verify",
                json={"token": token},
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Verify Status Code: {verify_response.status_code}")
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                print(f"[OK] Token verification successful!")
                print(f"   Valid: {verify_data.get('valid')}")
                print(f"   User: {verify_data.get('user', {}).get('username')}")
            else:
                print(f"[FAIL] Token verification failed!")
                print(f"   Response: {verify_response.text}")
            
            # Step 3: Test API access with token
            print("\n3. Testing API Access with Token...")
            
            # Test profile endpoint
            profile_response = requests.get(
                f"{BASE_URL}/auth/profile",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"Profile Status Code: {profile_response.status_code}")
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print(f"[OK] Profile access successful!")
                print(f"   Profile User: {profile_data.get('user', {}).get('username')}")
            else:
                print(f"[FAIL] Profile access failed!")
                print(f"   Response: {profile_response.text}")
            
            # Test datasets endpoint
            datasets_response = requests.get(
                f"{BASE_URL}/datasets",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"Datasets Status Code: {datasets_response.status_code}")
            if datasets_response.status_code == 200:
                datasets_data = datasets_response.json()
                print(f"[OK] Datasets access successful!")
                print(f"   Dataset count: {len(datasets_data.get('datasets', []))}")
            else:
                print(f"[FAIL] Datasets access failed!")
                print(f"   Response: {datasets_response.text}")
            
            # Test simulations endpoint
            simulations_response = requests.get(
                f"{BASE_URL}/simulations",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )
            
            print(f"Simulations Status Code: {simulations_response.status_code}")
            if simulations_response.status_code == 200:
                simulations_data = simulations_response.json()
                print(f"[OK] Simulations access successful!")
                print(f"   Simulation count: {len(simulations_data.get('simulations', []))}")
            else:
                print(f"[FAIL] Simulations access failed!")
                print(f"   Response: {simulations_response.text}")
                
        else:
            print(f"[FAIL] Login failed!")
            print(f"   Response: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Connection failed! Is the backend server running?")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False
    
    return True

def test_invalid_token():
    """Test behavior with invalid tokens."""
    print("\n\nTesting Invalid Token Handling")
    print("=" * 50)
    
    invalid_tokens = [
        "",
        "invalid_token",
        "Bearer invalid_token",
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature"
    ]
    
    for i, token in enumerate(invalid_tokens, 1):
        print(f"\n{i}. Testing invalid token: '{token[:20]}{'...' if len(token) > 20 else ''}'")
        
        response = requests.get(
            f"{BASE_URL}/datasets",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 401:
            print("   [OK] Correctly rejected invalid token")
        else:
            print("   [FAIL] Should have returned 401")

def test_token_format():
    """Test different Authorization header formats."""
    print("\n\nTesting Authorization Header Formats")
    print("=" * 50)
    
    # First get a valid token
    credentials = {
        "username": "Alio", 
        "password": "XmP6_6afz:NqTzT"
    }
    
    login_response = requests.post(f"{BASE_URL}/auth/login", json=credentials)
    if login_response.status_code != 200:
        print("[FAIL] Could not get valid token for testing")
        return
    
    token = login_response.json().get('token')
    
    test_cases = [
        ("Bearer {token}", "Standard Bearer format"),
        ("bearer {token}", "Lowercase bearer"),
        ("{token}", "Token only (no Bearer)"),
        ("Token {token}", "Token prefix instead of Bearer"),
    ]
    
    for auth_format, description in test_cases:
        print(f"\nTesting: {description}")
        auth_header = auth_format.format(token=token)
        
        response = requests.get(
            f"{BASE_URL}/auth/profile",
            headers={
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   [OK] Format accepted")
        else:
            print("   [FAIL] Format rejected")

if __name__ == "__main__":
    print("Authentication Flow Debug Tool")
    print("This tool helps diagnose authentication issues")
    print("between the frontend and backend.")
    print("\nMake sure the backend server is running on localhost:5000")
    
    input("\nPress Enter to start testing...")
    
    try:
        success = test_auth_flow()
        if success:
            test_invalid_token()
            test_token_format()
            
            print("\n\nAuthentication Flow Test Complete!")
            print("\nIf all tests passed, the authentication system is working correctly.")
            print("If tests failed, check the specific error messages above.")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()