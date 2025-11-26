"""RSVP service - business logic for RSVP management."""
from datetime import datetime
from app import db
from app.models import RSVP, Event, Person, Household
from app.services.notification_service import NotificationService


class RSVPService:
    """Service for managing RSVPs."""

    @staticmethod
    def create_rsvps_for_household(event, household):
        """Create RSVP records for all members of a household.

        Args:
            event: Event object
            household: Household object

        Returns:
            List of created RSVP objects
        """
        rsvps = []
        for member in household.active_members:
            # Check if RSVP already exists
            existing_rsvp = RSVP.query.filter_by(
                event_id=event.id, person_id=member.id
            ).first()

            if not existing_rsvp:
                rsvp = RSVP(
                    event_id=event.id,
                    person_id=member.id,
                    household_id=household.id,
                    status="no_response",
                )
                db.session.add(rsvp)
                rsvps.append(rsvp)

        db.session.commit()
        return rsvps

    @staticmethod
    def update_rsvp(rsvp, status, notes=None):
        """Update an RSVP status.

        Args:
            rsvp: RSVP object to update
            status: New status (attending, not_attending, maybe, no_response)
            notes: Optional notes from the guest

        Returns:
            Updated RSVP object
        """
        rsvp.update_status(status, notes)
        db.session.commit()

        # Send confirmation email
        NotificationService.send_rsvp_confirmation(rsvp)

        return rsvp

    @staticmethod
    def update_household_rsvps(event, household, rsvp_data):
        """Update RSVPs for all members of a household.

        Args:
            event: Event object
            household: Household object
            rsvp_data: Dictionary mapping person_id to status and notes
                      Example: {1: {'status': 'attending', 'notes': 'Excited!'}}

        Returns:
            List of updated RSVP objects
        """
        updated_rsvps = []

        for person_id, data in rsvp_data.items():
            rsvp = RSVP.query.filter_by(
                event_id=event.id, person_id=person_id, household_id=household.id
            ).first()

            if rsvp:
                status = data.get("status", "no_response")
                notes = data.get("notes")
                rsvp.update_status(status, notes)
                updated_rsvps.append(rsvp)

        db.session.commit()

        # Send confirmation email to household
        if updated_rsvps:
            NotificationService.send_household_rsvp_confirmation(
                event, household, updated_rsvps
            )

        return updated_rsvps

    @staticmethod
    def get_household_rsvps(event, household):
        """Get all RSVPs for a household for an event.

        Args:
            event: Event object
            household: Household object

        Returns:
            List of RSVP objects
        """
        return RSVP.query.filter_by(
            event_id=event.id, household_id=household.id
        ).all()

    @staticmethod
    def get_attending_count(event):
        """Get count of people attending an event.

        Args:
            event: Event object

        Returns:
            Integer count of attending people
        """
        return RSVP.query.filter_by(event_id=event.id, status="attending").count()

    @staticmethod
    def get_households_without_response(event):
        """Get households that haven't responded to an event.

        Args:
            event: Event object

        Returns:
            List of Household objects
        """
        # Get all invited households
        invitations = event.invitations.all()
        households_without_response = []

        for invitation in invitations:
            household = invitation.household
            rsvps = RSVP.query.filter_by(
                event_id=event.id, household_id=household.id
            ).all()

            # Check if all RSVPs are "no_response"
            if all(rsvp.status == "no_response" for rsvp in rsvps):
                households_without_response.append(household)

        return households_without_response

    @staticmethod
    def update_rsvp_by_host(rsvp, status, host_person_id, notes=None):
        """Update an RSVP status on behalf of a guest (by event host/admin).

        This method is used when a host manually updates a guest's RSVP status,
        typically after receiving RSVP via phone, text, or in-person communication.

        Args:
            rsvp: RSVP object to update
            status: New status (attending, not_attending, maybe, no_response)
            host_person_id: ID of the host/admin making the update
            notes: Optional notes about the update

        Returns:
            Updated RSVP object
        """
        rsvp.update_status(
            status,
            notes=notes,
            updated_by_person_id=host_person_id,
            updated_by_host=True
        )
        db.session.commit()

        # Note: We intentionally do NOT send a confirmation email to the guest
        # when a host updates their RSVP, as the guest already communicated
        # their response directly to the host. If notification is desired,
        # it should be handled separately with appropriate messaging.

        return rsvp

