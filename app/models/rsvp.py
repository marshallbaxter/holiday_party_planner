"""RSVP model."""
from datetime import datetime
from app import db


class RSVP(db.Model):
    """Represents an RSVP response from a person for an event."""

    __tablename__ = "rsvps"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    household_id = db.Column(
        db.Integer, db.ForeignKey("households.id"), nullable=False
    )
    status = db.Column(
        db.String(20), nullable=False, default="no_response"
    )  # attending, not_attending, maybe, no_response
    responded_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    updated_by_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True
    )  # Person who last updated the RSVP (host or guest)
    updated_by_host = db.Column(
        db.Boolean, default=False, nullable=False
    )  # True if last update was by a host/admin

    # Relationships
    event = db.relationship("Event", back_populates="rsvps")
    person = db.relationship("Person", back_populates="rsvps", foreign_keys=[person_id])
    household = db.relationship("Household", back_populates="rsvps")
    updated_by = db.relationship(
        "Person", foreign_keys=[updated_by_person_id], lazy="joined"
    )

    # Constraints
    __table_args__ = (
        db.UniqueConstraint("event_id", "person_id", name="unique_event_person_rsvp"),
        db.Index("idx_event_household_rsvp", "event_id", "household_id"),
        db.Index("idx_rsvp_status", "event_id", "status"),
    )

    def __repr__(self):
        return f"<RSVP event_id={self.event_id} person_id={self.person_id} status={self.status}>"

    @property
    def is_attending(self):
        """Check if person is attending."""
        return self.status == "attending"

    @property
    def is_not_attending(self):
        """Check if person is not attending."""
        return self.status == "not_attending"

    @property
    def is_maybe(self):
        """Check if person's attendance is uncertain."""
        return self.status == "maybe"

    @property
    def has_responded(self):
        """Check if person has responded to the invitation."""
        return self.status != "no_response"

    def update_status(self, new_status, notes=None, updated_by_person_id=None, updated_by_host=False):
        """Update RSVP status.

        Args:
            new_status: New status (attending, not_attending, maybe, no_response)
            notes: Optional notes from the guest
            updated_by_person_id: ID of person who updated the RSVP (optional)
            updated_by_host: True if update was made by a host/admin (default: False)
        """
        valid_statuses = ["attending", "not_attending", "maybe", "no_response"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        self.status = new_status
        if notes is not None:
            self.notes = notes

        if new_status != "no_response":
            self.responded_at = datetime.utcnow()
        else:
            self.responded_at = None

        self.updated_at = datetime.utcnow()
        self.updated_by_person_id = updated_by_person_id
        self.updated_by_host = updated_by_host

    def to_dict(self):
        """Convert RSVP to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "person_id": self.person_id,
            "household_id": self.household_id,
            "status": self.status,
            "responded_at": (
                self.responded_at.isoformat() if self.responded_at else None
            ),
            "notes": self.notes,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by_person_id": self.updated_by_person_id,
            "updated_by_host": self.updated_by_host,
        }

