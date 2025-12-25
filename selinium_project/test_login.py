"""
Login Functionality Tests
Tests user login with valid/invalid credentials
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from test_base import BaseTest
from test_config import BASE_URL, TEST_USERNAME, TEST_PASSWORD
import time

class TestLogin(BaseTest):
    """Login functionality tests"""
    
    def test_valid_login(self):
        """Test login with valid credentials"""
        try:
            if not self.setup():
                return self.record_test_result("Valid Login", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")
            
            if username_input and password_input:
                username_input.clear()
                username_input.send_keys(TEST_USERNAME)
                password_input.clear()
                password_input.send_keys(TEST_PASSWORD)
                
                login_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if login_btn:
                    login_btn.click()
                    time.sleep(3)
                    
                    # Check if redirected to upload/home page
                    if "/authenticate" in self.driver.current_url or "index" in self.driver.current_url or "upload" in self.driver.current_url.lower():
                        duration = time.time() - start_time
                        return self.record_test_result("Valid Login", "pass", "Login successful, redirected to upload page", duration)
                    else:
                        screenshot = self.take_screenshot("valid_login_failed")
                        duration = time.time() - start_time
                        return self.record_test_result("Valid Login", "fail", f"Login failed, still on {self.driver.current_url}. Screenshot: {screenshot}", duration, screenshot)
                else:
                    screenshot = self.take_screenshot("login_button_not_found")
                    duration = time.time() - start_time
                    return self.record_test_result("Valid Login", "fail", "Login button not found", duration, screenshot)
            else:
                screenshot = self.take_screenshot("login_form_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Valid Login", "fail", "Login form fields not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("valid_login_error")
            return self.record_test_result("Valid Login", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        try:
            
            if not self.setup():
                return self.record_test_result("Invalid Credentials", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")
            
            if username_input and password_input:
                username_input.clear()
                username_input.send_keys("invalid_user")
                password_input.clear()
                password_input.send_keys("wrong_password")
                
                login_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if login_btn:
                    login_btn.click()
                    time.sleep(3)
                    
                    # Should stay on login page or show error
                    if "/login" in self.driver.current_url or "error" in self.driver.page_source.lower() or "invalid" in self.driver.page_source.lower():
                        duration = time.time() - start_time
                        return self.record_test_result("Invalid Credentials", "pass", "Correctly rejected invalid credentials", duration)
                    else:
                        screenshot = self.take_screenshot("invalid_credentials_accepted")
                        duration = time.time() - start_time
                        return self.record_test_result("Invalid Credentials", "fail", "Invalid credentials were accepted", duration, screenshot)
                else:
                    screenshot = self.take_screenshot("login_button_not_found")
                    duration = time.time() - start_time
                    return self.record_test_result("Invalid Credentials", "fail", "Login button not found", duration, screenshot)
            else:
                screenshot = self.take_screenshot("login_form_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Invalid Credentials", "fail", "Login form fields not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("invalid_credentials_error")
            return self.record_test_result("Invalid Credentials", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def test_empty_credentials(self):
        """Test login with empty fields"""
        try:
            if not self.setup():
                return self.record_test_result("Empty Credentials", "error", "Browser setup failed", 0)
            
            start_time = time.time()
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)
            
            login_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
            if login_btn:
                login_btn.click()
                time.sleep(2)
                
                # Should show validation error or stay on page
                if "/login" in self.driver.current_url or "required" in self.driver.page_source.lower() or "empty" in self.driver.page_source.lower():
                    duration = time.time() - start_time
                    return self.record_test_result("Empty Credentials", "pass", "Correctly validated empty fields", duration)
                else:
                    screenshot = self.take_screenshot("empty_credentials_accepted")
                    duration = time.time() - start_time
                    return self.record_test_result("Empty Credentials", "fail", "Empty credentials were accepted", duration, screenshot)
            else:
                screenshot = self.take_screenshot("login_button_not_found")
                duration = time.time() - start_time
                return self.record_test_result("Empty Credentials", "fail", "Login button not found", duration, screenshot)
                
        except Exception as e:
            screenshot = self.take_screenshot("empty_credentials_error")
            return self.record_test_result("Empty Credentials", "error", str(e), time.time() - start_time if 'start_time' in locals() else 0, screenshot)
        finally:
            self.teardown()
    
    def run_all_tests(self):
        """Run all login tests"""
        results = []
        results.append(self.test_valid_login())
        results.append(self.test_invalid_credentials())
        results.append(self.test_empty_credentials())
        return results

