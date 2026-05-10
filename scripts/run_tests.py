#!/usr/bin/env python
"""Quick test runner for HospFlow"""
import subprocess
import sys

def run_tests():
    """Run all tests with proper settings"""
    print("Running HospFlow Test Suite...")
    print("=" * 50)

    # Set test settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hospflow.settings_test")

    # Run migrations first
    print("Setting up test database...")
    subprocess.run([sys.executable, "manage.py", "migrate", "--run-syncdb"], check=True)

    # Run tests
    print("Running tests...")
    result = subprocess.run(
        [sys.executable, "manage.py", "test", "--settings=hospflow.settings_test", "-v", "2"],
        capture_output=False
    )

    return result.returncode

if __name__ == "__main__":
    import os
    sys.exit(run_tests())
