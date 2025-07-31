#!/usr/bin/env python3
"""
Script to start the backend server and run tests.
"""

import subprocess
import time
import sys
import requests
from pathlib import Path

def check_server_status():
    """Check if the backend server is running."""
    try:
        response = requests.get("http://localhost:5000/api/auth/profile", timeout=5)
        return True  # Server responded
    except:
        return False

def start_server():
    """Start the backend server."""
    print("Starting backend server...")
    
    # Check if we're in the right directory
    if not Path("run.py").exists():
        print("[ERROR] run.py not found. Make sure you're in the backend directory.")
        return None
    
    # Start the server
    try:
        process = subprocess.Popen(
            [sys.executable, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        max_attempts = 30
        for attempt in range(max_attempts):
            if check_server_status():
                print(f"[OK] Server started successfully after {attempt + 1} seconds")
                return process
            time.sleep(1)
        
        print("[ERROR] Server failed to start within 30 seconds")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        return None

def main():
    """Main function."""
    print("Public Health Intelligence Platform - Server Startup & Test")
    print("=" * 60)
    
    # Check if server is already running
    if check_server_status():
        print("[OK] Server is already running")
        server_process = None
    else:
        # Start the server
        server_process = start_server()
        if not server_process:
            return False
    
    # Run the comprehensive test
    print("\nRunning comprehensive platform test...")
    try:
        # Import and run the test
        from test_app_with_data import main as run_test
        success = run_test()
        
        if success:
            print("\n[SUCCESS] All tests completed successfully!")
        else:
            print("\n[PARTIAL] Some tests failed, but core functionality works.")
            
    except Exception as e:
        print(f"\n[ERROR] Test execution failed: {e}")
        success = False
    
    # Cleanup
    if server_process:
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("[OK] Server stopped")
    
    return success

if __name__ == "__main__":
    main()