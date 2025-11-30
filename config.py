"""Application configuration."""
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""

    # Flask Core
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    FLASK_APP = os.environ.get("FLASK_APP", "run.py")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///holiday_party.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Application Settings
    APP_NAME = os.environ.get("APP_NAME", "Family Holiday Party Planner")
    # APP_URL can be set via environment variable for network access
    # For local network access, set to: http://<your-local-ip>:5000
    # For localhost only, use: http://localhost:5000
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
    SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL", "support@example.com")

    # Security & Tokens
    TOKEN_EXPIRATION_DAYS = int(os.environ.get("TOKEN_EXPIRATION_DAYS", 90))
    MAGIC_LINK_EXPIRATION_MINUTES = int(
        os.environ.get("MAGIC_LINK_EXPIRATION_MINUTES", 30)
    )
    PASSWORD_RESET_EXPIRATION_MINUTES = int(
        os.environ.get("PASSWORD_RESET_EXPIRATION_MINUTES", 60)
    )
    # Rate limiting for auth tokens (max requests per hour per IP)
    AUTH_TOKEN_RATE_LIMIT = int(os.environ.get("AUTH_TOKEN_RATE_LIMIT", 5))
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire

    # Brevo (Sendinblue) Configuration
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Holiday Party Planner")

    # Brevo SMS Configuration
    # SMS sender name (alphanumeric, max 11 chars for most countries)
    # Note: Some countries require pre-registered sender IDs
    BREVO_SMS_SENDER_NAME = os.environ.get("BREVO_SMS_SENDER_NAME", "HolidayParty")

    # Flask-Mail Configuration (fallback/testing)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "BREVO_SENDER_EMAIL", "noreply@example.com"
    )

    # Background Jobs
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "True").lower() == "true"
    REMINDER_CHECK_HOUR = int(os.environ.get("REMINDER_CHECK_HOUR", 9))

    # Feature Flags
    ENABLE_SMS = os.environ.get("ENABLE_SMS", "False").lower() == "true"
    ENABLE_MESSAGE_WALL = (
        os.environ.get("ENABLE_MESSAGE_WALL", "True").lower() == "true"
    )
    ENABLE_POTLUCK = os.environ.get("ENABLE_POTLUCK", "True").lower() == "true"

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/app.log")

    # Pagination
    ITEMS_PER_PAGE = 50

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Note: Flask-Session has compatibility issues with Werkzeug 3.0+
    # Using default Flask sessions (cookie-based) with permanent flag
    # Sessions will persist as long as the browser is open and SECRET_KEY doesn't change


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    SQLALCHEMY_ECHO = True
    TESTING = False

    # More relaxed session settings for development
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SCHEDULER_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    # Production session settings
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Ensure critical settings are set in production
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific settings."""
        Config.init_app(app)

        # Assert critical environment variables are set
        assert os.environ.get("SECRET_KEY"), "SECRET_KEY must be set in production"
        assert os.environ.get("BREVO_API_KEY"), "BREVO_API_KEY must be set"
        assert os.environ.get(
            "DATABASE_URL"
        ), "DATABASE_URL must be set in production"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

