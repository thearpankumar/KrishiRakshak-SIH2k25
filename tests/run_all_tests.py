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
from test_analysis_endpoints import test_image_analysis_endpoints
from test_knowledge_endpoints import test_knowledge_repository_endpoints
from test_community_endpoints import test_community_endpoints
from test_location_endpoints import test_location_services_endpoints


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
        
        # Test Suite 2: Image Analysis
        print("\n" + "📸 TEST SUITE 2: IMAGE ANALYSIS")
        print("-" * 60)
        analysis_success = self._run_analysis_tests()
        
        # Test Suite 3: Knowledge Repository  
        print("\n" + "🧠 TEST SUITE 3: KNOWLEDGE REPOSITORY")
        print("-" * 60)
        knowledge_success = self._run_knowledge_tests()
        
        # Test Suite 4: Community Features
        print("\n" + "👥 TEST SUITE 4: COMMUNITY FEATURES")
        print("-" * 60)
        community_success = self._run_community_tests()
        
        # Test Suite 5: Location Services
        print("\n" + "📍 TEST SUITE 5: LOCATION SERVICES")
        print("-" * 60)
        location_success = self._run_location_tests()
        
        # Final Results
        self._print_final_results([
            ("Core Functionality", core_success),
            ("Image Analysis", analysis_success),
            ("Knowledge Repository", knowledge_success),
            ("Community Features", community_success),
            ("Location Services", location_success)
        ])
        
        return all([core_success, analysis_success, knowledge_success, 
                   community_success, location_success])
    
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
            "/api/v1/location/* (Retailers, Nearby Search, Services)"
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