"""
RENAME THIS FILE TO config.py, ADD YOUR CONFIGURATION SETTINGS
This module contains configuration settings for the Money Manager application.
"""

import os

MONGO_URI = os.getenv("MONGO_URI", None)

TOKEN_SECRET_KEY = os.getenv("TOKEN_SECRET_KEY", None)
TOKEN_ALGORITHM = os.getenv("TOKEN_ALGORITHM", None)

API_BIND_HOST = os.getenv("API_BIND_HOST", "0.0.0.0")
API_BIND_PORT = os.getenv("API_BIND_PORT", "9999")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", None)
TELEGRAM_BOT_API_BASE_URL = os.getenv(
    "TELEGRAM_BOT_API_BASE_URL", "http://localhost:9999"
)
