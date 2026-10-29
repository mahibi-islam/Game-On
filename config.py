import os
from datetime import timedelta

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use default values

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/turf_booking'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'static/uploads'
    
    # Google Sheets for bookings export/sync
    GOOGLE_SHEETS_URL = os.environ.get('GOOGLE_SHEETS_URL')
    GOOGLE_SHEETS_CREDENTIALS_FILE = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE') or os.environ.get('GOOGLE_CREDENTIALS_FILE') or 'credentials.json'
    GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON') or os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    GOOGLE_TOKEN_FILE = os.environ.get('GOOGLE_TOKEN_FILE') or 'token.json'
    GOOGLE_TOKEN_JSON = os.environ.get('GOOGLE_TOKEN_JSON')
    
    # Cloudinary media storage (optional)
    CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
    
    # Fallback to local Excel if Google Sheets not configured
    EXCEL_FILE = os.environ.get('EXCEL_FILE') or 'bookings.xlsx'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CSRF tokens stay valid for the whole session instead of expiring after an hour
    WTF_CSRF_TIME_LIMIT = None

    # Rate limiting (Flask-Limiter)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI') or 'memory://'
    RATELIMIT_HEADERS_ENABLED = True

    # Number of reverse proxies in front of the app (the hosting platform's router).
    # Used to read the real client IP from X-Forwarded-For for rate limiting.
    PROXY_COUNT = int(os.environ.get('PROXY_COUNT', 1))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')

    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("No SECRET_KEY set for production configuration")
        if not self.MONGO_URI:
            raise ValueError("No MONGO_URI set for production configuration")

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MONGO_URI = os.environ.get('MONGO_TEST_URI') or 'mongodb://localhost:27017/turf_booking_test'

