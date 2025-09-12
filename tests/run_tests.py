#!/usr/bin/env python3
"""
Test runner script for Digital Krishi Officer API.
Supports both container testing and local testing.
"""

import sys
import argparse
import time
import requests
from test_container_endpoints import DigitalKrishiTester


def wait_for_service(url: str, timeout: int = 120) -> bool:
    """Wait for the service to be ready."""
    
    print(f"⏳ Waiting for service at {url} to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Service is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("⏳ Service not ready, waiting 5 seconds...")
        time.sleep(5)
    
    print(f"❌ Service failed to become ready within {timeout} seconds")
    return False


def main():
    """Main test runner function."""
    
    parser = argparse.ArgumentParser(description="Digital Krishi Officer API Test Runner")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--wait", 
        action="store_true",
        help="Wait for service to be ready before running tests"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds to wait for service (default: 120)"
    )
    
    args = parser.parse_args()
    
    # Wait for service if requested
    if args.wait:
        if not wait_for_service(args.url, args.timeout):
            sys.exit(1)
    
    # Update test configuration
    from test_container_endpoints import TestConfig
    TestConfig.BASE_URL = args.url
    
    # Run tests
    print(f"\n🧪 Running Digital Krishi Officer API Tests")
    print(f"🎯 Target URL: {args.url}")
    print("=" * 60)
    
    tester = DigitalKrishiTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()