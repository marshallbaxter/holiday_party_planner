"""Tag and PersonTag models for dietary restrictions and other tags."""
from datetime import datetime
from app import db


class Tag(db.Model):
    """Represents a tag (e.g., dietary restriction) that can be applied to people."""

    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(
        db.String(50), nullable=False, default="dietary"
    )  # 'dietary', 'allergy', 'preference', etc.
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usage_count = db.Column(
        db.Integer, nullable=False, default=0
    )  # Track how many people use this tag

    # Relationships
    person_tags = db.relationship("PersonTag", back_populates="tag", lazy="dynamic")

    def __repr__(self):
        return f"<Tag {self.name}>"

    def increment_usage(self):
        """Increment usage count when tag is added to a person."""
        self.usage_count += 1

    def decrement_usage(self):
        """Decrement usage count when tag is removed from a person."""
        if self.usage_count > 0:
            self.usage_count -= 1

    def to_dict(self):
        """Convert tag to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_or_create(cls, name, category="dietary"):
        """Get existing tag or create new one.

        Args:
            name: Tag name (will be normalized to lowercase)
            category: Tag category (default: 'dietary')

        Returns:
            Tag object
        """
        # Normalize tag name to lowercase for consistency
        normalized_name = name.strip().lower()

        # Try to find existing tag
        tag = cls.query.filter_by(name=normalized_name).first()

        if not tag:
            # Create new tag
            tag = cls(name=normalized_name, category=category)
            db.session.add(tag)
            db.session.flush()  # Get the ID without committing

        return tag

    @classmethod
    def get_popular_tags(cls, limit=20):
        """Get most popular tags by usage count.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of Tag objects
        """
        return cls.query.order_by(cls.usage_count.desc()).limit(limit).all()

    @classmethod
    def search_tags(cls, query, limit=10):
        """Search tags by name prefix.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of Tag objects
        """
        normalized_query = query.strip().lower()
        return (
            cls.query.filter(cls.name.like(f"{normalized_query}%"))
            .order_by(cls.usage_count.desc())
            .limit(limit)
            .all()
        )


class PersonTag(db.Model):
    """Represents a tag assigned to a person (many-to-many relationship)."""

    __tablename__ = "person_tags"

    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    added_by_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True
    )  # Who added this tag

    # Relationships
    person = db.relationship("Person", foreign_keys=[person_id], back_populates="person_tags")
    tag = db.relationship("Tag", back_populates="person_tags")
    added_by = db.relationship("Person", foreign_keys=[added_by_person_id])

    # Constraints
    __table_args__ = (
        db.UniqueConstraint("person_id", "tag_id", name="unique_person_tag"),
        db.Index("idx_person_tags", "person_id"),
        db.Index("idx_tag_persons", "tag_id"),
    )

    def __repr__(self):
        return f"<PersonTag person_id={self.person_id} tag_id={self.tag_id}>"

    def to_dict(self):
        """Convert person tag to dictionary."""
        return {
            "id": self.id,
            "person_id": self.person_id,
            "tag_id": self.tag_id,
            "tag_name": self.tag.name if self.tag else None,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "added_by_person_id": self.added_by_person_id,
        }

