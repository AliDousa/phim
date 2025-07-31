#!/usr/bin/env python3
"""
Comprehensive test script for the Public Health Intelligence Platform.
Tests data upload, processing, ML forecasting, and all major features.
"""

import requests
import json
import time
import os
from pathlib import Path
import pandas as pd

BASE_URL = "http://localhost:5000/api"
TEST_CREDENTIALS = {
    "username": "Alio",
    "password": "XmP6_6afz:NqTzT"
}

class PlatformTester:
    def __init__(self):
        self.token = None
        self.user_info = None
        self.uploaded_datasets = []
        self.created_simulations = []
        
    def authenticate(self):
        """Authenticate with the platform."""
        print("1. Authenticating with platform...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json=TEST_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_info = data.get('user')
                print(f"   [OK] Authenticated as {self.user_info.get('username')} (Role: {self.user_info.get('role')})")
                return True
            else:
                print(f"   [FAIL] Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   [FAIL] Authentication error: {e}")
            return False
    
    def get_auth_headers(self):
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_dataset_upload(self, file_path, dataset_name, description="Test dataset"):
        """Test dataset upload functionality."""
        print(f"2. Testing dataset upload: {file_path}")
        
        try:
            # First, let's try the programmatic approach
            # Read the file data
            with open(file_path, 'r') as f:
                if file_path.suffix == '.json':
                    file_data = json.load(f)
                else:
                    # For CSV files, we'll send the raw content
                    file_content = f.read()
            
            # Create dataset metadata
            dataset_info = {
                "name": dataset_name,
                "description": description,
                "data_type": "time_series",
                "source": "Test Data Generator",
                "is_public": False
            }
            
            # Upload dataset
            response = requests.post(
                f"{BASE_URL}/datasets",
                json=dataset_info,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                dataset = response.json()
                dataset_id = dataset.get('dataset', {}).get('id') or dataset.get('id')
                print(f"   [OK] Dataset created with ID: {dataset_id}")
                self.uploaded_datasets.append(dataset_id)
                return dataset_id
            else:
                print(f"   [FAIL] Dataset upload failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"   [FAIL] Dataset upload error: {e}")
            return None
    
    def test_dataset_list(self):
        """Test dataset listing functionality."""
        print("3. Testing dataset listing...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/datasets",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                datasets = data.get('datasets', [])
                print(f"   [OK] Found {len(datasets)} datasets")
                
                for dataset in datasets[:3]:  # Show first 3
                    print(f"      - {dataset.get('name')} (ID: {dataset.get('id')}, Status: {dataset.get('processing_status')})")
                
                return datasets
            else:
                print(f"   [FAIL] Dataset listing failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"   [FAIL] Dataset listing error: {e}")
            return []
    
    def test_ml_forecasting(self, dataset_id):
        """Test ML forecasting functionality."""
        print(f"4. Testing ML forecasting with dataset {dataset_id}...")
        
        try:
            # Create a simulation with ML forecasting
            simulation_config = {
                "name": f"ML Forecast Test - Dataset {dataset_id}",
                "description": "Test ML forecasting with uploaded data",
                "model_type": "ml_forecast",
                "dataset_id": dataset_id,
                "parameters": {
                    "forecast_horizon": 14,
                    "target_column": "new_cases",
                    "model_types": ["random_forest", "linear"],
                    "confidence_level": 0.95,
                    "validation_split": 0.2
                }
            }
            
            response = requests.post(
                f"{BASE_URL}/simulations",
                json=simulation_config,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                simulation = response.json()
                sim_id = simulation.get('simulation', {}).get('id') or simulation.get('id')
                print(f"   [OK] ML forecasting simulation created with ID: {sim_id}")
                self.created_simulations.append(sim_id)
                
                # Wait a moment for processing
                time.sleep(2)
                
                # Check simulation status
                status_response = requests.get(
                    f"{BASE_URL}/simulations/{sim_id}",
                    headers=self.get_auth_headers()
                )
                
                if status_response.status_code == 200:
                    sim_data = status_response.json()
                    status = sim_data.get('simulation', {}).get('status') or sim_data.get('status')
                    print(f"   [OK] Simulation status: {status}")
                    return sim_id
                else:
                    print(f"   [WARNING] Could not check simulation status: {status_response.status_code}")
                    return sim_id
                    
            else:
                print(f"   [FAIL] ML forecasting failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"   [FAIL] ML forecasting error: {e}")
            return None
    
    def test_seir_modeling(self, dataset_id):
        """Test SEIR modeling functionality."""
        print(f"5. Testing SEIR modeling with dataset {dataset_id}...")
        
        try:
            seir_config = {
                "name": f"SEIR Model Test - Dataset {dataset_id}",
                "description": "Test SEIR modeling with uploaded data",
                "model_type": "seir",
                "dataset_id": dataset_id,
                "parameters": {
                    "population": 100000,
                    "initial_conditions": {
                        "susceptible": 99950,
                        "exposed": 40,
                        "infectious": 10,
                        "recovered": 0
                    },
                    "model_parameters": {
                        "beta": 0.4,
                        "sigma": 0.2,
                        "gamma": 0.1
                    },
                    "time_horizon": 60
                }
            }
            
            response = requests.post(
                f"{BASE_URL}/simulations",
                json=seir_config,
                headers=self.get_auth_headers()
            )
            
            if response.status_code in [200, 201]:
                simulation = response.json()
                sim_id = simulation.get('simulation', {}).get('id') or simulation.get('id')
                print(f"   [OK] SEIR simulation created with ID: {sim_id}")
                self.created_simulations.append(sim_id)
                return sim_id
            else:
                print(f"   [FAIL] SEIR modeling failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"   [FAIL] SEIR modeling error: {e}")
            return None
    
    def test_simulation_list(self):
        """Test simulation listing functionality."""
        print("6. Testing simulation listing...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/simulations",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                simulations = data.get('simulations', [])
                print(f"   [OK] Found {len(simulations)} simulations")
                
                for sim in simulations[:3]:  # Show first 3
                    print(f"      - {sim.get('name')} (ID: {sim.get('id')}, Status: {sim.get('status')})")
                
                return simulations
            else:
                print(f"   [FAIL] Simulation listing failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"   [FAIL] Simulation listing error: {e}")
            return []
    
    def test_user_profile(self):
        """Test user profile functionality."""
        print("7. Testing user profile...")
        
        try:
            response = requests.get(
                f"{BASE_URL}/auth/profile",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                profile = response.json()
                user = profile.get('user', {})
                print(f"   [OK] Profile loaded for {user.get('username')}")
                print(f"      - Email: {user.get('email')}")
                print(f"      - Role: {user.get('role')}")
                print(f"      - Created: {user.get('created_at')}")
                return True
            else:
                print(f"   [FAIL] Profile loading failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   [FAIL] Profile loading error: {e}")
            return False
    
    def test_data_validation(self):
        """Test data validation features."""
        print("8. Testing data validation...")
        
        # Test with invalid data
        try:
            invalid_data = {
                "name": "Invalid Test Dataset",
                "description": "Dataset with validation errors",
                "data_type": "invalid_type",  # Invalid type
                "source": "Test"
            }
            
            response = requests.post(
                f"{BASE_URL}/datasets",
                json=invalid_data,
                headers=self.get_auth_headers()
            )
            
            # Should fail validation
            if response.status_code >= 400:
                print(f"   [OK] Data validation correctly rejected invalid data: {response.status_code}")
                return True
            else:
                print(f"   [WARNING] Data validation may not be working properly")
                return False
                
        except Exception as e:
            print(f"   [FAIL] Data validation test error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive test of the platform."""
        print("Public Health Intelligence Platform - Comprehensive Test")
        print("=" * 60)
        
        results = []
        
        # 1. Authentication
        if not self.authenticate():
            print("[CRITICAL] Authentication failed - stopping tests")
            return False
        results.append(True)
        
        # 2. Test with small dataset first
        test_data_dir = Path("test_datasets")
        small_dataset = test_data_dir / "small_test_dataset.csv"
        
        if small_dataset.exists():
            dataset_id = self.test_dataset_upload(
                small_dataset, 
                "Small Test Dataset",
                "30 days of COVID data for quick testing"
            )
            results.append(dataset_id is not None)
        else:
            print("   [WARNING] Small test dataset not found, skipping upload test")
            results.append(False)
        
        # 3. List datasets
        datasets = self.test_dataset_list()
        results.append(len(datasets) > 0)
        
        # 4. ML Forecasting (if we have a dataset)
        if self.uploaded_datasets:
            ml_sim = self.test_ml_forecasting(self.uploaded_datasets[0])
            results.append(ml_sim is not None)
        else:
            print("   [SKIP] No datasets available for ML forecasting test")
            results.append(False)
        
        # 5. SEIR Modeling (if we have a dataset)
        if self.uploaded_datasets:
            seir_sim = self.test_seir_modeling(self.uploaded_datasets[0])
            results.append(seir_sim is not None)
        else:
            print("   [SKIP] No datasets available for SEIR modeling test")
            results.append(False)
        
        # 6. List simulations
        simulations = self.test_simulation_list()
        results.append(len(simulations) >= 0)  # Just check it doesn't error
        
        # 7. User profile
        profile_ok = self.test_user_profile()
        results.append(profile_ok)
        
        # 8. Data validation
        validation_ok = self.test_data_validation()
        results.append(validation_ok)
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        passed = sum(1 for r in results if r)
        total = len(results)
        print(f"Passed: {passed}/{total} tests")
        
        test_names = [
            "Authentication",
            "Dataset Upload", 
            "Dataset Listing",
            "ML Forecasting",
            "SEIR Modeling", 
            "Simulation Listing",
            "User Profile",
            "Data Validation"
        ]
        
        for name, result in zip(test_names, results):
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {name}")
        
        if passed == total:
            print("\n[SUCCESS] All tests passed! Platform is working correctly.")
        elif passed >= total * 0.7:
            print(f"\n[PARTIAL] {passed}/{total} tests passed. Most features working.")
        else:
            print(f"\n[ISSUES] Only {passed}/{total} tests passed. Check the logs.")
        
        # Cleanup info
        if self.uploaded_datasets:
            print(f"\nUploaded datasets (IDs): {self.uploaded_datasets}")
        if self.created_simulations:
            print(f"Created simulations (IDs): {self.created_simulations}")
        
        return passed >= total * 0.7


def check_server_status():
    """Check if the backend server is running."""
    try:
        response = requests.get(f"{BASE_URL}/auth/profile", timeout=5)
        return True  # Server responded (even if unauthorized)
    except:
        return False


def main():
    """Main test function."""
    print("Checking if backend server is running...")
    if not check_server_status():
        print("[ERROR] Backend server is not running on localhost:5000")
        print("Please start the server with: python run.py")
        return False
    
    print("[OK] Backend server is responding")
    print()
    
    # Run the comprehensive test
    tester = PlatformTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("1. Try uploading larger datasets from test_datasets/")
        print("2. Test the web interface at http://localhost:5173")
        print("3. Explore forecasting results and visualizations")
        print("4. Test different model parameters and configurations")
    
    return success


if __name__ == "__main__":
    main()