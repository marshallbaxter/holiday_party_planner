"""Event-related models."""
from datetime import datetime
import uuid
from app import db


class Event(db.Model):
    """Represents a holiday party event."""

    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    venue_address = db.Column(db.Text, nullable=True)
    venue_map_url = db.Column(db.String(500), nullable=True)
    rsvp_deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default="draft"
    )  # draft, published, archived
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence_rule = db.Column(db.JSON, nullable=True)
    created_by_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=False
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    created_by = db.relationship("Person", foreign_keys=[created_by_person_id])
    admins = db.relationship("EventAdmin", back_populates="event", lazy="dynamic")
    invitations = db.relationship(
        "EventInvitation", back_populates="event", lazy="dynamic"
    )
    rsvps = db.relationship("RSVP", back_populates="event", lazy="dynamic")
    potluck_items = db.relationship(
        "PotluckItem", back_populates="event", lazy="dynamic"
    )
    message_posts = db.relationship(
        "MessageWallPost", back_populates="event", lazy="dynamic"
    )
    notifications = db.relationship(
        "Notification", back_populates="event", lazy="dynamic"
    )

    def __init__(self, **kwargs):
        """Initialize event with auto-generated UUID."""
        super(Event, self).__init__(**kwargs)
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

    def __repr__(self):
        return f"<Event {self.title}>"

    @property
    def is_draft(self):
        """Check if event is in draft status."""
        return self.status == "draft"

    @property
    def is_published(self):
        """Check if event is published."""
        return self.status == "published"

    @property
    def is_archived(self):
        """Check if event is archived."""
        return self.status == "archived"

    @property
    def is_past(self):
        """Check if event date has passed."""
        return self.event_date < datetime.utcnow()

    @property
    def rsvp_deadline_passed(self):
        """Check if RSVP deadline has passed."""
        if not self.rsvp_deadline:
            return False
        return self.rsvp_deadline < datetime.utcnow()

    def get_url(self, _external=True):
        """Get the public URL for this event."""
        from flask import url_for

        return url_for("public.event_detail", event_uuid=self.uuid, _external=_external)

    def get_organizer_url(self, _external=True):
        """Get the organizer dashboard URL for this event."""
        from flask import url_for

        return url_for(
            "organizer.event_dashboard", event_uuid=self.uuid, _external=_external
        )

    def get_rsvp_stats(self):
        """Get RSVP statistics for this event."""
        all_rsvps = self.rsvps.all()
        return {
            "total": len(all_rsvps),
            "attending": len([r for r in all_rsvps if r.status == "attending"]),
            "not_attending": len([r for r in all_rsvps if r.status == "not_attending"]),
            "maybe": len([r for r in all_rsvps if r.status == "maybe"]),
            "no_response": len([r for r in all_rsvps if r.status == "no_response"]),
        }

    def get_dietary_restrictions(self, min_attendees=2):
        """Get aggregated dietary restrictions for attending guests.

        Returns dietary restriction tags with counts, but only if there are
        at least min_attendees people attending (for privacy protection).

        Args:
            min_attendees: Minimum number of attending guests required to show data (default: 2)

        Returns:
            dict with:
                - show_data: Boolean indicating if data should be displayed
                - attending_count: Number of people attending
                - tags: List of dicts with 'name' and 'count' for each tag
                - message: Optional message to display if data is hidden
        """
        # Get all RSVPs with status "attending"
        attending_rsvps = self.rsvps.filter_by(status="attending").all()
        attending_count = len(attending_rsvps)

        # Check privacy threshold
        if attending_count < min_attendees:
            return {
                "show_data": False,
                "attending_count": attending_count,
                "tags": [],
                "message": "Dietary restrictions will be displayed once more guests RSVP"
            }

        # Aggregate tags from all attending guests
        tag_counts = {}
        for rsvp in attending_rsvps:
            person = rsvp.person
            if person:
                for tag in person.tags:
                    tag_name = tag.name
                    tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1

        # Convert to sorted list (most common first)
        tags_list = [
            {"name": name, "count": count}
            for name, count in sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))
        ]

        return {
            "show_data": True,
            "attending_count": attending_count,
            "tags": tags_list,
            "message": None
        }

    def is_admin_by_person_id(self, person_id):
        """Check if a person is an admin of this event."""
        from app.models.event_admin import EventAdmin
        return EventAdmin.query.filter_by(
            event_id=self.id,
            person_id=person_id,
            removed_at=None
        ).first() is not None

    def to_dict(self):
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "title": self.title,
            "description": self.description,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "venue_address": self.venue_address,
            "venue_map_url": self.venue_map_url,
            "rsvp_deadline": (
                self.rsvp_deadline.isoformat() if self.rsvp_deadline else None
            ),
            "status": self.status,
            "is_recurring": self.is_recurring,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

