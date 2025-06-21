#!/usr/bin/env python3
"""
Test runner script for the Medical Records Management System.
Run from the project root directory: python tests/run_tests.py <test_type>
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, capture_output=False, text=True)
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def show_help():
    """Show help message."""
    print("Medical Records Management System - Test Runner")
    print("=" * 50)
    print("Usage: python tests/run_tests.py <test_type>")
    print("\nAvailable test types:")
    print("  all          - Run all tests")
    print("  auth         - Run authentication tests only")
    print("  api          - Run API tests only")
    print("  patients     - Run patient-related tests")
    print("  medical      - Run medical records tests")
    print("  users        - Run user management tests")
    print("  integration  - Run integration tests only")
    print("  quick        - Run quick tests (excludes slow tests)")
    print("  coverage     - Run tests with coverage report")
    print("  verbose      - Run tests with verbose output")
    print("  file <name>  - Run specific test file")
    print("  help         - Show this help message")


def main():
    """Main test runner function."""
    # Change to project directory (parent of tests directory)
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    test_type = sys.argv[1].lower()
      # Base pytest command - use current Python executable
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if test_type == "all":
        cmd = base_cmd + ["tests/"]
        run_command(cmd, "All Tests")
    
    elif test_type == "auth":
        cmd = base_cmd + ["tests/test_auth.py"]
        run_command(cmd, "Authentication Tests")
    
    elif test_type == "api":
        cmd = base_cmd + ["tests/test_api.py"]
        run_command(cmd, "API Tests")
    
    elif test_type == "patients":
        cmd = base_cmd + ["tests/test_patients.py"]
        run_command(cmd, "Patient-related Tests")
    
    elif test_type == "medical":
        cmd = base_cmd + ["tests/test_medical_records.py"]
        run_command(cmd, "Medical Records Tests")
    
    elif test_type == "users":
        cmd = base_cmd + ["tests/test_users.py"]
        run_command(cmd, "User Management Tests")
    
    elif test_type == "integration":
        cmd = base_cmd + ["tests/test_integration.py"]
        run_command(cmd, "Integration Tests")
    
    elif test_type == "quick":
        cmd = base_cmd + ["-m", "not slow", "tests/"]
        run_command(cmd, "Quick Tests (excluding slow tests)")
    
    elif test_type == "coverage":
        try:
            import importlib.util
            spec = importlib.util.find_spec("pytest_cov")
            if spec is not None:
                cmd = base_cmd + ["--cov=app", "--cov-report=html", "--cov-report=term-missing", "tests/"]
                run_command(cmd, "Tests with Coverage Report")
                print("\nCoverage report generated in htmlcov/ directory")
            else:
                raise ImportError("pytest-cov not found")
        except ImportError:
            print("pytest-cov not installed. Install with: pip install pytest-cov")
            cmd = base_cmd + ["tests/"]
            run_command(cmd, "All Tests (without coverage)")
    
    elif test_type == "verbose":
        cmd = base_cmd + ["-v", "-s", "tests/"]
        run_command(cmd, "Verbose Tests")
    
    elif test_type == "file":
        if len(sys.argv) < 3:
            print("Please specify a test file name")
            print("Usage: python tests/run_tests.py file <test_file_name>")
            return
        
        test_file = sys.argv[2]
        if not test_file.startswith("test_"):
            test_file = f"test_{test_file}"
        if not test_file.endswith(".py"):
            test_file = f"{test_file}.py"
        
        cmd = base_cmd + [f"tests/{test_file}"]
        run_command(cmd, f"Specific Test File: {test_file}")
    
    elif test_type == "help":
        show_help()
    
    else:
        print(f"Unknown test type: {test_type}")
        print("Run 'python tests/run_tests.py help' for available options")


if __name__ == "__main__":
    main()
