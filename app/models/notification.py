"""Notification audit log model."""
from datetime import datetime
from app import db


class Notification(db.Model):
    """Represents a notification sent to a person (audit log)."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    notification_type = db.Column(
        db.String(50), nullable=False
    )  # invitation, rsvp_reminder, potluck_reminder, etc.
    channel = db.Column(db.String(20), nullable=False)  # email, sms
    status = db.Column(
        db.String(20), nullable=False, default="queued"
    )  # queued, sent, failed, bounced
    sent_at = db.Column(db.DateTime, nullable=True)
    provider_message_id = db.Column(
        db.String(255), nullable=True
    )  # ID from Brevo/Twilio
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    event = db.relationship("Event", back_populates="notifications")
    person = db.relationship("Person", back_populates="notifications")

    # Constraints
    __table_args__ = (
        db.Index("idx_notification_status", "event_id", "status"),
        db.Index("idx_notification_type", "event_id", "notification_type"),
        db.Index("idx_person_notifications", "person_id", "sent_at"),
    )

    def __repr__(self):
        return f"<Notification {self.notification_type} to person_id={self.person_id}>"

    def mark_sent(self, provider_message_id=None):
        """Mark notification as sent."""
        self.status = "sent"
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id

    def mark_failed(self, error_message=None):
        """Mark notification as failed."""
        self.status = "failed"
        self.sent_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message

    def mark_bounced(self):
        """Mark notification as bounced."""
        self.status = "bounced"

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "person_id": self.person_id,
            "notification_type": self.notification_type,
            "channel": self.channel,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "provider_message_id": self.provider_message_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

