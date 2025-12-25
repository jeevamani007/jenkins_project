"""
Server Loading Tests
Tests if server and pages are accessible
"""
import sys
import os
from typing import Final
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from test_base import BaseTest
from test_config import BASE_URL
import time

class TestServer(BaseTest):
    """Server loading tests"""
    
    def test_server_running(self):
        """Test if server is running"""
        try:
            start_time = time.time()
            response = requests.get(BASE_URL, timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return self.record_test_result("Server Running", "pass", f"Server is running (Status: {response.status_code})", duration)
            else:
                return self.record_test_result("Server Running", "fail", f"Server returned status {response.status_code}", duration)
        except requests.exceptions.ConnectionError:
            return self.record_test_result("Server Running", "fail", "Cannot connect to server. Is it running?", 0)
        except Exception as e:
            return self.record_test_result("Server Running", "error", str(e), 0)
    
    def test_home_page_loads(self):
        """Test if home page loads"""
        try:
            start_time = time.time()
            response = requests.get(BASE_URL, timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200 and len(response.text) > 100:
                return self.record_test_result("Home Page Loads", "pass", f"Home page loaded successfully ({len(response.text)} bytes)", duration)
            else:
                return self.record_test_result("Home Page Loads", "fail", f"Home page failed to load properly (Status: {response.status_code})", duration)
        except Exception as e:
            return self.record_test_result("Home Page Loads", "error", str(e), 0)
    
    def test_login_page_loads(self):
        """Test if login page loads"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/login", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200 and "login" in response.text.lower():
                return self.record_test_result("Login Page Loads", "pass", f"Login page loaded successfully", duration)
            else:
                return self.record_test_result("Login Page Loads", "fail", f"Login page failed to load (Status: {response.status_code})", duration)
        except Exception as e:
            return self.record_test_result("Login Page Loads", "error", str(e), 0)
    
    def test_signup_page_loads(self):
        """Test if signup page loads"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/signup", timeout=5)
            duration = time.time() - start_time
            
            if response.status_code == 200 and ("signup" in response.text.lower() or "sign up" in response.text.lower()):
                return self.record_test_result("Signup Page Loads", "pass", f"Signup page loaded successfully", duration)
            else:
                return self.record_test_result("Signup Page Loads", "fail", f"Signup page failed to load (Status: {response.status_code})", duration)
        except Exception as e:
            return self.record_test_result("Signup Page Loads", "error", str(e), 0)
    
 #   def test_dashboard_page_loads(self):
  #      """Test if test dashboard page loads"""
   #     try:
    #        start_time = time.time()
     ##      duration = time.time() - start_time
       ##    if response.status_code == 200:
         #       return self.record_test_result("Test Dashboard Loads", "pass", f"Test dashboard loaded successfully", duration)
          #  else:
           #     return self.record_test_result("Test Dashboard Loads", "fail", f"Test dashboard failed to load (Status: {response.status_code})", duration)
       # except Exception as e:
        #    return self.record_test_result("Test Dashboard Loads", "error", str(e), 0)
    
    def test_page_response_times(self):
        """Test page response times"""
        try:
            start_time = time.time()
            pages = [
                ("/", "Home"),
                ("/login", "Login"),
                ("/signup", "Signup"),
                ("/authenticate","Authenticate"),
                ("/analyze","Analyze"),
                ('/final/',"Final")
            ]
            
            slow_pages = []
            for path, name in pages:
                try:
                    page_start = time.time()
                    response = requests.get(f"{BASE_URL}{path}", timeout=12)
                    page_duration = time.time() - page_start
                    
                    if page_duration > 5.0:  # More than 2 seconds is slow
                        slow_pages.append(f"{name} ({page_duration:.2f}s)")
                except:
                    slow_pages.append(f"{name} (failed)")
            
            duration = time.time() - start_time
            
            if slow_pages:
                return self.record_test_result("Page Response Times", "fail", f"Slow pages: {', '.join(slow_pages)}", duration)
            else:
                return self.record_test_result("Page Response Times", "pass", "All pages loaded within acceptable time", duration)
        except Exception as e:
            return self.record_test_result("Page Response Times", "error", str(e), 0)
    
    def run_all_tests(self):
        """Run all server tests"""
        results = []
        results.append(self.test_server_running())
        results.append(self.test_home_page_loads())
        results.append(self.test_login_page_loads())
        results.append(self.test_signup_page_loads())
        # results.append(self.test_dashboard_page_loads())  # Commented out - method not implemented
        results.append(self.test_page_response_times())
        return results

