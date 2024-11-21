"""
RENAME THIS FILE TO config.py, ADD YOUR CONFIGURATION SETTINGS
This module contains configuration settings for the Money Manager application.
"""

import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

TOKEN_SECRET_KEY = os.getenv("TOKEN_SECRET_KEY", "")
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", "HS256")

API_BIND_HOST = os.getenv("API_BIND_HOST", "0.0.0.0")
API_BIND_PORT = int(os.getenv("API_BIND_PORT", "9999"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_API_BASE_URL = os.getenv(
    "TELEGRAM_BOT_API_BASE_URL", "http://localhost:9999"
)

TIME_ZONE = os.getenv("TIME_ZONE", "America/New_York")
