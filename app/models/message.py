"""Message wall model."""
from datetime import datetime
from app import db


class MessageWallPost(db.Model):
    """Represents a post on an event's message wall."""

    __tablename__ = "message_wall_posts"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_organizer_post = db.Column(db.Boolean, default=False, nullable=False)
    posted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    event = db.relationship("Event", back_populates="message_posts")
    person = db.relationship("Person", back_populates="message_posts")

    # Constraints
    __table_args__ = (db.Index("idx_event_messages", "event_id", "posted_at"),)

    def __repr__(self):
        return f"<MessageWallPost event_id={self.event_id} person_id={self.person_id}>"

    def to_dict(self):
        """Convert message post to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "person_id": self.person_id,
            "person_name": self.person.full_name if self.person else None,
            "message": self.message,
            "is_organizer_post": self.is_organizer_post,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
        }

