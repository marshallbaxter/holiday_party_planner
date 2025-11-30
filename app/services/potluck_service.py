"""Potluck service - business logic for potluck management."""
from datetime import datetime
from app import db
from app.models import PotluckItem, PotluckClaim, Event, Person


class PotluckService:
    """Service for managing potluck items and claims."""

    @staticmethod
    def create_item(
        event, name, category="other", dietary_tags=None, notes=None, quantity_needed=1,
        created_by_person_id=None, contributor_ids=None
    ):
        """Create a potluck item.

        Args:
            event: Event object
            name: Item name
            category: Item category (main, side, dessert, drink, other)
            dietary_tags: List of dietary tags
            notes: Additional notes
            quantity_needed: Number of this item needed
            created_by_person_id: ID of person creating the item
            contributor_ids: List of person IDs who are contributing to this item

        Returns:
            Created PotluckItem object
        """
        item = PotluckItem(
            event_id=event.id,
            name=name,
            category=category,
            dietary_tags=dietary_tags or [],
            notes=notes,
            quantity_needed=quantity_needed,
            created_by_person_id=created_by_person_id,
        )

        db.session.add(item)
        db.session.flush()  # Flush to get the item ID

        # Add contributors
        if contributor_ids:
            item.set_contributors(contributor_ids)
        elif created_by_person_id:
            # Backward compatibility: if no contributors specified, add creator as contributor
            item.set_contributors([created_by_person_id])

        db.session.commit()

        return item

    @staticmethod
    def update_item(item, contributor_ids=None, **kwargs):
        """Update a potluck item.

        Args:
            item: PotluckItem object
            contributor_ids: List of person IDs who are contributing (optional)
            **kwargs: Fields to update

        Returns:
            Updated PotluckItem object
        """
        allowed_fields = ["name", "category", "dietary_tags", "notes", "quantity_needed"]

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(item, field, value)

        # Update contributors if provided
        if contributor_ids is not None:
            item.set_contributors(contributor_ids)

        db.session.commit()

        return item

    @staticmethod
    def delete_item(item):
        """Delete a potluck item.

        Args:
            item: PotluckItem object

        Returns:
            Boolean indicating success
        """
        # Delete all claims first
        PotluckClaim.query.filter_by(potluck_item_id=item.id).delete()
        db.session.delete(item)
        db.session.commit()

        return True

    @staticmethod
    def claim_item(item, person, household=None, notes=None):
        """Claim a potluck item.

        Args:
            item: PotluckItem object
            person: Person object claiming the item
            household: Household object (optional)
            notes: Additional notes from claimer

        Returns:
            Created PotluckClaim object or None if item is fully claimed
        """
        # Check if item is fully claimed
        if item.is_fully_claimed:
            return None

        # Check if person has already claimed this item
        existing_claim = PotluckClaim.query.filter_by(
            potluck_item_id=item.id, person_id=person.id
        ).first()

        if existing_claim:
            return existing_claim

        claim = PotluckClaim(
            potluck_item_id=item.id,
            person_id=person.id,
            household_id=household.id if household else None,
            notes=notes,
        )

        db.session.add(claim)
        db.session.commit()

        return claim

    @staticmethod
    def unclaim_item(claim):
        """Remove a claim on a potluck item.

        Args:
            claim: PotluckClaim object

        Returns:
            Boolean indicating success
        """
        db.session.delete(claim)
        db.session.commit()

        return True

    @staticmethod
    def get_items_by_category(event):
        """Get potluck items grouped by category.

        Args:
            event: Event object

        Returns:
            Dictionary mapping category to list of items
        """
        items = event.potluck_items.all()
        categories = {}

        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        return categories

    @staticmethod
    def get_unclaimed_items(event):
        """Get all unclaimed potluck items for an event.

        Args:
            event: Event object

        Returns:
            List of PotluckItem objects
        """
        items = event.potluck_items.all()
        return [item for item in items if not item.is_fully_claimed]

    @staticmethod
    def get_person_claims(event, person):
        """Get all items claimed by a person for an event.

        Args:
            event: Event object
            person: Person object

        Returns:
            List of PotluckClaim objects
        """
        return (
            PotluckClaim.query.join(PotluckItem)
            .filter(PotluckItem.event_id == event.id, PotluckClaim.person_id == person.id)
            .all()
        )

    @staticmethod
    def get_person_contributions(event, person_id):
        """Get all potluck items a person is contributing to for an event.

        Args:
            event: Event object
            person_id: ID of the person

        Returns:
            List of PotluckItem objects where person is a contributor
        """
        from app.models import PotluckItemContributor

        # Get all items for this event where person is a contributor
        items = (
            PotluckItem.query
            .join(PotluckItemContributor)
            .filter(
                PotluckItem.event_id == event.id,
                PotluckItemContributor.person_id == person_id
            )
            .all()
        )

        return items

    # ==================== Suggested Items Methods ====================

    @staticmethod
    def create_suggested_item(event, name, category="other", notes=None):
        """Create a suggested potluck item (created by organizer for guests to claim).

        Args:
            event: Event object
            name: Item name
            category: Item category (main, side, dessert, drink, other)
            notes: Additional notes/description

        Returns:
            Created PotluckItem object
        """
        item = PotluckItem(
            event_id=event.id,
            name=name,
            category=category,
            notes=notes,
            is_suggested=True,
        )

        db.session.add(item)
        db.session.commit()

        return item

    @staticmethod
    def update_suggested_item(item, **kwargs):
        """Update a suggested potluck item.

        Args:
            item: PotluckItem object (must be a suggested item)
            **kwargs: Fields to update

        Returns:
            Updated PotluckItem object
        """
        if not item.is_suggested:
            raise ValueError("Cannot use this method on non-suggested items")

        allowed_fields = ["name", "category", "notes"]

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(item, field, value)

        db.session.commit()

        return item

    @staticmethod
    def delete_suggested_item(item):
        """Delete a suggested potluck item.

        Args:
            item: PotluckItem object (must be a suggested item)

        Returns:
            Boolean indicating success
        """
        if not item.is_suggested:
            raise ValueError("Cannot use this method on non-suggested items")

        db.session.delete(item)
        db.session.commit()

        return True

    @staticmethod
    def claim_suggested_item(item, person, claimer_notes=None, claimer_dietary_tags=None):
        """Claim a suggested potluck item.

        Args:
            item: PotluckItem object (must be a suggested item)
            person: Person object claiming the item
            claimer_notes: Optional notes from the claimer about what they're bringing
            claimer_dietary_tags: Optional list of dietary tags for the item

        Returns:
            Updated PotluckItem object or None if already claimed
        """
        if not item.is_suggested:
            raise ValueError("Cannot use this method on non-suggested items")

        # Check if item is already claimed
        if item.claimed_by_person_id is not None:
            return None

        item.claimed_by_person_id = person.id
        item.claimed_at = datetime.utcnow()
        item.claimer_notes = claimer_notes
        item.claimer_dietary_tags = claimer_dietary_tags if claimer_dietary_tags else None

        db.session.commit()

        return item

    @staticmethod
    def update_claim_details(item, person, claimer_notes=None, claimer_dietary_tags=None):
        """Update the details of a claimed suggested item.

        Args:
            item: PotluckItem object (must be a suggested item claimed by the person)
            person: Person object who claimed the item
            claimer_notes: Notes from the claimer about what they're bringing
            claimer_dietary_tags: List of dietary tags for the item

        Returns:
            Updated PotluckItem object or None if not claimed by this person
        """
        if not item.is_suggested:
            raise ValueError("Cannot use this method on non-suggested items")

        # Check if item is claimed by this person
        if item.claimed_by_person_id != person.id:
            return None

        item.claimer_notes = claimer_notes
        item.claimer_dietary_tags = claimer_dietary_tags if claimer_dietary_tags else None

        db.session.commit()

        return item

    @staticmethod
    def unclaim_suggested_item(item, person):
        """Unclaim a suggested potluck item.

        Args:
            item: PotluckItem object (must be a suggested item)
            person: Person object unclaiming the item

        Returns:
            Updated PotluckItem object or None if not claimed by this person
        """
        if not item.is_suggested:
            raise ValueError("Cannot use this method on non-suggested items")

        # Check if item is claimed by this person
        if item.claimed_by_person_id != person.id:
            return None

        item.claimed_by_person_id = None
        item.claimed_at = None
        item.claimer_notes = None
        item.claimer_dietary_tags = None

        db.session.commit()

        return item

    @staticmethod
    def get_suggested_items(event):
        """Get all suggested potluck items for an event.

        Args:
            event: Event object

        Returns:
            List of PotluckItem objects that are suggested items
        """
        return PotluckItem.query.filter_by(
            event_id=event.id,
            is_suggested=True
        ).order_by(PotluckItem.category, PotluckItem.name).all()

    @staticmethod
    def get_suggested_items_by_category(event):
        """Get suggested potluck items grouped by category.

        Args:
            event: Event object

        Returns:
            Dictionary mapping category to list of suggested items
        """
        items = PotluckService.get_suggested_items(event)
        categories = {}

        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        return categories

    @staticmethod
    def get_freeform_items(event):
        """Get all freeform (non-suggested) potluck items for an event.

        Args:
            event: Event object

        Returns:
            List of PotluckItem objects that are freeform items
        """
        return PotluckItem.query.filter_by(
            event_id=event.id,
            is_suggested=False
        ).order_by(PotluckItem.category, PotluckItem.name).all()

    @staticmethod
    def get_freeform_items_by_category(event):
        """Get freeform potluck items grouped by category.

        Args:
            event: Event object

        Returns:
            Dictionary mapping category to list of freeform items
        """
        items = PotluckService.get_freeform_items(event)
        categories = {}

        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        return categories

    @staticmethod
    def get_person_suggested_claims(event, person):
        """Get all suggested items claimed by a person for an event.

        Args:
            event: Event object
            person: Person object

        Returns:
            List of PotluckItem objects (suggested items claimed by person)
        """
        return PotluckItem.query.filter_by(
            event_id=event.id,
            is_suggested=True,
            claimed_by_person_id=person.id
        ).all()

