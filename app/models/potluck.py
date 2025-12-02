"""Potluck-related models."""
from datetime import datetime
from app import db


class PotluckItemContributor(db.Model):
    """Junction table for many-to-many relationship between potluck items and contributors."""

    __tablename__ = "potluck_item_contributors"

    id = db.Column(db.Integer, primary_key=True)
    potluck_item_id = db.Column(
        db.Integer, db.ForeignKey("potluck_items.id", ondelete="CASCADE"), nullable=False
    )
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    potluck_item = db.relationship("PotluckItem", back_populates="contributor_associations")
    person = db.relationship("Person")

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "potluck_item_id", "person_id", name="unique_item_contributor"
        ),
        db.Index("idx_potluck_item_contributors", "potluck_item_id"),
        db.Index("idx_contributor_person", "person_id"),
    )

    def __repr__(self):
        return f"<PotluckItemContributor item_id={self.potluck_item_id} person_id={self.person_id}>"


class PotluckItem(db.Model):
    """Represents a potluck item for an event.

    Items can be either:
    - Suggested items: Created by organizers as suggestions for guests to claim
    - Freeform items: Created by guests to indicate what they're bringing
    """

    __tablename__ = "potluck_items"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(
        db.String(50), nullable=False, default="other"
    )  # main, side, dessert, drink, other
    dietary_tags = db.Column(db.JSON, nullable=True)  # Array of dietary tags
    notes = db.Column(db.Text, nullable=True)
    quantity_needed = db.Column(db.Integer, nullable=True, default=1)
    created_by_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True
    )  # Keep for backward compatibility and tracking original creator
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Suggested item fields
    is_suggested = db.Column(db.Boolean, nullable=False, default=False)
    # For suggested items: the person who claimed it (NULL if unclaimed)
    claimed_by_person_id = db.Column(
        db.Integer, db.ForeignKey("persons.id"), nullable=True
    )
    claimed_at = db.Column(db.DateTime, nullable=True)
    # Details provided by the claimer (separate from organizer's notes)
    claimer_notes = db.Column(db.Text, nullable=True)
    claimer_dietary_tags = db.Column(db.JSON, nullable=True)  # Array of dietary tags

    # Relationships
    event = db.relationship("Event", back_populates="potluck_items")
    created_by = db.relationship("Person", foreign_keys=[created_by_person_id])
    claimed_by = db.relationship("Person", foreign_keys=[claimed_by_person_id])
    claims = db.relationship("PotluckClaim", back_populates="item", lazy="dynamic")
    contributor_associations = db.relationship(
        "PotluckItemContributor",
        back_populates="potluck_item",
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self):
        return f"<PotluckItem {self.name}>"

    @property
    def is_claimed(self):
        """Check if item has been claimed.

        For both suggested and freeform items, check claims relationship.
        Legacy: Also checks claimed_by_person_id for backward compatibility.
        """
        if self.claims.count() > 0:
            return True
        # Legacy fallback for suggested items
        if self.is_suggested and self.claimed_by_person_id is not None:
            return True
        return False

    @property
    def claim_count(self):
        """Get number of claims for this item."""
        count = self.claims.count()
        # Legacy fallback: count old single-claim field if no new claims exist
        if count == 0 and self.is_suggested and self.claimed_by_person_id:
            return 1
        return count

    @property
    def is_fully_claimed(self):
        """Check if item has been fully claimed.

        For suggested items, there's no limit - always allow more claims.
        For freeform items, check against quantity_needed.
        """
        if self.is_suggested:
            # Suggested items can always accept more claims
            return False
        if not self.quantity_needed:
            return self.is_claimed
        return self.claim_count >= self.quantity_needed

    @property
    def remaining_quantity(self):
        """Get remaining quantity needed."""
        if self.is_suggested:
            # Suggested items have unlimited claims
            return 1  # Always allow claiming
        if not self.quantity_needed:
            return 0 if self.is_claimed else 1
        return max(0, self.quantity_needed - self.claim_count)

    def get_dietary_tags_list(self):
        """Get dietary tags as a list."""
        if not self.dietary_tags:
            return []
        return self.dietary_tags if isinstance(self.dietary_tags, list) else []

    def get_claimer_dietary_tags_list(self):
        """Get claimer dietary tags as a list (for suggested items).

        DEPRECATED: Use get_all_claims() to get individual claim dietary tags.
        Returns first claim's dietary tags for backward compatibility.
        """
        # First try new claims system
        first_claim = self.claims.first()
        if first_claim and first_claim.dietary_tags:
            return first_claim.get_dietary_tags_list()
        # Legacy fallback
        if not self.claimer_dietary_tags:
            return []
        return self.claimer_dietary_tags if isinstance(self.claimer_dietary_tags, list) else []

    def get_all_claims(self):
        """Get all claims for this item as a list.

        For suggested items with legacy data, includes the old claimed_by_person_id as a claim.
        Returns list of PotluckClaim objects (or dict for legacy data).
        """
        claims_list = list(self.claims.all())

        # Include legacy claim if it exists and no new claims reference it
        if self.is_suggested and self.claimed_by_person_id:
            legacy_person_ids = [c.person_id for c in claims_list]
            if self.claimed_by_person_id not in legacy_person_ids:
                # Return a dict that mimics PotluckClaim for the legacy claim
                from app.models import Person
                legacy_person = Person.query.get(self.claimed_by_person_id)
                if legacy_person:
                    claims_list.insert(0, {
                        'person': legacy_person,
                        'person_id': self.claimed_by_person_id,
                        'notes': self.claimer_notes,
                        'dietary_tags': self.claimer_dietary_tags or [],
                        'claimed_at': self.claimed_at,
                        'is_legacy': True
                    })

        return claims_list

    def get_claimers_display(self):
        """Get formatted string of claimer names.

        Returns:
            String like "John Doe", "John and Jane Doe", or "John, Jane, and Tommy Doe"
        """
        claims = self.get_all_claims()
        if not claims:
            return None

        names = []
        for claim in claims:
            if isinstance(claim, dict):
                # Legacy claim
                names.append(claim['person'].full_name)
            else:
                # PotluckClaim object
                names.append(claim.person.full_name)

        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} and {names[1]}"
        else:
            return f"{', '.join(names[:-1])}, and {names[-1]}"

    def has_claim_by_person(self, person_id):
        """Check if a specific person has claimed this item."""
        if person_id is None:
            return False
        # Check new claims
        if self.claims.filter_by(person_id=person_id).first():
            return True
        # Check legacy claim
        if self.is_suggested and self.claimed_by_person_id == person_id:
            return True
        return False

    def get_claim_by_person(self, person_id):
        """Get the claim for a specific person, or None if not claimed.

        Returns PotluckClaim object or dict (for legacy claims).
        """
        if person_id is None:
            return None
        # Check new claims first
        claim = self.claims.filter_by(person_id=person_id).first()
        if claim:
            return claim
        # Check legacy claim
        if self.is_suggested and self.claimed_by_person_id == person_id:
            from app.models import Person
            legacy_person = Person.query.get(self.claimed_by_person_id)
            if legacy_person:
                return {
                    'person': legacy_person,
                    'person_id': self.claimed_by_person_id,
                    'notes': self.claimer_notes,
                    'dietary_tags': self.claimer_dietary_tags or [],
                    'claimed_at': self.claimed_at,
                    'is_legacy': True
                }
        return None

    @property
    def contributors(self):
        """Get list of Person objects who are contributors."""
        return [assoc.person for assoc in self.contributor_associations]

    @property
    def contributor_ids(self):
        """Get list of contributor person IDs."""
        return [assoc.person_id for assoc in self.contributor_associations]

    def is_contributor(self, person_id):
        """Check if a person is a contributor to this item."""
        return person_id in self.contributor_ids

    def get_contributors_display(self):
        """Get formatted string of contributor names.

        Returns:
            String like "John Doe", "John and Jane Doe", or "John, Jane, and Tommy Doe"
        """
        contributors = self.contributors
        if not contributors:
            # Fallback to created_by for backward compatibility
            if self.created_by:
                return self.created_by.full_name
            return "Unknown"

        if len(contributors) == 1:
            return contributors[0].full_name
        elif len(contributors) == 2:
            return f"{contributors[0].full_name} and {contributors[1].full_name}"
        else:
            # Three or more: "John, Jane, and Tommy"
            names = [c.full_name for c in contributors[:-1]]
            return f"{', '.join(names)}, and {contributors[-1].full_name}"

    def add_contributor(self, person_id):
        """Add a contributor to this item."""
        if not self.is_contributor(person_id):
            contributor = PotluckItemContributor(
                potluck_item_id=self.id,
                person_id=person_id
            )
            self.contributor_associations.append(contributor)

    def remove_contributor(self, person_id):
        """Remove a contributor from this item."""
        self.contributor_associations = [
            assoc for assoc in self.contributor_associations
            if assoc.person_id != person_id
        ]

    def set_contributors(self, person_ids):
        """Set the contributors for this item, replacing any existing ones."""
        # Delete existing contributors from database
        deleted_count = PotluckItemContributor.query.filter_by(potluck_item_id=self.id).delete()

        # Flush the delete operation to ensure it's executed
        db.session.flush()

        # Expire the contributor_associations relationship to force reload
        db.session.expire(self, ['contributor_associations'])

        # Add new contributors
        for person_id in person_ids:
            contributor = PotluckItemContributor(
                potluck_item_id=self.id,
                person_id=person_id
            )
            db.session.add(contributor)

        # Flush to ensure new contributors are added
        db.session.flush()

    def to_dict(self):
        """Convert potluck item to dictionary."""
        result = {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "category": self.category,
            "dietary_tags": self.get_dietary_tags_list(),
            "notes": self.notes,
            "quantity_needed": self.quantity_needed,
            "claim_count": self.claim_count,
            "is_fully_claimed": self.is_fully_claimed,
            "remaining_quantity": self.remaining_quantity,
            "contributors": [c.full_name for c in self.contributors],
            "contributor_ids": self.contributor_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_suggested": self.is_suggested,
        }
        # Add suggested item fields
        if self.is_suggested:
            result["claimed_by_person_id"] = self.claimed_by_person_id
            result["claimed_by_name"] = self.claimed_by.full_name if self.claimed_by else None
            result["claimed_at"] = self.claimed_at.isoformat() if self.claimed_at else None
            result["claimer_notes"] = self.claimer_notes
            result["claimer_dietary_tags"] = self.get_claimer_dietary_tags_list()
        return result


class PotluckClaim(db.Model):
    """Represents a claim on a potluck item by a person/household.

    Used for both freeform items (multiple claims) and suggested items (multiple claims).
    """

    __tablename__ = "potluck_claims"

    id = db.Column(db.Integer, primary_key=True)
    potluck_item_id = db.Column(
        db.Integer, db.ForeignKey("potluck_items.id"), nullable=False
    )
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False)
    household_id = db.Column(
        db.Integer, db.ForeignKey("households.id"), nullable=True
    )
    claimed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    dietary_tags = db.Column(db.JSON, nullable=True)  # Array of dietary tags for this claim

    # Relationships
    item = db.relationship("PotluckItem", back_populates="claims")
    person = db.relationship("Person", back_populates="potluck_claims")
    household = db.relationship("Household")

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "potluck_item_id", "person_id", name="unique_item_person_claim"
        ),
        db.Index("idx_potluck_claims", "potluck_item_id"),
    )

    def __repr__(self):
        return f"<PotluckClaim item_id={self.potluck_item_id} person_id={self.person_id}>"

    def get_dietary_tags_list(self):
        """Get dietary tags as a list."""
        if not self.dietary_tags:
            return []
        return self.dietary_tags if isinstance(self.dietary_tags, list) else []

    def to_dict(self):
        """Convert potluck claim to dictionary."""
        return {
            "id": self.id,
            "potluck_item_id": self.potluck_item_id,
            "person_id": self.person_id,
            "household_id": self.household_id,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "notes": self.notes,
            "dietary_tags": self.get_dietary_tags_list(),
            "person_name": self.person.full_name if self.person else None,
        }

