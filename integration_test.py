"""
Simple smoke test script to verify project integrity and basic functionality.
"""

import sys
import os
import requests
import time
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_backend_startup():
    """Test if backend starts correctly."""
    print("\nTesting backend startup...")

    backend_dir = os.path.join(SCRIPT_DIR, "backend")
    python_executable = os.path.join(backend_dir, "venv", "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(backend_dir, "venv", "bin", "python")
    main_script = os.path.join(backend_dir, "src", "main.py")

    if not os.path.exists(python_executable):
        print(f"✗ Python executable not found at {python_executable}")
        print("  Please run the setup script first.")
        return False

    # Attempt to kill any existing process on port 5000
    print("  Attempting to free up port 5000...")
    if sys.platform == "win32":
        subprocess.run('taskkill /F /IM python.exe /T 2>nul', shell=True, check=False)
    else:
        subprocess.run("lsof -t -i:5000 | xargs kill -9", shell=True, check=False)
    time.sleep(2)

    # Start backend
    env = os.environ.copy()
    env["FLASK_ENV"] = "development"

    process = subprocess.Popen(
        [python_executable, main_script],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for startup
    print("  Waiting for backend to start...")
    time.sleep(10) # Give it a bit more time to initialize db etc.

    # Test health endpoint
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        if response.status_code == 200:
            print(f"✓ Backend health check passed. Status: {response.json().get('status')}")
            return True
        else:
            print(f"✗ Backend health check failed with status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Backend connection failed: {e}")
        print("  Is the backend running? Check the logs.")
        stderr = process.stderr.read().decode('utf-8', errors='ignore')
        if stderr:
            print("\n--- Backend Error Log ---")
            print(stderr)
            print("------------------------")
        return False
    finally:
        # Clean up
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_frontend_build():
    """Test if frontend builds correctly."""
    print("\nTesting frontend build...")
    frontend_dir = os.path.join(SCRIPT_DIR, "frontend")
    npm_command = "npm.cmd" if sys.platform == "win32" else "npm"

    try:
        result = subprocess.run(
            [npm_command, "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print("✓ Frontend build successful")
            return True
        else:
            print("✗ Frontend build failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Frontend build timed out")
        return False
    except Exception as e:
        print(f"✗ Frontend build error: {e}")
        return False


def test_windows_compatibility():
    """Test Windows-specific features."""
    print("\nTesting Windows compatibility...")
    project_dir = SCRIPT_DIR
    
    windows_files = ["setup.bat", "WINDOWS_SETUP.md", "README.md"]

    all_exist = True
    for file in windows_files:
        file_path = os.path.join(project_dir, file)
        if os.path.exists(file_path):
            print(f"✓ {file} exists")
        else: # pragma: no cover
            print(f"✗ {file} missing")
            all_exist = False

    # Check requirements.txt
    req_file = os.path.join(project_dir, "backend", "requirements.txt")
    if os.path.exists(req_file):
        print("✓ requirements.txt exists")
        with open(req_file, "r") as f:
            content = f.read()
            if "Flask" in content and "scikit-learn" in content:
                print("✓ Key dependencies found in requirements.txt")
            else:
                print("✗ Missing key dependencies in requirements.txt") # pragma: no cover
                all_exist = False
    else:
        print("✗ requirements.txt missing")
        all_exist = False

    return all_exist


def main():
    """Run all tests."""
    print("=" * 60)
    print("Public Health Intelligence Platform - Integration Tests")
    print("=" * 60)

    tests_passed = 0
    total_tests = 3

    # Test 1: Windows compatibility
    if test_windows_compatibility(): # pragma: no branch
        tests_passed += 1

    # Test 2: Frontend build
    if test_frontend_build(): # pragma: no branch
        tests_passed += 1

    # Test 3: Backend startup
    if test_backend_startup(): # pragma: no branch
        tests_passed += 1

    print("\n" + "=" * 60)
    print(f"Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Platform is ready for Windows deployment.")
    else:
        print("✗ Some tests failed. Please check the issues above.")

    print("=" * 60)

    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
