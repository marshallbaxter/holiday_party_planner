"""Event service - business logic for event management."""
from datetime import datetime
from app import db
from app.models import Event, EventAdmin, EventInvitation, Person, Household


class EventService:
    """Service for managing events."""

    @staticmethod
    def create_event(
        title,
        event_date,
        created_by_person_id,
        description=None,
        venue_address=None,
        venue_map_url=None,
        rsvp_deadline=None,
        is_recurring=False,
        recurrence_rule=None,
        status="draft",
    ):
        """Create a new event.

        Args:
            title: Event title
            event_date: Date and time of the event
            created_by_person_id: ID of the person creating the event
            description: Event description (optional)
            venue_address: Venue address (optional)
            venue_map_url: URL to map (optional)
            rsvp_deadline: RSVP deadline (optional)
            is_recurring: Whether event recurs annually (optional)
            recurrence_rule: Recurrence rule as JSON (optional)
            status: Event status - draft, published, or archived (optional, defaults to draft)

        Returns:
            Created Event object
        """
        event = Event(
            title=title,
            description=description,
            event_date=event_date,
            venue_address=venue_address,
            venue_map_url=venue_map_url,
            rsvp_deadline=rsvp_deadline,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
            created_by_person_id=created_by_person_id,
            status=status,
        )

        db.session.add(event)

        # Add creator as organizer
        admin = EventAdmin(
            event=event, person_id=created_by_person_id, role="organizer"
        )
        db.session.add(admin)

        db.session.commit()

        return event

    @staticmethod
    def update_event(event, **kwargs):
        """Update event details.

        Args:
            event: Event object to update
            **kwargs: Fields to update

        Returns:
            Updated Event object
        """
        allowed_fields = [
            "title",
            "description",
            "event_date",
            "venue_address",
            "venue_map_url",
            "rsvp_deadline",
            "status",
            "is_recurring",
            "recurrence_rule",
        ]

        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(event, field, value)

        event.updated_at = datetime.utcnow()
        db.session.commit()

        return event

    @staticmethod
    def publish_event(event):
        """Publish an event (make it visible to guests).

        Args:
            event: Event object to publish

        Returns:
            Updated Event object
        """
        event.status = "published"
        event.updated_at = datetime.utcnow()
        db.session.commit()

        return event

    @staticmethod
    def archive_event(event):
        """Archive an event after it has passed.

        Args:
            event: Event object to archive

        Returns:
            Updated Event object
        """
        event.status = "archived"
        event.updated_at = datetime.utcnow()
        db.session.commit()

        return event

    @staticmethod
    def add_admin(event, person_id=None, household_id=None, role="co-organizer"):
        """Add an admin/co-organizer to an event.

        Args:
            event: Event object
            person_id: ID of person to add as admin (optional)
            household_id: ID of household to add as admin (optional)
            role: Admin role (organizer or co-organizer)

        Returns:
            Created EventAdmin object
        """
        if not person_id and not household_id:
            raise ValueError("Must provide either person_id or household_id")

        admin = EventAdmin(
            event=event, person_id=person_id, household_id=household_id, role=role
        )
        db.session.add(admin)
        db.session.commit()

        return admin

    @staticmethod
    def remove_admin(event_admin):
        """Remove an admin from an event.

        Args:
            event_admin: EventAdmin object to remove

        Returns:
            Updated EventAdmin object
        """
        event_admin.removed_at = datetime.utcnow()
        db.session.commit()

        return event_admin

    @staticmethod
    def copy_guest_list_from_event(target_event, source_event):
        """Copy guest list from one event to another.

        Args:
            target_event: Event to copy guests to
            source_event: Event to copy guests from

        Returns:
            Number of households copied
        """
        # Get all invitations from source event
        source_invitations = source_event.invitations.all()

        copied_count = 0
        for source_invitation in source_invitations:
            # Check if household is already invited to target event
            existing = EventInvitation.query.filter_by(
                event_id=target_event.id, household_id=source_invitation.household_id
            ).first()

            if not existing:
                new_invitation = EventInvitation(
                    event_id=target_event.id, household_id=source_invitation.household_id
                )
                db.session.add(new_invitation)
                copied_count += 1

        db.session.commit()

        return copied_count

