"""Authentication token model for magic links and password resets."""
from datetime import datetime, timedelta
import secrets
from app import db


class AuthToken(db.Model):
    """Represents an authentication token for magic links or password resets."""

    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_type = db.Column(
        db.String(20), nullable=False
    )  # 'magic_link' or 'password_reset'
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 max length
    user_agent = db.Column(db.String(255), nullable=True)

    # Relationships
    person = db.relationship("Person", backref="auth_tokens")

    # Constraints
    __table_args__ = (
        db.Index("idx_token_lookup", "token", "token_type"),
        db.Index("idx_person_tokens", "person_id", "token_type", "expires_at"),
    )

    def __repr__(self):
        return f"<AuthToken {self.token_type} person_id={self.person_id}>"

    @staticmethod
    def generate_token():
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)

    @classmethod
    def create_magic_link_token(cls, person, expiration_minutes=30, ip_address=None, user_agent=None):
        """Create a magic link token for a person.

        Args:
            person: Person object
            expiration_minutes: Token expiration time in minutes
            ip_address: IP address of requester (optional)
            user_agent: User agent of requester (optional)

        Returns:
            AuthToken object
        """
        token = cls(
            person_id=person.id,
            token=cls.generate_token(),
            token_type="magic_link",
            expires_at=datetime.utcnow() + timedelta(minutes=expiration_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(token)
        db.session.commit()
        return token

    @classmethod
    def create_password_reset_token(cls, person, expiration_minutes=60, ip_address=None, user_agent=None):
        """Create a password reset token for a person.

        Args:
            person: Person object
            expiration_minutes: Token expiration time in minutes
            ip_address: IP address of requester (optional)
            user_agent: User agent of requester (optional)

        Returns:
            AuthToken object
        """
        token = cls(
            person_id=person.id,
            token=cls.generate_token(),
            token_type="password_reset",
            expires_at=datetime.utcnow() + timedelta(minutes=expiration_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(token)
        db.session.commit()
        return token

    @property
    def is_expired(self):
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self):
        """Check if token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self):
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and not self.is_used

    def mark_as_used(self):
        """Mark token as used."""
        self.used_at = datetime.utcnow()
        db.session.commit()

    @classmethod
    def verify_token(cls, token_string, token_type):
        """Verify and retrieve a token.

        Args:
            token_string: The token string to verify
            token_type: Type of token ('magic_link' or 'password_reset')

        Returns:
            AuthToken object if valid, None otherwise
        """
        token = cls.query.filter_by(token=token_string, token_type=token_type).first()

        if not token:
            return None

        if not token.is_valid:
            return None

        return token

    @classmethod
    def cleanup_expired_tokens(cls):
        """Delete expired tokens from the database.

        Returns:
            Number of tokens deleted
        """
        expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        count = len(expired_tokens)

        for token in expired_tokens:
            db.session.delete(token)

        db.session.commit()
        return count

    def to_dict(self):
        """Convert token to dictionary."""
        return {
            "id": self.id,
            "person_id": self.person_id,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_valid": self.is_valid,
        }

