"""Authentication service - handles magic links and password resets."""
from flask import current_app, request
from app import db
from app.models import AuthToken, Person


class AuthService:
    """Service for managing authentication tokens."""

    @staticmethod
    def check_rate_limit(person_id, token_type):
        """Check if rate limit has been exceeded for token requests.

        Args:
            person_id: Person ID
            token_type: Type of token ('magic_link' or 'password_reset')

        Returns:
            Boolean indicating if rate limit is exceeded
        """
        from datetime import datetime, timedelta

        rate_limit = current_app.config.get("AUTH_TOKEN_RATE_LIMIT", 5)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Count tokens created in the last hour
        recent_tokens = AuthToken.query.filter(
            AuthToken.person_id == person_id,
            AuthToken.token_type == token_type,
            AuthToken.created_at >= one_hour_ago
        ).count()

        return recent_tokens >= rate_limit

    @staticmethod
    def create_magic_link_token(person):
        """Create a magic link token for a person.

        Args:
            person: Person object

        Returns:
            AuthToken object or None if rate limited
        """
        # Check rate limit
        if AuthService.check_rate_limit(person.id, "magic_link"):
            current_app.logger.warning(
                f"Rate limit exceeded for magic link request: person_id={person.id}"
            )
            return None

        expiration_minutes = current_app.config.get("MAGIC_LINK_EXPIRATION_MINUTES", 30)
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get("User-Agent") if request else None

        # Invalidate any existing unused magic link tokens for this person
        AuthService._invalidate_existing_tokens(person.id, "magic_link")

        token = AuthToken.create_magic_link_token(
            person=person,
            expiration_minutes=expiration_minutes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return token

    @staticmethod
    def create_password_reset_token(person):
        """Create a password reset token for a person.

        Args:
            person: Person object

        Returns:
            AuthToken object or None if rate limited
        """
        # Check rate limit
        if AuthService.check_rate_limit(person.id, "password_reset"):
            current_app.logger.warning(
                f"Rate limit exceeded for password reset request: person_id={person.id}"
            )
            return None

        expiration_minutes = current_app.config.get("PASSWORD_RESET_EXPIRATION_MINUTES", 60)
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get("User-Agent") if request else None

        # Invalidate any existing unused password reset tokens for this person
        AuthService._invalidate_existing_tokens(person.id, "password_reset")

        token = AuthToken.create_password_reset_token(
            person=person,
            expiration_minutes=expiration_minutes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return token

    @staticmethod
    def verify_magic_link_token(token_string):
        """Verify a magic link token.

        Args:
            token_string: The token string to verify

        Returns:
            Person object if valid, None otherwise
        """
        token = AuthToken.verify_token(token_string, "magic_link")

        if not token:
            return None

        # Mark token as used
        token.mark_as_used()

        return token.person

    @staticmethod
    def verify_password_reset_token(token_string):
        """Verify a password reset token.

        Args:
            token_string: The token string to verify

        Returns:
            AuthToken object if valid, None otherwise
        """
        token = AuthToken.verify_token(token_string, "password_reset")
        return token

    @staticmethod
    def use_password_reset_token(token):
        """Mark a password reset token as used.

        Args:
            token: AuthToken object

        Returns:
            None
        """
        if token and token.is_valid:
            token.mark_as_used()

    @staticmethod
    def _invalidate_existing_tokens(person_id, token_type):
        """Invalidate all existing unused tokens of a specific type for a person.

        Args:
            person_id: Person ID
            token_type: Type of token ('magic_link' or 'password_reset')

        Returns:
            Number of tokens invalidated
        """
        from datetime import datetime

        tokens = AuthToken.query.filter_by(
            person_id=person_id, token_type=token_type, used_at=None
        ).all()

        count = 0
        for token in tokens:
            token.used_at = datetime.utcnow()
            count += 1

        if count > 0:
            db.session.commit()

        return count

    @staticmethod
    def cleanup_expired_tokens():
        """Delete expired tokens from the database.

        Returns:
            Number of tokens deleted
        """
        return AuthToken.cleanup_expired_tokens()

    @staticmethod
    def get_person_by_email(email):
        """Get a person by email address.

        Args:
            email: Email address

        Returns:
            Person object if found, None otherwise
        """
        return Person.query.filter_by(email=email).first()

