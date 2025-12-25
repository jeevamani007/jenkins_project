"""
Test runner that executes all test suites
"""
import sys
import os
import json
from datetime import datetime

# Add tests directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import available test suites
try:
    from test_full_application import TestFullApplication
    FULL_APP_AVAILABLE = True
except ImportError:
    FULL_APP_AVAILABLE = False
    print("⚠️  test_full_application.py not found")

# Optional test suites (if they exist)
try:
    from test_server import TestServer
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False

try:
    from test_login import TestLogin
    LOGIN_AVAILABLE = True
except ImportError:
    LOGIN_AVAILABLE = False

try:
    from test_signup import TestSignup
    SIGNUP_AVAILABLE = True
except ImportError:
    SIGNUP_AVAILABLE = False

try:
    from test_upload import TestUpload
    UPLOAD_AVAILABLE = True
except ImportError:
    UPLOAD_AVAILABLE = False

try:
    from test_results_page import test_esults_page
    RESULTS_AVAILABLE = True
except ImportError:
    RESULTS_AVAILABLE = False

class TestRunner:
    """Main test runner"""
    
    def __init__(self):
        self.all_results = []
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = datetime.now()
        
        print("=" * 60)
        print("Starting Test Suite Execution")
        print("=" * 60)
        
        test_count = 0
        
        # Run server tests first (if available)
        if SERVER_AVAILABLE:
            test_count += 1
            print(f"\n[{test_count}] Running Server Loading Tests...")
            server_tests = TestServer()
            server_results = server_tests.run_all_tests()
            self.all_results.extend(server_results)
        
        # Run login tests (if available)
        if LOGIN_AVAILABLE:
            test_count += 1
            print(f"[{test_count}] Running Login Tests...")
            login_tests = TestLogin()
            login_results = login_tests.run_all_tests()
            self.all_results.extend(login_results)
        
        # Run signup tests (if available)
        if SIGNUP_AVAILABLE:
            test_count += 1
            print(f"[{test_count}] Running Signup Tests...")
            signup_tests = TestSignup()
            signup_results = signup_tests.run_all_tests()
            self.all_results.extend(signup_results)
        
        # Run upload tests (if available)
        if UPLOAD_AVAILABLE:
            test_count += 1
            print(f"[{test_count}] Running Upload Tests...")
            upload_tests = TestUpload()
            upload_results = upload_tests.run_all_tests()
            self.all_results.extend(upload_results)
        
        # Run results page tests (if available)
        if RESULTS_AVAILABLE:
            test_count += 1
            print(f"[{test_count}] Running Results Page Tests...")
            results_tests = TestResultsPage()
            results_page_results = results_tests.run_all_tests()
            self.all_results.extend(results_page_results)
        
        # Run full application flow tests (always run if available)
        if FULL_APP_AVAILABLE:
            test_count += 1
            print(f"[{test_count}] Running Full Application Flow Tests...")
            full_app_tests = TestFullApplication()
            full_app_results = full_app_tests.run_all_tests()
            self.all_results.extend(full_app_results)
        else:
            print("\n⚠️  No test suites found! Make sure test files exist in tests/ directory.")
        
        self.end_time = datetime.now()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.all_results)
        passed = len([r for r in self.all_results if r["status"] == "pass"])
        failed = len([r for r in self.all_results if r["status"] == "fail"])
        errors = len([r for r in self.all_results if r["status"] == "error"])
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        summary = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "duration": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "results": self.all_results
        }
        
        return summary
    
    def save_results(self, filename="test_results.json"):
        """Save test results to JSON file"""
        summary = self.generate_summary()
        os.makedirs("tests/results", exist_ok=True)
        filepath = f"tests/results/{filename}"
        
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)
        
        return filepath

if __name__ == "__main__":
    runner = TestRunner()
    summary = runner.run_all_tests()
    
    print("\n" + "=" * 60)
    print("Test Execution Summary")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Errors: {summary['errors']}")
    print(f"Duration: {summary['duration']:.2f} seconds")
    print("=" * 60)
    
    # Save results
    result_file = runner.save_results()
    print(f"\nResults saved to: {result_file}")
    
    # Results saved, ready for dashboard display

