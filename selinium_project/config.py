"""
Configuration for Test Dashboard
Set environment variables to customize
"""
import os

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))

# Test Configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:8000')
TEST_TIMEOUT = int(os.getenv('TEST_TIMEOUT', 30))

# Display Configuration
AUTO_RELOAD = os.getenv('AUTO_RELOAD', 'true').lower() == 'true'
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'

print(f"Configuration:")
print(f"  Host: {HOST}")
print(f"  Port: {PORT}")
print(f"  Base URL: {BASE_URL}")
print(f"  Auto Reload: {AUTO_RELOAD}")
print(f"  Debug: {DEBUG}")

