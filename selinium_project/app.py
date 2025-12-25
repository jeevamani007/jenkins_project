
"""
Flask server for Test Dashboard
Serves the test dashboard and provides API endpoints to run tests
"""
from flask import Flask, render_template, jsonify, request
import sys
import os
import json
import threading
from datetime import datetime

# Add current directory to path for test imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test runner with error handling
try:
    from test_runner import TestRunner
    from test_server import TestServer
    from test_login import TestLogin
    from test_signup import TestSignup
    from test_upload import TestUpload
    from test_full_application import TestFullApplication
except ImportError as e:
    print(f"Warning: Could not import test modules: {e}")
    print("Make sure all test files are in the tests/ directory")
    TestRunner = None
    TestServer = None
    TestLogin = None
    TestSignup = None
    TestUpload = None
    TestFullApplication = None

app = Flask(__name__, static_folder='static', static_url_path='/static', template_folder='templates')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Store current test execution status
test_status = {
    'running': False,
    'results': None,
    'current_test': None
}

# Test name mapping for better display names
TEST_NAME_MAPPING = {
    'test_server_running': 'Server Running',
    'test_home_page_loads': 'Home Page Loads',
    'test_login_page_loads': 'Login Page Loads',
    'test_signup_page_loads': 'Signup Page Loads',
    'test_page_response_times': 'Page Response Times',
    'test_valid_login': 'Valid Login',
    'test_invalid_credentials': 'Invalid Credentials',
    'test_empty_credentials': 'Empty Credentials',
    'test_valid_signup': 'Valid Signup',
    'test_duplicate_username': 'Duplicate Username',
    'test_empty_fields': 'Empty Signup Fields',
    'test_upload_page_access': 'Upload Page Access',
    'test_upload_form_elements': 'Upload Form Elements',
    'test_simple_file_upload': 'Simple File Upload',
    'test_complete_user_journey': 'Complete User Journey',
    'test_database_connection': 'Database Connection',
    'test_api_endpoints': 'API Endpoints',
    'test_navigation_flow': 'Navigation Flow',
}

# Define all available test cases - dynamically discover test methods
def discover_test_methods(test_class, suite_name):
    """Discover all test methods from a test class"""
    test_cases = []
    if test_class:
        # Get all methods that start with 'test_'
        for method_name in dir(test_class):
            if method_name.startswith('test_') and callable(getattr(test_class, method_name, None)):
                # Use mapping if available, otherwise format from method name
                if method_name in TEST_NAME_MAPPING:
                    name = TEST_NAME_MAPPING[method_name]
                else:
                    # Format method name: test_something -> Something
                    name = method_name.replace('test_', '').replace('_', ' ').title()
                
                test_cases.append({
                    'suite': suite_name,
                    'name': name,
                    'method': method_name,
                    'class': test_class
                })
    return test_cases

# Define all available test cases
TEST_CASES = []

# Discover tests from each class
if TestServer:
    TEST_CASES.extend(discover_test_methods(TestServer, 'Server'))

if TestLogin:
    TEST_CASES.extend(discover_test_methods(TestLogin, 'Login'))

if TestSignup:
    TEST_CASES.extend(discover_test_methods(TestSignup, 'Signup'))

if TestUpload:
    TEST_CASES.extend(discover_test_methods(TestUpload, 'Upload'))

if TestFullApplication:
    TEST_CASES.extend(discover_test_methods(TestFullApplication, 'Full Application'))

# Print debug info
print(f"\n📊 Discovered {len(TEST_CASES)} test cases:")
for tc in TEST_CASES:
    print(f"  - {tc['suite']}: {tc['name']} ({tc['method']})")
print()

@app.route('/')
def index():
    """Redirect to test dashboard"""
    return render_template('test_dashboard.html')

@app.route('/tests')
def test_dashboard():
    """Test dashboard page"""
    return render_template('test_dashboard.html')

@app.route('/api/test-cases', methods=['GET'])
def get_test_cases():
    """Get list of all test cases"""
    # Re-discover test cases in case classes were loaded after server start
    TEST_CASES = []
    
    if TestServer:
        TEST_CASES.extend(discover_test_methods(TestServer, 'Server'))
    if TestLogin:
        TEST_CASES.extend(discover_test_methods(TestLogin, 'Login'))
    if TestSignup:
        TEST_CASES.extend(discover_test_methods(TestSignup, 'Signup'))
    if TestUpload:
        TEST_CASES.extend(discover_test_methods(TestUpload, 'Upload'))
    if TestFullApplication:
        TEST_CASES.extend(discover_test_methods(TestFullApplication, 'Full Application'))
    
    # Convert class objects to strings for JSON serialization (remove class from response)
    test_cases_json = []
    for tc in TEST_CASES:
        test_cases_json.append({
            'suite': tc['suite'],
            'name': tc['name'],
            'method': tc['method']
        })
    
    return jsonify({
        'test_cases': test_cases_json,
        'total': len(TEST_CASES),
        'suites': {
            'Server': len([tc for tc in TEST_CASES if tc['suite'] == 'Server']),
            'Login': len([tc for tc in TEST_CASES if tc['suite'] == 'Login']),
            'Signup': len([tc for tc in TEST_CASES if tc['suite'] == 'Signup']),
            'Upload': len([tc for tc in TEST_CASES if tc['suite'] == 'Upload']),
            'Full Application': len([tc for tc in TEST_CASES if tc['suite'] == 'Full Application']),
        }
    })

@app.route('/api/run-test', methods=['POST'])
def run_single_test():
    """Run a single test case"""
    data = request.json
    suite_name = data.get('suite')
    test_name = data.get('name')
    method_name = data.get('method')
    
    if test_status['running']:
        return jsonify({'error': 'Tests are already running'}), 400
    
    # Find the test case - match by suite and method name
    test_case = None
    for tc in TEST_CASES:
        if tc['suite'] == suite_name and tc['method'] == method_name:
            test_case = tc
            break
    
    if not test_case:
        # Try to find by matching the class
        test_class_map = {
            'Server': TestServer,
            'Login': TestLogin,
            'Signup': TestSignup,
            'Upload': TestUpload,
            'Full Application': TestFullApplication,
        }
        test_class = test_class_map.get(suite_name)
        if test_class and hasattr(test_class, method_name):
            test_case = {
                'suite': suite_name,
                'name': test_name,
                'method': method_name,
                'class': test_class
            }
    
    if not test_case:
        return jsonify({'error': f'Test case not found: {suite_name}.{method_name}'}), 404
    
    # Run test in background thread
    def run_test():
        test_status['running'] = True
        test_status['current_test'] = test_name
        try:
            test_class = test_case['class']
            test_instance = test_class()
            test_method = getattr(test_instance, method_name)
            result = test_method()
            test_status['results'] = [result]
        except Exception as e:
            test_status['results'] = [{
                'test_name': test_name,
                'status': 'error',
                'message': str(e),
                'duration': 0,
                'timestamp': datetime.now().isoformat()
            }
            ]
        finally:
            test_status['running'] = False
            test_status['current_test'] = None
    
    thread = threading.Thread(target=run_test)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': f'Test {test_name} started', 'status': 'running'})

@app.route('/api/run-suite', methods=['POST'])
def run_suite():
    """Run all tests in a suite"""
    data = request.json
    suite_name = data.get('suite')
    
    if test_status['running']:
        return jsonify({'error': 'Tests are already running'}), 400
    
    # Filter test cases by suite
    suite_tests = [tc for tc in TEST_CASES if tc['suite'] == suite_name]
    
    if not suite_tests:
        return jsonify({'error': 'Suite not found'}), 404
    
    # Run tests in background thread
    def run_suite_tests():
        test_status['running'] = True
        test_status['results'] = []  # Clear previous results for suite
        results = []
        try:
            test_class = suite_tests[0]['class']
            test_instance = test_class()
            results = test_instance.run_all_tests()
            # Store all results from this suite
            test_status['results'] = results if results else []
        except Exception as e:
            test_status['results'] = [{
                'test_name': f'{suite_name} Suite',
                'status': 'error',
                'message': str(e),
                'duration': 0,
                'timestamp': datetime.now().isoformat()
            }]
        finally:
            test_status['running'] = False
            test_status['current_test'] = None
    
    thread = threading.Thread(target=run_suite_tests)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': f'Suite {suite_name} started', 'status': 'running'})

@app.route('/api/run-all', methods=['POST'])
def run_all_tests():
    """Run all test suites"""
    if test_status['running']:
        return jsonify({'error': 'Tests are already running'}), 400
    
    if not TestRunner:
        return jsonify({'error': 'TestRunner not available'}), 500
    
    # Run all tests in background thread
    def run_all():
        test_status['running'] = True
        test_status['results'] = []  # Clear previous results
        try:
            runner = TestRunner()
            summary = runner.run_all_tests()
            runner.save_results()
            # Store ALL results from all test suites
            all_results = summary.get('results', [])
            test_status['results'] = all_results if all_results else []
        except Exception as e:
            test_status['results'] = [{
                'test_name': 'All Tests',
                'status': 'error',
                'message': str(e),
                'duration': 0,
                'timestamp': datetime.now().isoformat()
            }]
        finally:
            test_status['running'] = False
            test_status['current_test'] = None
    
    thread = threading.Thread(target=run_all)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'All tests started', 'status': 'running'})

@app.route('/api/test-status', methods=['GET'])
def get_test_status():
    """Get current test execution status and results"""
    return jsonify({
        'running': test_status['running'],
        'current_test': test_status['current_test'],
        'results': test_status['results'] if test_status['results'] else []
    })


if __name__ == '__main__':
   
    app.run(host='0.0.0.0', port=8000, debug=True)

