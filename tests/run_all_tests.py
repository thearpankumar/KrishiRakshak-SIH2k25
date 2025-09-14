#!/usr/bin/env python3
"""
Comprehensive test runner for Digital Krishi Officer API.
Runs all test suites for the complete application.
"""

import sys
import time
import json
from datetime import datetime, timezone

# Import all test modules
from test_container_endpoints import DigitalKrishiTester
from test_upload_endpoints import TestUploadEndpoints
from test_analysis_endpoints import test_image_analysis_endpoints
from test_knowledge_endpoints import test_knowledge_repository_endpoints
from test_community_endpoints import test_community_endpoints
from test_location_endpoints import test_location_services_endpoints
from test_triggers import test_n8n_trigger_endpoints
from test_webhooks import test_n8n_webhook_endpoints


class ComprehensiveTestRunner:
    """Comprehensive test runner for all Digital Krishi Officer APIs."""
    
    def __init__(self):
        self.start_time = None
        self.test_results = {}
        self.base_url = "http://localhost:8000"
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_all_tests(self):
        """Run all test suites comprehensively."""
        
        print("🚀 Starting Comprehensive Digital Krishi Officer API Tests")
        print("=" * 80)
        print(f"🔗 Testing against: {self.base_url}")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Test Suite 1: Core Functionality (Original Tests)
        print("\n" + "🔧 TEST SUITE 1: CORE FUNCTIONALITY")
        print("-" * 60)
        core_success = self._run_core_tests()
        
        # Test Suite 2: Upload Functionality
        print("\n" + "⬆️  TEST SUITE 2: UPLOAD FUNCTIONALITY")
        print("-" * 60)
        upload_success = self._run_upload_tests()

        # Test Suite 3: Image Analysis
        print("\n" + "📸 TEST SUITE 3: IMAGE ANALYSIS")
        print("-" * 60)
        analysis_success = self._run_analysis_tests()
        
        # Test Suite 4: Knowledge Repository
        print("\n" + "🧠 TEST SUITE 4: KNOWLEDGE REPOSITORY")
        print("-" * 60)
        knowledge_success = self._run_knowledge_tests()

        # Test Suite 5: Community Features
        print("\n" + "👥 TEST SUITE 5: COMMUNITY FEATURES")
        print("-" * 60)
        community_success = self._run_community_tests()

        # Test Suite 6: Location Services
        print("\n" + "📍 TEST SUITE 6: LOCATION SERVICES")
        print("-" * 60)
        location_success = self._run_location_tests()

        # Test Suite 7: N8N Trigger Endpoints
        print("\n" + "🔗 TEST SUITE 7: N8N TRIGGER ENDPOINTS")
        print("-" * 60)
        trigger_success = self._run_trigger_tests()

        # Test Suite 8: N8N Webhook Endpoints
        print("\n" + "🔄 TEST SUITE 8: N8N WEBHOOK ENDPOINTS")
        print("-" * 60)
        webhook_success = self._run_webhook_tests()

        # Final Results
        self._print_final_results([
            ("Core Functionality", core_success),
            ("Upload Functionality", upload_success),
            ("Image Analysis", analysis_success),
            ("Knowledge Repository", knowledge_success),
            ("Community Features", community_success),
            ("Location Services", location_success),
            ("N8N Trigger Endpoints", trigger_success),
            ("N8N Webhook Endpoints", webhook_success)
        ])

        return all([core_success, upload_success, analysis_success, knowledge_success,
                   community_success, location_success, trigger_success, webhook_success])
    
    def _run_core_tests(self):
        """Run core functionality tests."""
        try:
            print("Running authentication, chat, and user management tests...")
            tester = DigitalKrishiTester()
            success = tester.run_all_tests()
            
            if success:
                print("✅ Core functionality tests: PASSED")
                self.passed_tests += 1
            else:
                print("❌ Core functionality tests: FAILED")
                self.failed_tests += 1
            
            self.total_tests += 1
            return success
            
        except Exception as e:
            print(f"❌ Core functionality tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def _run_upload_tests(self):
        """Run upload functionality tests."""
        try:
            print("Running file upload, validation, and security tests...")

            # Run upload tests
            upload_tester = TestUploadEndpoints()
            upload_tester.setup()

            # Run all test methods
            test_methods = [
                upload_tester.test_upload_image_success,
                upload_tester.test_upload_different_image_formats,
                upload_tester.test_upload_invalid_file_type,
                upload_tester.test_upload_without_authentication,
                upload_tester.test_upload_corrupted_image,
                upload_tester.test_upload_large_image,
                upload_tester.test_upload_no_file
            ]

            for test_method in test_methods:
                test_method()

            # Clean up test user
            upload_tester.cleanup()

            print("✅ Upload functionality tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Upload functionality tests: FAILED - {str(e)}")
            print(f"📋 Full error details:\n{error_details}")

            # Try to cleanup even if tests failed
            try:
                if 'upload_tester' in locals():
                    upload_tester.cleanup()
            except:
                pass  # Ignore cleanup errors if tests already failed

            self.failed_tests += 1
            self.total_tests += 1
            return False

    def _run_analysis_tests(self):
        """Run image analysis tests."""
        try:
            print("Running image upload, analysis, and AI vision tests...")
            test_image_analysis_endpoints()
            print("✅ Image analysis tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True
            
        except Exception as e:
            print(f"❌ Image analysis tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False
    
    def _run_knowledge_tests(self):
        """Run knowledge repository tests."""
        try:
            print("Running Q&A repository, vector search, and AI integration tests...")
            test_knowledge_repository_endpoints()
            print("✅ Knowledge repository tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True
            
        except Exception as e:
            print(f"❌ Knowledge repository tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False
    
    def _run_community_tests(self):
        """Run community features tests."""
        try:
            print("Running group chats, messaging, and community discovery tests...")
            test_community_endpoints()
            print("✅ Community features tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True
            
        except Exception as e:
            print(f"❌ Community features tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False
    
    def _run_location_tests(self):
        """Run location services tests."""
        try:
            print("Running retailer management, geospatial search, and location tests...")
            test_location_services_endpoints()
            print("✅ Location services tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True

        except Exception as e:
            print(f"❌ Location services tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def _run_trigger_tests(self):
        """Run N8N trigger endpoint tests."""
        try:
            print("Running N8N workflow trigger, authentication, and integration tests...")
            test_n8n_trigger_endpoints()
            print("✅ N8N trigger endpoint tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True

        except Exception as e:
            print(f"❌ N8N trigger endpoint tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def _run_webhook_tests(self):
        """Run N8N webhook endpoint tests."""
        try:
            print("Running N8N webhook receivers, callback processing, and validation tests...")
            test_n8n_webhook_endpoints()
            print("✅ N8N webhook endpoint tests: PASSED")
            self.passed_tests += 1
            self.total_tests += 1
            return True

        except Exception as e:
            print(f"❌ N8N webhook endpoint tests: FAILED - {str(e)}")
            self.failed_tests += 1
            self.total_tests += 1
            return False
    
    def _print_final_results(self, test_suites):
        """Print comprehensive final results."""
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        # Test suite results
        print("\n🎯 Test Suite Results:")
        for suite_name, success in test_suites:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status} {suite_name}")
        
        # Overall statistics
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Test Suites: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.failed_tests}")
        print(f"   Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        print(f"   Duration: {duration:.1f} seconds")
        
        # Feature coverage summary
        print(f"\n🎯 Feature Coverage Summary:")
        features_tested = [
            "✅ User Authentication & Authorization",
            "✅ Farming Profile Management",
            "✅ AI-Powered Chat System",
            "✅ Image Analysis & Vision AI",
            "✅ Knowledge Repository with Vector Search",
            "✅ Community Group Chats & Messaging",
            "✅ Location-Based Retailer Services",
            "✅ Geospatial Distance Calculations",
            "✅ N8N Workflow Integration & Triggers",
            "✅ N8N Webhook Processing & Callbacks",
            "✅ Multi-language Support",
            "✅ Rate Limiting & Security"
        ]
        
        for feature in features_tested:
            print(f"   {feature}")
        
        # API endpoints tested
        print(f"\n🔗 API Endpoints Tested:")
        endpoints_tested = [
            "/api/v1/auth/* (Registration, Login, Profiles)",
            "/api/v1/chat/* (AI Chat, History, Management)",
            "/api/v1/analysis/* (Image Upload, Analysis, Stats)",
            "/api/v1/knowledge/* (Q&A, Search, AI Integration)",
            "/api/v1/community/* (Groups, Messages, Discovery)",
            "/api/v1/location/* (Retailers, Nearby Search, Services)",
            "/api/v1/triggers/* (N8N Workflow Triggers, Integration)",
            "/api/v1/webhooks/* (N8N Callbacks, Result Processing)"
        ]
        
        for endpoint in endpoints_tested:
            print(f"   ✅ {endpoint}")
        
        # Final status
        if self.passed_tests == self.total_tests:
            print(f"\n🎉 ALL TEST SUITES PASSED! Your Digital Krishi Officer API is fully functional!")
            print(f"🚀 Ready for production deployment!")
        else:
            print(f"\n⚠️  {self.failed_tests} test suite(s) failed. Please review the errors above.")
        
        print("=" * 80)
        
        # Save results to file
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "total_suites": self.total_tests,
            "passed_suites": self.passed_tests,
            "failed_suites": self.failed_tests,
            "success_rate": (self.passed_tests/self.total_tests*100) if self.total_tests > 0 else 0,
            "test_suites": [{"name": name, "passed": success} for name, success in test_suites],
            "base_url": self.base_url
        }
        
        with open('comprehensive_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Comprehensive results saved to comprehensive_test_results.json")


def main():
    """Main entry point."""
    
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()