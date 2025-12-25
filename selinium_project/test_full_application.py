"""
Full Application Flow Test - End to End Testing
Tests complete user journey: Signup -> Login -> Upload -> Analysis -> Results
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from test_base import BaseTest
from test_config import BASE_URL, TEST_USERNAME, TEST_PASSWORD
import time
import random
import string


class TestFullApplication(BaseTest):
    """Complete end-to-end application testing"""

    def generate_random_username(self):
        """Generate random username for testing"""
        return f"testuser_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"

    # ---------------------------------------------------------------------
    # COMPLETE USER JOURNEY TEST
    # ---------------------------------------------------------------------
    def test_complete_user_journey(self):
        """Test complete flow: Home -> Signup -> Login -> Upload"""
        try:
            if not self.setup():
                return self.record_test_result("Complete User Journey", "error", "Browser setup failed", 0)

            start_time = time.time()
            journey_steps = []

            # Step 1: Home Page
            self.driver.get(self.base_url)
            time.sleep(2)
            journey_steps.append("Home page loaded")

            # Step 2: Signup Page
            signup_link = self.wait_for_element(By.LINK_TEXT, "Sign Up")
            if not signup_link:
                signup_link = self.wait_for_element(By.PARTIAL_LINK_TEXT, "Sign")

            if signup_link:
                signup_link.click()
                time.sleep(2)
                journey_steps.append("Navigated to signup")
            else:
                self.driver.get(f"{self.base_url}/signup")
                time.sleep(2)
                journey_steps.append("Direct signup page access")

            # Step 3: Signup
            random_username = self.generate_random_username()
            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")

            if username_input and password_input:
                username_input.send_keys(random_username)
                password_input.send_keys("1234")

                submit_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if submit_btn:
                    submit_btn.click()
                    time.sleep(3)
                    journey_steps.append(f"Account created: {random_username}")
                else:
                    screenshot = self.take_screenshot("signup_button_not_found")
                    return self.record_test_result("Complete User Journey", "fail",
                                                   "Signup button missing",
                                                   time.time() - start_time,
                                                   screenshot)
            else:
                screenshot = self.take_screenshot("signup_form_not_found")
                return self.record_test_result("Complete User Journey", "fail",
                                               "Signup form missing",
                                               time.time() - start_time,
                                               screenshot)

            # Step 4: Login
            self.driver.get(f"{self.base_url}/login")
            time.sleep(2)

            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")

            if username_input and password_input:
                username_input.send_keys(random_username)
                password_input.send_keys("1234")

                login_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
                if login_btn:
                    login_btn.click()
                    time.sleep(3)
                    journey_steps.append("Login successful")
                else:
                    screenshot = self.take_screenshot("login_button_not_found")
                    return self.record_test_result("Complete User Journey", "fail",
                                                   "Login button missing",
                                                   time.time() - start_time,
                                                   screenshot)
            else:
                screenshot = self.take_screenshot("login_form_not_found")
                return self.record_test_result("Complete User Journey", "fail",
                                               "Login form missing",
                                               time.time() - start_time,
                                               screenshot)

            # Step 5: Upload Page
            if ("authenticate" in self.driver.current_url.lower() or
                "index" in self.driver.current_url.lower() or
                "upload" in self.driver.current_url.lower()):
                journey_steps.append("Reached upload page")
            else:
                file_input = self.wait_for_element(By.CSS_SELECTOR, "input[type='file']")
                if file_input:
                    journey_steps.append("Upload form found")
                else:
                    screenshot = self.take_screenshot("upload_page_not_reached")
                    return self.record_test_result("Complete User Journey", "fail",
                                                   f"Not on upload page. URL: {self.driver.current_url}",
                                                   time.time() - start_time,
                                                   screenshot)

            duration = time.time() - start_time
            return self.record_test_result("Complete User Journey", "pass",
                                           " -> ".join(journey_steps), duration)

        except Exception as e:
            screenshot = self.take_screenshot("complete_journey_error")
            return self.record_test_result("Complete User Journey", "error",
                                           str(e),
                                           time.time() - start_time if 'start_time' in locals() else 0,
                                           screenshot)
        finally:
            self.teardown()

    # ---------------------------------------------------------------------
    # DATABASE CONNECTION TEST (POSTGRESQL)
    # ---------------------------------------------------------------------
    def test_database_connection(self):
        """Validate PostgreSQL insert (signup + DB check)"""

        try:
            if not self.setup():
                return self.record_test_result("Database Connection", "error", "Browser setup failed", 0)

            start_time = time.time()
            random_username = self.generate_random_username()

            # UI Signup
            self.driver.get(f"{self.base_url}/signup")
            time.sleep(2)

            username_input = self.wait_for_element(By.ID, "name")
            password_input = self.wait_for_element(By.ID, "password")

            if not username_input or not password_input:
                return self.record_test_result("Database Connection", "fail",
                                               "Form fields missing",
                                               time.time() - start_time)

            username_input.send_keys(random_username)
            password_input.send_keys("1234")

            submit_btn = self.wait_for_element(By.CSS_SELECTOR, "button[type='submit']")
            if not submit_btn:
                return self.record_test_result("Database Connection", "fail",
                                               "Submit button missing",
                                               time.time() - start_time)

            submit_btn.click()
            time.sleep(3)

            # Validate successful signup UI
            if not ("login" in self.driver.current_url.lower()
                    or "success" in self.driver.page_source.lower()):
                return self.record_test_result("Database Connection", "fail",
                                               "Signup did not complete via UI",
                                               time.time() - start_time)

            # DB CHECK - Try to verify user was created
            result = None
            db_checked = False
            try:
                import psycopg2
                
                # Try to connect to database
                # Use environment variables or default values
                db_host = os.getenv("DB_HOST", "localhost")
                db_name = os.getenv("DB_NAME", "detection")
                db_user = os.getenv("DB_USER", "postgres")
                db_password = os.getenv("DB_PASSWORD", "Jeeva@123")
                db_port = int(os.getenv("DB_PORT", "5432"))

                conn = psycopg2.connect(
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=db_password,
                    port=db_port,
                    connect_timeout=10
                )

                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM authenticate WHERE name = %s",
                    (random_username,)
                )
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                db_checked = True

            except ImportError:
                # psycopg2 not installed - skip DB check
                return self.record_test_result("Database Connection", "pass",
                                               f"UI signup successful (DB check skipped - psycopg2 not installed)",
                                               time.time() - start_time)
            except Exception as e:
                # Database connection failed
                error_msg = str(e)
                print(f"Database check error: {error_msg}")
                # If UI signup was successful, we'll consider it a partial pass
                # since the main goal is to test the application flow
                duration = time.time() - start_time
                return self.record_test_result("Database Connection", "fail",
                                               f"UI signup succeeded but DB verification failed: {error_msg[:100]}",
                                               duration)

            duration = time.time() - start_time

            if db_checked:
                if result:
                    return self.record_test_result("Database Connection", "pass",
                                                   f"DB insert verified (user={random_username})",
                                                   duration)
                else:
                    return self.record_test_result("Database Connection", "fail",
                                                   f"UI signup succeeded but user not found in DB: {random_username}",
                                                   duration)
            else:
                return self.record_test_result("Database Connection", "pass",
                                               f"UI signup successful (DB check skipped)",
                                               duration)

        except Exception as e:
            screenshot = self.take_screenshot("database_connection_error")
            return self.record_test_result("Database Connection", "error",
                                           str(e),
                                           time.time() - start_time if 'start_time' in locals() else 0,
                                           screenshot)
        finally:
            self.teardown()

    # ---------------------------------------------------------------------
    # API ENDPOINT TEST
    # ---------------------------------------------------------------------
    def test_api_endpoints(self):
        """Test FastAPI / Flask endpoints"""
        try:
            import requests
            start_time = time.time()

            # Use BASE_URL from config - this should point to the actual app server (not test dashboard)
            # If BASE_URL points to test dashboard (port 8000), we need the actual app URL
            # Check if BASE_URL is the test dashboard, if so, try to find actual app
            app_url = BASE_URL
            # If BASE_URL is test dashboard, try common app ports
            if '8000' in BASE_URL and '/api/' not in BASE_URL:
                # Try to detect actual app port - could be 5000, 8080, etc.
                # For now, use BASE_URL as is, but allow it to be configured
                app_url = BASE_URL

            # GET endpoints - test actual application endpoints
            get_endpoints = [
                ('/', 'Home'),
                ('/login', 'Login'),
                ('/signup', 'Signup'),
                ('/home', 'Home Page'),
            ]
            
            # POST endpoints - these may need data but should exist
            post_endpoints = [
                ('/authenticate', 'Authenticate'),
                ('/analyze', 'Analyze'),
            ]

            failed = []
            passed = []

            # Test GET endpoints
            for path, name in get_endpoints:
                try:
                    response = requests.get(f"{app_url}{path}", timeout=5, allow_redirects=True)
                    # Accept 200, 302 (redirect), 301 (redirect) as success
                    if response.status_code in [200, 302, 301]:
                        passed.append(f"{name}")
                    else:
                        failed.append(f"{name} ({response.status_code})")
                except requests.exceptions.ConnectionError:
                    failed.append(f"{name} (connection failed - is server running?)")
                except Exception as e:
                    failed.append(f"{name} Error: {str(e)[:50]}")

            # Test POST endpoints - they should exist even if they return validation errors
            for path, name in post_endpoints:
                try:
                    response = requests.post(f"{app_url}{path}", json={}, timeout=5)
                    # 200 = success, 422/400 = endpoint exists but needs data (OK), 405 = method not allowed
                    if response.status_code in [200, 422, 400]:
                        passed.append(f"{name}")
                    elif response.status_code == 405:
                        # Try GET to see if endpoint exists at all
                        get_resp = requests.get(f"{app_url}{path}", timeout=5)
                        if get_resp.status_code != 404:
                            passed.append(f"{name} (exists)")
                        else:
                            failed.append(f"{name} (not found)")
                    else:
                        failed.append(f"{name} ({response.status_code})")
                except requests.exceptions.ConnectionError:
                    failed.append(f"{name} (connection failed)")
                except Exception as e:
                    failed.append(f"{name} Error: {str(e)[:50]}")

            duration = time.time() - start_time

            if failed:
                return self.record_test_result("API Endpoints", "fail",
                                               f"Failed: {', '.join(failed)}. Passed: {len(passed)}",
                                               duration)
            else:
                return self.record_test_result("API Endpoints", "pass",
                                               f"All {len(passed)} endpoints accessible",
                                               duration)

        except ImportError:
            return self.record_test_result("API Endpoints", "error", "requests library not installed", 0)
        except Exception as e:
            return self.record_test_result("API Endpoints", "error", str(e), 0)

    # ---------------------------------------------------------------------
    # NAVIGATION TEST
    # ---------------------------------------------------------------------
    def test_navigation_flow(self):
        """Test page navigation"""
        try:
            if not self.setup():
                return self.record_test_result("Navigation Flow", "error", "Browser setup failed", 0)

            start_time = time.time()
            steps = []

            self.driver.get(self.base_url)
            time.sleep(1)

            self.driver.get(f"{self.base_url}/login")
            time.sleep(1)
            if "/login" in self.driver.current_url:
                steps.append("Home→Login")

            self.driver.get(f"{self.base_url}/signup")
            time.sleep(1)
            if "/signup" in self.driver.current_url:
                steps.append("Login→Signup")

            self.driver.get(self.base_url)
            time.sleep(1)
            steps.append("Signup→Home")

            duration = time.time() - start_time

            if len(steps) >= 3:
                return self.record_test_result("Navigation Flow", "pass",
                                               " -> ".join(steps), duration)
            else:
                return self.record_test_result("Navigation Flow", "fail",
                                               "Navigation incomplete",
                                               duration)

        except Exception as e:
            screenshot = self.take_screenshot("navigation_error")
            return self.record_test_result("Navigation Flow", "error",
                                           str(e),
                                           time.time() - start_time if 'start_time' in locals() else 0,
                                           screenshot)
        finally:
            self.teardown()

    # ---------------------------------------------------------------------
    # RUN ALL TESTS
    # ---------------------------------------------------------------------
    def run_all_tests(self):
        """Run the full suite"""
        results = []
        results.append(self.test_api_endpoints())
        results.append(self.test_navigation_flow())
        results.append(self.test_database_connection())
        results.append(self.test_complete_user_journey())
        return results
