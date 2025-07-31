#!/usr/bin/env python3
"""
Quick test script for the upload endpoint functionality.
"""

import requests
import json

def test_upload_endpoint():
    """Test the upload endpoint functionality."""
    try:
        # Test server health
        health = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f'Health check: {health.status_code}')
        
        # Test login
        login_data = {'username': 'Alio', 'password': 'XmP6_6afz:NqTzT'}
        login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data, timeout=10)
        print(f'Login status: {login_response.status_code}')
        
        if login_response.status_code == 200:
            token = login_response.json().get('token')
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            
            # Test upload endpoint with OPTIONS (CORS preflight)
            options_response = requests.options('http://localhost:5000/api/datasets/upload', headers=headers, timeout=10)
            print(f'OPTIONS /api/datasets/upload: {options_response.status_code}')
            
            # Test upload endpoint with POST (empty data)
            upload_data = {
                'name': 'Test Dataset',
                'description': 'Test upload endpoint',
                'data_type': 'time_series',
                'source': 'API test'
            }
            upload_response = requests.post('http://localhost:5000/api/datasets/upload', json=upload_data, headers=headers, timeout=10)
            print(f'POST /api/datasets/upload: {upload_response.status_code}')
            
            if upload_response.status_code in [200, 201]:
                print('[SUCCESS] Upload endpoint is working!')
                response_data = upload_response.json()
                print(f'Response: {response_data}')
                return True
            else:
                print(f'[ERROR] Upload failed: {upload_response.text}')
                return False
        else:
            print(f'[ERROR] Login failed: {login_response.text}')
            return False
            
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        return False

if __name__ == '__main__':
    test_upload_endpoint()