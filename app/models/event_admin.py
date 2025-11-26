"""EventAdmin and EventInvitation models."""
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

    # Invitation sending tracking
    sent_at = db.Column(db.DateTime, nullable=True)  # First time invitation was sent
    sent_count = db.Column(db.Integer, nullable=False, default=0)  # Number of times sent
    last_sent_at = db.Column(db.DateTime, nullable=True)  # Most recent send time

    # Relationships
    event = db.relationship("Event", back_populates="invitations")
    household = db.relationship("Household", back_populates="invitations")

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

    @property
    def is_sent(self):
        """Check if invitation has been sent."""
        return self.sent_at is not None

    @property
    def send_status(self):
        """Get human-readable send status."""
        if not self.is_sent:
            return "pending"
        elif self.sent_count == 1:
            return "sent"
        else:
            return f"sent ({self.sent_count}x)"

    def mark_as_sent(self):
        """Mark invitation as sent and update tracking fields."""
        now = datetime.utcnow()
        if not self.sent_at:
            self.sent_at = now
        self.last_sent_at = now
        self.sent_count += 1

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
        }

