"""
Test configuration for Selenium tests
"""
import os

# Base URL for the application
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

# Browser configuration
BROWSER = os.getenv("TEST_BROWSER", "chrome")  # chrome, firefox, edge

# Timeout settings
IMPLICIT_WAIT = 10  # seconds
EXPLICIT_WAIT = 20  # seconds

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "1234"
TEST_PROJECT_NAME = "Test Project"

# Screenshot settings
SCREENSHOT_ON_FAILURE = True
SCREENSHOT_DIR = "tests/screenshots"
