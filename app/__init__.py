"""Flask application factory."""
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import config

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
# Note: Flask-Session disabled due to compatibility issues with Werkzeug 3.0+
# Using default Flask sessions (cookie-based) instead


def create_app(config_name="default"):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration name (development, testing, production)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.routes import organizer, public, api, guests

    app.register_blueprint(organizer.bp)
    app.register_blueprint(public.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(guests.bp)

    # Register error handlers
    register_error_handlers(app)

    # Configure logging
    configure_logging(app)

    # Initialize background scheduler
    if app.config["SCHEDULER_ENABLED"] and not app.config["TESTING"]:
        from app.scheduler import init_scheduler

        init_scheduler(app)

    # Register template filters and context processors
    register_template_helpers(app)

    return app


def register_error_handlers(app):
    """Register error handlers for common HTTP errors."""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template

        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template

        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template

        return render_template("errors/403.html"), 403


def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # File handler
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"], maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(getattr(logging, app.config["LOG_LEVEL"]))
        app.logger.addHandler(file_handler)

        app.logger.setLevel(getattr(logging, app.config["LOG_LEVEL"]))
        app.logger.info("Holiday Party Planner startup")


def register_template_helpers(app):
    """Register custom template filters and context processors."""

    @app.template_filter("datetime")
    def format_datetime(value, format="%B %d, %Y at %I:%M %p"):
        """Format a datetime object for display."""
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter("date")
    def format_date(value, format="%B %d, %Y"):
        """Format a date object for display."""
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter("phone")
    def format_phone(value):
        """Format a phone number for display.

        Converts E.164 format (+12025551234) to user-friendly format ((202) 555-1234).
        """
        if not value:
            return ""
        from app.utils.phone_utils import format_phone_display
        return format_phone_display(value)

    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates."""
        from flask import session, g
        from app.models import Person

        context = {
            "app_name": app.config["APP_NAME"],
            "support_email": app.config["SUPPORT_EMAIL"],
        }

        # Add current user and dev user switcher data (development only)
        # Check if we're in development mode (not production or testing)
        is_dev = not app.config.get("TESTING") and app.config.get("ENV") != "production"

        if is_dev:
            context["is_dev_mode"] = True

            # Get current user if logged in
            person_id = session.get("person_id")
            if person_id:
                current_person = getattr(g, "current_person", None) or Person.query.get(person_id)
                context["current_person"] = current_person

                # Get all users with passwords (organizers) for the switcher
                available_users = Person.query.filter(
                    Person.password_hash.isnot(None)
                ).order_by(Person.first_name, Person.last_name).all()
                context["available_users"] = available_users
        else:
            context["is_dev_mode"] = False

        return context

