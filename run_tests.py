#!/usr/bin/env python3
"""
Simple test runner that starts the mock server and runs tests.
"""

import subprocess
import time
import sys
import os

# Change to chatbot_tester directory
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/chatbot_tester")

def start_server():
    """Start the mock server in background."""
    print("Starting mock ChatBot server...")
    server_process = subprocess.Popen(
        [sys.executable, "../mock_chatbot_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    return server_process

def run_tests():
    """Run pytest with HTML report."""
    print("\n" + "="*60)
    print("Running ChatBot Tester Framework Tests")
    print("="*60 + "\n")

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_functional.py",
        "-v", "--tb=short",
        "--html=reports/report.html",
        "--self-contained-html",
        "-k", "test_greeting_response or test_health_endpoint or test_error_handling"
    ], cwd=".")

    return result.returncode == 0

if __name__ == "__main__":
    server = start_server()

    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    finally:
        print("\nStopping mock server...")
        server.terminate()
        server.wait()