"""GuestReferral model for tracking 'bring a friend' relationships."""
import secrets
from datetime import datetime
from app import db


class GuestReferral(db.Model):
    """Tracks when an invited guest brings a friend to an event.
    
    This model captures the relationship between:
    - The referring guest (who was originally invited to the event)
    - The referred friend (who was invited by the referring guest)
    - The event they're both attending
    
    Friends brought by guests are distinguished from regular household invitations:
    - They don't require household association
    - They are invited by other guests, not by event organizers
    - They track who invited them via this referral record
    """

    __tablename__ = "guest_referrals"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    
    # The person who invited the friend (must be an existing invited guest)
    referrer_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=False
    )
    
    # The friend who was invited by the referrer
    referred_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=False
    )
    
    # Unique token for the referred friend to access the event (like an invitation token)
    invitation_token = db.Column(db.String(500), unique=True, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Short token for SMS-friendly URLs
    short_token = db.Column(db.String(16), unique=True, nullable=True, index=True)

    # Invitation sending tracking
    sent_at = db.Column(db.DateTime, nullable=True)  # First time invitation was sent
    sent_count = db.Column(db.Integer, nullable=False, default=0)  # Number of times sent
    last_sent_at = db.Column(db.DateTime, nullable=True)  # Most recent send time

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship("Event", backref=db.backref("guest_referrals", lazy="dynamic"))
    referrer = db.relationship(
        "Person", 
        foreign_keys=[referrer_person_id],
        backref=db.backref("referrals_made", lazy="dynamic")
    )
    referred = db.relationship(
        "Person",
        foreign_keys=[referred_person_id],
        backref=db.backref("referral_received", uselist=False)
    )

    # Constraints
    __table_args__ = (
        # One person can only be referred once to an event
        db.UniqueConstraint(
            "event_id", "referred_person_id",
            name="unique_event_referred_person"
        ),
        db.Index("idx_referral_event", "event_id"),
        db.Index("idx_referral_referrer", "referrer_person_id"),
    )

    def __repr__(self):
        return f"<GuestReferral event_id={self.event_id} referrer={self.referrer_person_id} referred={self.referred_person_id}>"

    @property
    def is_sent(self):
        """Check if invitation email has been sent."""
        return self.sent_count > 0

    def generate_token(self):
        """Generate a secure token for the referred friend to access the event."""
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app
        from datetime import timedelta
        
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token_data = {
            "event_id": self.event_id,
            "referred_person_id": self.referred_person_id,
            "referral_id": self.id,
            "type": "guest_referral",
        }
        self.invitation_token = serializer.dumps(token_data, salt="guest-referral-token")
        self.token_expires_at = datetime.utcnow() + timedelta(
            days=current_app.config.get("TOKEN_EXPIRATION_DAYS", 90)
        )
        return self.invitation_token

    def generate_short_token(self):
        """Generate a short token for SMS-friendly URLs."""
        while True:
            token = secrets.token_urlsafe(8)[:12]  # 12 chars
            existing = GuestReferral.query.filter_by(short_token=token).first()
            if not existing:
                self.short_token = token
                return token

    @staticmethod
    def verify_token(token):
        """Verify a guest referral token and return the token data.
        
        Args:
            token: The token string to verify
            
        Returns:
            Dictionary with token data if valid, None otherwise
        """
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        from flask import current_app
        
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            # Allow tokens up to 365 days old (configurable)
            max_age = current_app.config.get("TOKEN_EXPIRATION_DAYS", 90) * 24 * 3600
            token_data = serializer.loads(token, salt="guest-referral-token", max_age=max_age)
            
            # Verify it's a guest referral token
            if token_data.get("type") != "guest_referral":
                return None
                
            return token_data
        except (SignatureExpired, BadSignature):
            return None

    @staticmethod
    def get_by_short_token(short_token):
        """Get a GuestReferral by its short token."""
        return GuestReferral.query.filter_by(short_token=short_token).first()

    def to_dict(self):
        """Convert referral to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "referrer_person_id": self.referrer_person_id,
            "referred_person_id": self.referred_person_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_count": self.sent_count,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "is_sent": self.is_sent,
        }

