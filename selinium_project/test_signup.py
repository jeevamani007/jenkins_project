"""
Signup Functionality Tests
Tests user registration and form validation
"""
import sys
import os
import random
import string
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from test_base import BaseTest
from test_config import BASE_URL
import time

class TestSignup(BaseTest):
    """Signup functionality tests"""
    
    def generate_random_username(self):
        """Generate random username for testing"""
        return f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
    
    def test_valid_signup(self):
        """Test signup with valid credentials"""
        try:
            if not self.setup():
                return self.record_test_result("Valid Signup", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            random_username = self.generate_random_username()
            self.driver.get(f"{self.base_url}/signup")
            time.sleep(2)
            
            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")
            
            if username_input and password_input:
                username_input.clear()
                username_input.send_keys(random_username)
                password_input.clear()
                password_input.send_keys("1234")
                
                submit_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if submit_btn:
                    submit_btn.click()
                    time.sleep(3)
                    
                    # Check if redirected to login or success page
                    if "/login" in self.driver.current_url or "success" in self.driver.page_source.lower():
                        duration = time.time() - start_time
                        return self.record_test_result("Valid Signup", "pass", f"Signup successful for {random_username}", duration)
                    else:
                        screenshot = self.take_screenshot("valid_signup_failed")
                        duration = time.time() - start_time
                        return self.record_test_result("Valid Signup", "fail", f"Signup failed, still on {self.driver.current_url}", duration, screenshot)
                else:
                    screenshot = self.take_screenshot("signup_button_not_found")
                    duration = time.time() - start_time
                    return self.record_test_result("Valid Signup", "fail", "Signup button not found", duration, screenshot)
            else:
                screenshot = self.take_screenshot("signup_form_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Valid Signup", "fail", "Signup form fields not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("valid_signup_error")
            return self.record_test_result("Valid Signup", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def test_duplicate_username(self):
        """Test signup with existing username"""
        try:
            if not self.setup():
                return self.record_test_result("Duplicate Username", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            # Use a known username (might already exist)
            self.driver.get(f"{self.base_url}/signup")
            time.sleep(2)
            
            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")
            
            if username_input and password_input:
                username_input.clear()
                username_input.send_keys("testuser")
                password_input.clear()
                password_input.send_keys("1234")
                
                submit_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if submit_btn:
                    submit_btn.click()
                    time.sleep(3)
                    
                    # Should show error or stay on signup page
                    if "/signup" in self.driver.current_url or "exists" in self.driver.page_source.lower() or "already" in self.driver.page_source.lower():
                        duration = time.time() - start_time
                        return self.record_test_result("Duplicate Username", "pass", "Correctly rejected duplicate username", duration)
                    else:
                        screenshot = self.take_screenshot("duplicate_username_accepted")
                        duration = time.time() - start_time
                        return self.record_test_result("Duplicate Username", "fail", "Duplicate username was accepted", duration, screenshot)
                else:
                    screenshot = self.take_screenshot("signup_button_not_found")
                    duration = time.time() - start_time
                    return self.record_test_result("Duplicate Username", "fail", "Signup button not found", duration, screenshot)
            else:
                screenshot = self.take_screenshot("signup_form_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Duplicate Username", "fail", "Signup form fields not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("duplicate_username_error")
            return self.record_test_result("Duplicate Username", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def test_empty_fields(self):
        """Test signup with empty fields"""
        try:
            if not self.setup():
                return self.record_test_result("Empty Signup Fields", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            self.driver.get(f"{self.base_url}/signup")
            time.sleep(2)
            
            submit_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
            if submit_btn:
                submit_btn.click()
                time.sleep(2)
                
                # Should show validation error
                if "/signup" in self.driver.current_url or "required" in self.driver.page_source.lower():
                    duration = time.time() - start_time
                    return self.record_test_result("Empty Signup Fields", "pass", "Correctly validated empty fields", duration)
                else:
                    screenshot = self.take_screenshot("empty_fields_accepted")
                    duration = time.time() - start_time
                    return self.record_test_result("Empty Signup Fields", "fail", "Empty fields were accepted", duration, screenshot)
            else:
                screenshot = self.take_screenshot("signup_button_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Empty Signup Fields", "fail", "Signup button not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("empty_fields_error")
            return self.record_test_result("Empty Signup Fields", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def run_all_tests(self):
        """Run all signup tests"""
        results = []
        results.append(self.test_valid_signup())
        results.append(self.test_duplicate_username())
        results.append(self.test_empty_fields())
        return results

