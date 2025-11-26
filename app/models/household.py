"""Household and HouseholdMembership models."""
from datetime import datetime
from app import db


class Household(db.Model):
    """Represents a household (group of people)."""

    __tablename__ = "households"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    memberships = db.relationship(
        "HouseholdMembership", back_populates="household", lazy="dynamic"
    )
    invitations = db.relationship(
        "EventInvitation", back_populates="household", lazy="dynamic"
    )
    rsvps = db.relationship("RSVP", back_populates="household", lazy="dynamic")

    def __repr__(self):
        return f"<Household {self.name}>"

    @property
    def active_members(self):
        """Get all active members of this household."""
        return [
            membership.person
            for membership in self.memberships.filter(
                HouseholdMembership.left_at.is_(None)
            ).all()
        ]

    @property
    def adults(self):
        """Get all adult members of this household."""
        return [member for member in self.active_members if member.is_adult]

    @property
    def children(self):
        """Get all child members of this household."""
        return [member for member in self.active_members if member.is_child]

    @property
    def contacts_with_email(self):
        """Get all household members with email addresses."""
        return [member for member in self.active_members if member.email]

    @property
    def contact_emails(self):
        """Get list of all contact email addresses for this household."""
        return [member.email for member in self.contacts_with_email]

    def get_rsvps_for_event(self, event_id):
        """Get all RSVPs for this household for a specific event."""
        return self.rsvps.filter_by(event_id=event_id).all()

    def has_rsvped_for_event(self, event_id):
        """Check if household has any RSVPs for an event."""
        rsvps = self.get_rsvps_for_event(event_id)
        return any(rsvp.status != "no_response" for rsvp in rsvps)

    def to_dict(self):
        """Convert household to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "member_count": len(self.active_members),
            "adult_count": len(self.adults),
            "child_count": len(self.children),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HouseholdMembership(db.Model):
    """Represents a person's membership in a household."""

    __tablename__ = "household_memberships"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    household_id = db.Column(
        db.Integer, db.ForeignKey("households.id"), nullable=False
    )
    role = db.Column(
        db.String(20), nullable=False, default="adult"
    )  # 'adult' or 'child'
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    person = db.relationship("Person", back_populates="household_memberships")
    household = db.relationship("Household", back_populates="memberships")

    # Constraints
    __table_args__ = (
        db.Index("idx_person_household", "person_id", "household_id"),
        db.Index("idx_active_memberships", "household_id", "left_at"),
    )

    def __repr__(self):
        return f"<HouseholdMembership person_id={self.person_id} household_id={self.household_id}>"

    @property
    def is_active(self):
        """Check if membership is currently active."""
        return self.left_at is None

    def to_dict(self):
        """Convert membership to dictionary."""
        return {
            "id": self.id,
            "person_id": self.person_id,
            "household_id": self.household_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None,
            "is_active": self.is_active,
        }

