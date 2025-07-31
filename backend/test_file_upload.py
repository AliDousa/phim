#!/usr/bin/env python3
"""
Test script for file upload functionality with actual CSV file.
"""

import requests
import json
from pathlib import Path

def test_file_upload():
    """Test file upload with actual CSV data."""
    try:
        # Test login first
        login_data = {'username': 'Alio', 'password': 'XmP6_6afz:NqTzT'}
        login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data, timeout=10)
        print(f'Login status: {login_response.status_code}')
        
        if login_response.status_code != 200:
            print(f'[ERROR] Login failed: {login_response.text}')
            return False
            
        token = login_response.json().get('token')
        
        # Test file upload with form data
        test_file = Path('test_datasets/small_test_dataset.csv')
        if not test_file.exists():
            print(f'[ERROR] Test file not found: {test_file}')
            return False
        
        # Prepare form data for file upload
        files = {'file': open(test_file, 'rb')}
        form_data = {
            'name': 'Small Test Dataset Upload',
            'description': 'Testing actual file upload functionality',
            'data_type': 'time_series',
            'source': 'File upload test',
            'column_mapping': json.dumps({
                'timestamp_col': 'date',
                'location_col': 'location',
                'new_cases_col': 'new_cases',
                'new_deaths_col': 'new_deaths',
                'population_col': 'population'
            })
        }
        
        headers = {'Authorization': f'Bearer {token}'}
        
        print('Testing file upload...')
        upload_response = requests.post(
            'http://localhost:5000/api/datasets/upload',
            files=files,
            data=form_data,
            headers=headers,
            timeout=30
        )
        
        files['file'].close()  # Close the file
        
        print(f'Upload status: {upload_response.status_code}')
        
        if upload_response.status_code in [200, 201]:
            print('[SUCCESS] File upload successful!')
            response_data = upload_response.json()
            dataset = response_data.get('dataset', {})
            print(f'Dataset ID: {dataset.get("id")}')
            print(f'Records processed: {response_data.get("records_processed", 0)}')
            print(f'Processing status: {dataset.get("processing_status")}')
            return True
        else:
            print(f'[ERROR] Upload failed: {upload_response.text}')
            return False
            
    except Exception as e:
        print(f'[ERROR] Test failed: {e}')
        return False

if __name__ == '__main__':
    test_file_upload()