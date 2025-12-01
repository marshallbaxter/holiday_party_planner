"""Person model."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from app import db
from app.utils.phone_utils import format_phone_e164, format_phone_display


class Person(db.Model):
    """Represents an individual person (adult or child)."""

    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)  # Optional - some guests may only have first name
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For organizer login
    role = db.Column(
        db.String(20), nullable=False, default="adult"
    )  # 'adult' or 'child'

    # Communication preferences for notifications
    preferred_contact_method = db.Column(
        db.String(20), nullable=False, default="email"
    )  # 'email', 'sms', 'both'
    sms_opt_in = db.Column(db.Boolean, nullable=False, default=False)  # SMS consent
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
    invitation_links = db.relationship(
        "PersonInvitationLink", back_populates="person", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Person {self.first_name} {self.last_name}>"

    @property
    def full_name(self):
        """Return full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

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

    @property
    def phone_display(self):
        """Return phone number in user-friendly display format."""
        return format_phone_display(self.phone) if self.phone else ""

    def normalize_phone(self):
        """Normalize the phone number to E.164 format.

        This is called automatically before insert/update via SQLAlchemy event.
        Can also be called manually if needed.

        Returns:
            The normalized phone number, or None if invalid
        """
        if self.phone:
            normalized = format_phone_e164(self.phone)
            if normalized:
                self.phone = normalized
            # If normalization fails, keep original value
            # (allows storing numbers that may be valid but not US format)
        return self.phone

    def normalize_optional_fields(self):
        """Convert empty strings to None for optional fields.

        This is called automatically before insert/update via SQLAlchemy event.
        Ensures that optional fields with UNIQUE constraints (like email) don't
        fail when multiple records have empty values.
        """
        # Convert empty strings to None for optional fields
        if self.last_name is not None and self.last_name.strip() == '':
            self.last_name = None
        if self.email is not None and self.email.strip() == '':
            self.email = None
        if self.phone is not None and self.phone.strip() == '':
            self.phone = None

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

    @property
    def can_receive_sms(self):
        """Check if person can receive SMS notifications.

        Returns True if:
        - Person has a phone number
        - Person has opted in to SMS
        - Person's preferred contact method includes SMS ('sms' or 'both')
        """
        return (
            self.phone
            and self.sms_opt_in
            and self.preferred_contact_method in ('sms', 'both')
        )

    @property
    def can_receive_email(self):
        """Check if person can receive email notifications.

        Returns True if:
        - Person has an email address
        - Person's preferred contact method includes email ('email' or 'both')
        """
        return (
            self.email
            and self.preferred_contact_method in ('email', 'both')
        )

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
            "preferred_contact_method": self.preferred_contact_method,
            "sms_opt_in": self.sms_opt_in,
            "tags": [tag.name for tag in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# SQLAlchemy event listeners to normalize fields before insert/update
@event.listens_for(Person, "before_insert")
def normalize_fields_before_insert(mapper, connection, target):
    """Normalize phone number and convert empty strings to None before inserting."""
    target.normalize_phone()
    target.normalize_optional_fields()


@event.listens_for(Person, "before_update")
def normalize_fields_before_update(mapper, connection, target):
    """Normalize phone number and convert empty strings to None before updating."""
    target.normalize_phone()
    target.normalize_optional_fields()
