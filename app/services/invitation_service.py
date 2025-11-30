"""Invitation service - business logic for sending invitations."""
from app import db
from app.models import EventInvitation, Household
from app.services.notification_service import NotificationService
from app.services.rsvp_service import RSVPService


class InvitationService:
    """Service for managing event invitations."""

    @staticmethod
    def create_invitation(event, household):
        """Create an invitation for a household.

        Args:
            event: Event object
            household: Household object

        Returns:
            Created EventInvitation object
        """
        # Check if invitation already exists
        existing = EventInvitation.query.filter_by(
            event_id=event.id, household_id=household.id
        ).first()

        if existing:
            return existing

        invitation = EventInvitation(event_id=event.id, household_id=household.id)
        invitation.generate_token()

        db.session.add(invitation)
        db.session.commit()

        # Create RSVP records for household members
        RSVPService.create_rsvps_for_household(event, household)

        return invitation

    @staticmethod
    def create_invitations_bulk(event, household_ids):
        """Create invitations for multiple households.

        Args:
            event: Event object
            household_ids: List of household IDs

        Returns:
            List of created EventInvitation objects
        """
        invitations = []

        for household_id in household_ids:
            household = Household.query.get(household_id)
            if household:
                invitation = InvitationService.create_invitation(event, household)
                invitations.append(invitation)

        return invitations

    @staticmethod
    def send_invitation(invitation):
        """Send invitation emails to all household members with email addresses.

        Args:
            invitation: EventInvitation object

        Returns:
            Boolean indicating if at least one email was sent successfully
        """
        household = invitation.household
        contacts = household.contacts_with_email

        if not contacts:
            return False

        # Send invitation email to all contacts via NotificationService
        success_count = 0
        for contact in contacts:
            if NotificationService.send_invitation_email(invitation, contact):
                success_count += 1

        # Mark invitation as sent if at least one email was successful
        if success_count > 0:
            invitation.mark_as_sent()
            db.session.commit()

        return success_count > 0

    @staticmethod
    def send_invitations_bulk(event):
        """Send invitations to all invited households for an event.

        Args:
            event: Event object

        Returns:
            Dictionary with success and failure counts
        """
        invitations = event.invitations.all()
        success_count = 0
        failure_count = 0

        for invitation in invitations:
            if InvitationService.send_invitation(invitation):
                success_count += 1
            else:
                failure_count += 1

        return {"success": success_count, "failure": failure_count}

    @staticmethod
    def resend_invitation(invitation):
        """Resend an invitation to a household.

        Args:
            invitation: EventInvitation object

        Returns:
            Boolean indicating success
        """
        return InvitationService.send_invitation(invitation)

    @staticmethod
    def send_invitation_to_person(invitation, person):
        """Send invitation email to a specific person in a household.

        Args:
            invitation: EventInvitation object
            person: Person object to send invitation to

        Returns:
            Boolean indicating if email was sent successfully
        """
        if not person or not person.email:
            return False

        # Verify person belongs to the invitation's household
        household = invitation.household
        if person not in household.active_members:
            return False

        # Send invitation email to this specific person
        if NotificationService.send_invitation_email(invitation, person):
            # Mark invitation as sent (tracks household-level send status)
            invitation.mark_as_sent()
            db.session.commit()
            return True

        return False

    @staticmethod
    def get_invitation_by_token(token):
        """Get invitation by token.

        Args:
            token: Invitation token string

        Returns:
            EventInvitation object or None
        """
        # Verify token
        token_data = EventInvitation.verify_token(token)
        if not token_data:
            return None

        # Get invitation
        invitation = EventInvitation.query.filter_by(
            event_id=token_data["event_id"], household_id=token_data["household_id"]
        ).first()

        return invitation

    @staticmethod
    def get_invitation_stats(event):
        """Get invitation statistics for an event.

        Args:
            event: Event object

        Returns:
            Dictionary with invitation statistics
        """
        invitations = event.invitations.all()

        total = len(invitations)
        sent = sum(1 for inv in invitations if inv.is_sent)
        pending = total - sent

        # Count households without email
        no_email = sum(1 for inv in invitations if not inv.household.contacts_with_email)

        return {
            "total": total,
            "sent": sent,
            "pending": pending,
            "no_email": no_email,
            "can_send": pending - no_email
        }

    @staticmethod
    def send_invitations_selective(event, household_ids):
        """Send invitations to specific households.

        Args:
            event: Event object
            household_ids: List of household IDs to send invitations to

        Returns:
            Dictionary with success and failure counts
        """
        invitations = EventInvitation.query.filter(
            EventInvitation.event_id == event.id,
            EventInvitation.household_id.in_(household_ids)
        ).all()

        success_count = 0
        failure_count = 0

        for invitation in invitations:
            if InvitationService.send_invitation(invitation):
                success_count += 1
            else:
                failure_count += 1

        return {"success": success_count, "failure": failure_count}

    @staticmethod
    def send_pending_invitations(event):
        """Send invitations only to households that haven't been sent yet.

        Args:
            event: Event object

        Returns:
            Dictionary with success and failure counts
        """
        # Get only pending invitations (not yet sent)
        invitations = EventInvitation.query.filter(
            EventInvitation.event_id == event.id,
            EventInvitation.sent_at.is_(None)
        ).all()

        success_count = 0
        failure_count = 0

        for invitation in invitations:
            if InvitationService.send_invitation(invitation):
                success_count += 1
            else:
                failure_count += 1

        return {"success": success_count, "failure": failure_count}

