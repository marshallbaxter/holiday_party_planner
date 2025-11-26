"""Person model."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Person(db.Model):
    """Represents an individual person (adult or child)."""

    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For organizer login
    role = db.Column(
        db.String(20), nullable=False, default="adult"
    )  # 'adult' or 'child'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    household_memberships = db.relationship(
        "HouseholdMembership", back_populates="person", lazy="dynamic"
    )
    rsvps = db.relationship(
        "RSVP",
        back_populates="person",
        lazy="dynamic",
        foreign_keys="RSVP.person_id"
    )
    potluck_claims = db.relationship(
        "PotluckClaim", back_populates="person", lazy="dynamic"
    )
    message_posts = db.relationship(
        "MessageWallPost", back_populates="person", lazy="dynamic"
    )
    notifications = db.relationship(
        "Notification", back_populates="person", lazy="dynamic"
    )
    person_tags = db.relationship(
        "PersonTag", foreign_keys="PersonTag.person_id", back_populates="person", lazy="dynamic"
    )

    def __repr__(self):
        return f"<Person {self.first_name} {self.last_name}>"

    @property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_adult(self):
        """Check if person is an adult."""
        return self.role == "adult"

    @property
    def is_child(self):
        """Check if person is a child."""
        return self.role == "child"

    @property
    def active_households(self):
        """Get all active households this person belongs to."""
        from app.models.household import HouseholdMembership

        return [
            membership.household
            for membership in self.household_memberships.filter(
                HouseholdMembership.left_at.is_(None)
            ).all()
        ]

    @property
    def primary_household(self):
        """Get the primary household (first active household)."""
        households = self.active_households
        return households[0] if households else None

    def get_rsvp_for_event(self, event_id):
        """Get RSVP for a specific event."""
        return self.rsvps.filter_by(event_id=event_id).first()

    def has_rsvped_for_event(self, event_id):
        """Check if person has RSVPed for an event."""
        rsvp = self.get_rsvp_for_event(event_id)
        return rsvp and rsvp.status != "no_response"

    def set_password(self, password):
        """Set password hash for organizer login."""
        # Use pbkdf2:sha256 method for compatibility with Python 3.9
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check if provided password matches hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def tags(self):
        """Get all tags for this person."""
        from app.models.tag import Tag
        return [pt.tag for pt in self.person_tags.all()]

    @property
    def tag_names(self):
        """Get list of tag names for this person."""
        return [tag.name for tag in self.tags]

    def has_tag(self, tag_name):
        """Check if person has a specific tag.

        Args:
            tag_name: Tag name to check (case-insensitive)

        Returns:
            Boolean
        """
        normalized_name = tag_name.strip().lower()
        return normalized_name in self.tag_names

    def add_tag(self, tag_name, added_by_person_id=None, category="dietary"):
        """Add a tag to this person.

        Args:
            tag_name: Tag name to add
            added_by_person_id: ID of person adding the tag (optional)
            category: Tag category (default: 'dietary')

        Returns:
            PersonTag object or None if tag already exists
        """
        from app.models.tag import Tag, PersonTag

        # Get or create the tag
        tag = Tag.get_or_create(tag_name, category=category)

        # Check if person already has this tag
        existing = PersonTag.query.filter_by(
            person_id=self.id, tag_id=tag.id
        ).first()

        if existing:
            return None  # Tag already exists

        # Create person-tag relationship
        person_tag = PersonTag(
            person_id=self.id,
            tag_id=tag.id,
            added_by_person_id=added_by_person_id
        )
        db.session.add(person_tag)

        # Increment tag usage count
        tag.increment_usage()

        return person_tag

    def remove_tag(self, tag_name):
        """Remove a tag from this person.

        Args:
            tag_name: Tag name to remove (case-insensitive)

        Returns:
            Boolean indicating success
        """
        from app.models.tag import Tag, PersonTag

        # Find the tag
        normalized_name = tag_name.strip().lower()
        tag = Tag.query.filter_by(name=normalized_name).first()

        if not tag:
            return False

        # Find and delete the person-tag relationship
        person_tag = PersonTag.query.filter_by(
            person_id=self.id, tag_id=tag.id
        ).first()

        if not person_tag:
            return False

        db.session.delete(person_tag)

        # Decrement tag usage count
        tag.decrement_usage()

        return True

    def to_dict(self):
        """Convert person to dictionary."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "tags": [tag.name for tag in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

