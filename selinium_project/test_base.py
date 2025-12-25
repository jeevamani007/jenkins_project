"""
Base test class for Selenium tests
"""
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import test config with fallback for different execution contexts
try:
    from test_config import BASE_URL, BROWSER, IMPLICIT_WAIT, EXPLICIT_WAIT, SCREENSHOT_ON_FAILURE, SCREENSHOT_DIR
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_config import BASE_URL, BROWSER, IMPLICIT_WAIT, EXPLICIT_WAIT, SCREENSHOT_ON_FAILURE, SCREENSHOT_DIR

class BaseTest:
    """Base class for all test cases"""
    
    def __init__(self):
        self.driver = None
        self.base_url = BASE_URL
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
    def setup(self):
        """Setup test environment"""
        try:
            chrome_options = Options()
            #chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Set page load timeout
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)  # 30 second page load timeout
            self.driver.implicitly_wait(IMPLICIT_WAIT)
            self.driver.maximize_window()
            self.start_time = datetime.now()
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False
    
    def teardown(self):
        """Cleanup after test"""
        if self.driver:
            self.driver.quit()
        self.end_time = datetime.now()
    
    def wait_for_element(self, by, value, timeout=EXPLICIT_WAIT):
        """Wait for element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(

                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def wait_for_clickable(self, by, value, timeout=EXPLICIT_WAIT):
        """Wait for element to be clickable"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def take_screenshot(self, name):
        """Take screenshot"""
        if SCREENSHOT_ON_FAILURE:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = f"{SCREENSHOT_DIR}/{filename}"
            self.driver.save_screenshot(filepath)
            return filename  # Return just filename, not full path
        return None
    
    def record_test_result(self, test_name, status, message="", duration=0, screenshot_path=None):
        """Record test result"""
        result = {
            "test_name": test_name,
            "status": status,  # "pass", "fail", "error"
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path if screenshot_path else None
        }
        self.test_results.append(result)
        return result

