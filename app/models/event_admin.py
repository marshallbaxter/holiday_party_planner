"""EventAdmin and EventInvitation models."""
import secrets
from datetime import datetime, timedelta
from app import db
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


class EventAdmin(db.Model):
    """Represents admin/organizer access to an event."""

    __tablename__ = "event_admins"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=True)
    household_id = db.Column(
        db.Integer, db.ForeignKey("households.id"), nullable=True
    )
    role = db.Column(
        db.String(20), nullable=False, default="organizer"
    )  # organizer, co-organizer
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    removed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    event = db.relationship("Event", back_populates="admins")
    person = db.relationship("Person")
    household = db.relationship("Household")

    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            "(person_id IS NOT NULL) OR (household_id IS NOT NULL)",
            name="check_admin_target",
        ),
        db.Index("idx_event_admins", "event_id", "removed_at"),
    )

    def __repr__(self):
        return f"<EventAdmin event_id={self.event_id} role={self.role}>"

    @property
    def is_active(self):
        """Check if admin access is currently active."""
        return self.removed_at is None

    def to_dict(self):
        """Convert event admin to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "person_id": self.person_id,
            "household_id": self.household_id,
            "role": self.role,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
            "is_active": self.is_active,
        }


class EventInvitation(db.Model):
    """Represents an invitation sent to a household for an event."""

    __tablename__ = "event_invitations"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    household_id = db.Column(
        db.Integer, db.ForeignKey("households.id"), nullable=False
    )
    invited_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    invitation_token = db.Column(db.String(500), unique=True, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)

    # Short token for SMS-friendly URLs (8-12 characters)
    short_token = db.Column(db.String(16), unique=True, nullable=True, index=True)

    # Invitation sending tracking
    sent_at = db.Column(db.DateTime, nullable=True)  # First time invitation was sent
    sent_count = db.Column(db.Integer, nullable=False, default=0)  # Number of times sent
    last_sent_at = db.Column(db.DateTime, nullable=True)  # Most recent send time

    # SMS sending tracking (separate from email)
    sms_sent_at = db.Column(db.DateTime, nullable=True)  # First time SMS was sent
    sms_sent_count = db.Column(db.Integer, nullable=False, default=0)  # Number of SMS sent
    sms_last_sent_at = db.Column(db.DateTime, nullable=True)  # Most recent SMS send time

    # Relationships
    event = db.relationship("Event", back_populates="invitations")
    household = db.relationship("Household", back_populates="invitations")
    person_links = db.relationship(
        "PersonInvitationLink", back_populates="invitation", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        db.UniqueConstraint("event_id", "household_id", name="unique_event_household"),
        db.Index("idx_invitation_token", "invitation_token"),
    )

    def __repr__(self):
        return f"<EventInvitation event_id={self.event_id} household_id={self.household_id}>"

    def generate_token(self):
        """Generate a secure token for RSVP access."""
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        token_data = {
            "event_id": self.event_id,
            "household_id": self.household_id,
        }
        self.invitation_token = serializer.dumps(token_data, salt="rsvp-token")
        self.token_expires_at = datetime.utcnow() + timedelta(
            days=current_app.config["TOKEN_EXPIRATION_DAYS"]
        )
        return self.invitation_token

    def generate_short_token(self):
        """Generate a short token for SMS-friendly URLs.

        Uses secrets.token_urlsafe to generate a URL-safe token that is
        short enough for SMS messages while still being secure.

        Returns:
            The generated short token (10 characters, ~60 bits of entropy)
        """
        # Generate unique short token, retry if collision (very unlikely)
        max_attempts = 5
        for _ in range(max_attempts):
            # 8 bytes = 64 bits of entropy, produces ~11 characters
            token = secrets.token_urlsafe(8)[:10]  # Truncate to exactly 10 chars
            existing = EventInvitation.query.filter_by(short_token=token).first()
            if not existing:
                self.short_token = token
                return token

        # If we somehow can't generate a unique token after 5 attempts,
        # use a longer token that includes the invitation ID
        self.short_token = f"{self.id}_{secrets.token_urlsafe(4)}"
        return self.short_token

    @staticmethod
    def get_by_short_token(short_token):
        """Find an invitation by its short token.

        Args:
            short_token: The short token to look up

        Returns:
            EventInvitation object or None if not found
        """
        if not short_token:
            return None
        return EventInvitation.query.filter_by(short_token=short_token).first()

    @staticmethod
    def verify_token(token, max_age=None):
        """Verify and decode an invitation token.

        Args:
            token: The token to verify
            max_age: Maximum age in seconds (None = no expiration check)

        Returns:
            Dictionary with event_id and household_id, or None if invalid
        """
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            data = serializer.loads(token, salt="rsvp-token", max_age=max_age)
            return data
        except Exception:
            return None

    def get_rsvp_url(self, _external=True):
        """Get the RSVP URL with token."""
        from flask import url_for

        if not self.invitation_token:
            self.generate_token()

        return url_for(
            "public.rsvp_form",
            event_uuid=self.event.uuid,
            token=self.invitation_token,
            _external=_external,
        )

    def get_event_url(self, _external=True):
        """Get the event public page URL with token.

        This URL directs guests to the event detail page where they can see
        event information and their RSVP status before updating their response.
        """
        from flask import url_for

        if not self.invitation_token:
            self.generate_token()

        return url_for(
            "public.event_detail",
            event_uuid=self.event.uuid,
            token=self.invitation_token,
            _external=_external,
        )

    def get_short_rsvp_url(self, _external=True):
        """Get a short URL for SMS invitations.

        This URL uses the short_token for a more SMS-friendly link length.
        """
        from flask import url_for

        if not self.short_token:
            self.generate_short_token()

        return url_for(
            "public.short_rsvp_redirect",
            short_token=self.short_token,
            _external=_external,
        )

    def get_person_short_url(self, person, _external=True):
        """Get a person-specific short URL for this invitation.

        This creates a unique short link for a specific person in the household,
        enabling personalized landing pages and individual tracking.

        Args:
            person: Person object (must be a member of the invited household)
            _external: Whether to generate an absolute URL

        Returns:
            URL string (e.g., https://domain.com/i/abc123xyz)
        """
        from app.models.person_invitation_link import PersonInvitationLink
        link = PersonInvitationLink.get_or_create(self, person)
        return link.get_short_url(_external=_external)

    @property
    def is_sent(self):
        """Check if invitation email has been sent."""
        return self.sent_at is not None

    @property
    def is_sms_sent(self):
        """Check if invitation SMS has been sent."""
        return self.sms_sent_at is not None

    @property
    def send_status(self):
        """Get human-readable email send status."""
        if not self.is_sent:
            return "pending"
        elif self.sent_count == 1:
            return "sent"
        else:
            return f"sent ({self.sent_count}x)"

    @property
    def sms_send_status(self):
        """Get human-readable SMS send status."""
        if not self.is_sms_sent:
            return "pending"
        elif self.sms_sent_count == 1:
            return "sent"
        else:
            return f"sent ({self.sms_sent_count}x)"

    def mark_as_sent(self):
        """Mark invitation email as sent and update tracking fields."""
        now = datetime.utcnow()
        if not self.sent_at:
            self.sent_at = now
        self.last_sent_at = now
        self.sent_count += 1

    def mark_sms_as_sent(self):
        """Mark invitation SMS as sent and update tracking fields."""
        now = datetime.utcnow()
        if not self.sms_sent_at:
            self.sms_sent_at = now
        self.sms_last_sent_at = now
        self.sms_sent_count += 1

    def to_dict(self):
        """Convert invitation to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "household_id": self.household_id,
            "invited_at": self.invited_at.isoformat() if self.invited_at else None,
            "token_expires_at": (
                self.token_expires_at.isoformat() if self.token_expires_at else None
            ),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "sent_count": self.sent_count,
            "last_sent_at": self.last_sent_at.isoformat() if self.last_sent_at else None,
            "is_sent": self.is_sent,
            "send_status": self.send_status,
            "sms_sent_at": self.sms_sent_at.isoformat() if self.sms_sent_at else None,
            "sms_sent_count": self.sms_sent_count,
            "sms_last_sent_at": (
                self.sms_last_sent_at.isoformat() if self.sms_last_sent_at else None
            ),
            "is_sms_sent": self.is_sms_sent,
            "sms_send_status": self.sms_send_status,
            "short_token": self.short_token,
        }

