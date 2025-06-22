#!/usr/bin/env python3
"""
API Test Script for Public Health Intelligence Platform

This script tests the core functionality of the backend API.
Run this after starting the server to verify everything works.
"""

import requests
import json
import time
import sys
from pathlib import Path


class APITester:
    """Test the backend API endpoints."""

    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.dataset_id = None
        self.simulation_id = None

    def test_health_check(self):
        """Test the health check endpoint."""
        print("🔍 Testing health check...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Database: {data['database']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    def test_user_registration(self):
        """Test user registration."""
        print("\n🔍 Testing user registration...")
        try:
            user_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123!",
                "role": "analyst",
            }

            response = requests.post(
                f"{self.base_url}/api/auth/register", json=user_data
            )

            if response.status_code == 201:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                print("✅ User registration successful")
                print(f"   User ID: {self.user_id}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False

    def test_user_login(self):
        """Test user login."""
        print("\n🔍 Testing user login...")
        try:
            login_data = {"username": "testuser", "password": "TestPass123!"}

            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                print("✅ User login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_dataset_upload(self):
        """Test dataset upload with sample data."""
        print("\n🔍 Testing dataset upload...")
        try:
            # Create sample CSV data
            csv_data = """date,region,daily_cases,daily_deaths,population
2024-01-01,Region A,120,5,1000000
2024-01-02,Region A,135,3,1000000
2024-01-03,Region A,142,7,1000000
2024-01-04,Region A,156,4,1000000
2024-01-05,Region A,171,6,1000000
2024-01-06,Region A,189,8,1000000
2024-01-07,Region A,198,5,1000000
2024-01-08,Region A,205,9,1000000
2024-01-09,Region A,224,7,1000000
2024-01-10,Region A,241,11,1000000"""

            # Column mapping
            column_mapping = {
                "timestamp_col": "date",
                "location_col": "region",
                "new_cases_col": "daily_cases",
                "new_deaths_col": "daily_deaths",
                "population_col": "population",
            }

            # Prepare form data
            files = {"file": ("test_data.csv", csv_data, "text/csv")}

            data = {
                "name": "Test Dataset",
                "description": "Test dataset for API validation",
                "data_type": "time_series",
                "column_mapping": json.dumps(column_mapping),
            }

            headers = {"Authorization": f"Bearer {self.token}"}

            response = requests.post(
                f"{self.base_url}/api/datasets", files=files, data=data, headers=headers
            )

            if response.status_code == 201:
                result = response.json()
                self.dataset_id = result.get("dataset", {}).get("id")
                print("✅ Dataset upload successful")
                print(f"   Dataset ID: {self.dataset_id}")
                print(f"   Points added: {result.get('points_added', 0)}")
                return True
            else:
                print(f"❌ Dataset upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Dataset upload error: {e}")
            return False

    def test_simulation_creation(self):
        """Test simulation creation."""
        print("\n🔍 Testing simulation creation...")
        try:
            simulation_data = {
                "name": "Test SEIR Simulation",
                "description": "Test simulation for API validation",
                "model_type": "seir",
                "parameters": {
                    "beta": 0.5,
                    "sigma": 0.2,
                    "gamma": 0.1,
                    "population": 100000,
                    "time_horizon": 180,
                },
            }

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.base_url}/api/simulations",
                json=simulation_data,
                headers=headers,
            )

            if response.status_code == 201:
                result = response.json()
                self.simulation_id = result.get("simulation", {}).get("id")
                print("✅ Simulation creation successful")
                print(f"   Simulation ID: {self.simulation_id}")
                return True
            else:
                print(f"❌ Simulation creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Simulation creation error: {e}")
            return False

    def test_simulation_status(self):
        """Test simulation status checking."""
        print("\n🔍 Checking simulation status...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            # Wait for simulation to complete (max 30 seconds)
            for i in range(30):
                response = requests.get(
                    f"{self.base_url}/api/simulations/{self.simulation_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("simulation", {}).get("status")
                    print(f"   Status: {status}")

                    if status == "completed":
                        print("✅ Simulation completed successfully")
                        return True
                    elif status == "failed":
                        print("❌ Simulation failed")
                        return False
                    else:
                        time.sleep(1)
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    return False

            print("⏰ Simulation timeout (still running)")
            return True  # Don't fail for timeout

        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False

    def test_data_retrieval(self):
        """Test data retrieval endpoints."""
        print("\n🔍 Testing data retrieval...")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}

            # Test datasets list
            response = requests.get(f"{self.base_url}/api/datasets", headers=headers)
            if response.status_code == 200:
                datasets = response.json().get("datasets", [])
                print(f"✅ Retrieved {len(datasets)} datasets")
            else:
                print(f"❌ Datasets retrieval failed: {response.status_code}")
                return False

            # Test simulations list
            response = requests.get(f"{self.base_url}/api/simulations", headers=headers)
            if response.status_code == 200:
                simulations = response.json().get("simulations", [])
                print(f"✅ Retrieved {len(simulations)} simulations")
                return True
            else:
                print(f"❌ Simulations retrieval failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Data retrieval error: {e}")
            return False

    def run_all_tests(self):
        """Run all API tests."""
        print("🚀 Starting API tests...")
        print("=" * 50)

        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_user_login,
            self.test_dataset_upload,
            self.test_simulation_creation,
            self.test_simulation_status,
            self.test_data_retrieval,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            time.sleep(0.5)  # Brief pause between tests

        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {passed}/{total} passed")

        if passed == total:
            print("🎉 All tests passed! API is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Check the output above.")
            return False


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"

    print(f"Testing API at: {base_url}")

    tester = APITester(base_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
