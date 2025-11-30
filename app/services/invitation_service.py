"""Invitation service - business logic for sending invitations."""
from flask import current_app
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
    def send_invitation(invitation, channels=None):
        """Send invitation to all household members via their preferred channels.

        Args:
            invitation: EventInvitation object
            channels: List of channels to use ('email', 'sms', or both).
                     If None, uses each person's preferred_contact_method.

        Returns:
            Boolean indicating if at least one notification was sent successfully
        """
        household = invitation.household
        email_success = 0
        sms_success = 0

        # Get all active household members
        members = household.active_members

        for member in members:
            # Determine which channels to use for this member
            use_email = False
            use_sms = False

            if channels:
                # Explicit channels specified
                use_email = 'email' in channels and member.email
                use_sms = 'sms' in channels and member.can_receive_sms
            else:
                # Use member's preferences
                use_email = member.can_receive_email
                use_sms = member.can_receive_sms

            # Send email if applicable
            if use_email:
                if NotificationService.send_invitation_email(invitation, member):
                    email_success += 1

            # Send SMS if applicable and enabled
            if use_sms and current_app.config.get("ENABLE_SMS"):
                # Ensure short token exists for SMS URL
                if not invitation.short_token:
                    invitation.generate_short_token()
                    db.session.commit()

                if NotificationService.send_invitation_sms(invitation, member):
                    sms_success += 1

        # Mark invitation as sent if at least one notification was successful
        if email_success > 0:
            invitation.mark_as_sent()

        if sms_success > 0:
            invitation.mark_sms_as_sent()

        if email_success > 0 or sms_success > 0:
            db.session.commit()

        return (email_success + sms_success) > 0

    @staticmethod
    def send_invitation_email_only(invitation):
        """Send invitation via email only.

        Args:
            invitation: EventInvitation object

        Returns:
            Boolean indicating if at least one email was sent successfully
        """
        return InvitationService.send_invitation(invitation, channels=['email'])

    @staticmethod
    def send_invitation_sms_only(invitation):
        """Send invitation via SMS only.

        Args:
            invitation: EventInvitation object

        Returns:
            Boolean indicating if at least one SMS was sent successfully
        """
        return InvitationService.send_invitation(invitation, channels=['sms'])

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
    def send_invitation_to_person(invitation, person, channel=None):
        """Send invitation to a specific person in a household.

        Args:
            invitation: EventInvitation object
            person: Person object to send invitation to
            channel: 'email', 'sms', or None (uses person's preference)

        Returns:
            Boolean indicating if notification was sent successfully
        """
        if not person:
            return False

        # Verify person belongs to the invitation's household
        household = invitation.household
        if person not in household.active_members:
            return False

        email_sent = False
        sms_sent = False

        # Determine which channel(s) to use
        if channel == 'email':
            use_email = bool(person.email)
            use_sms = False
        elif channel == 'sms':
            use_email = False
            # When explicitly requesting SMS, only require phone number
            # (organizer is making a deliberate choice to send)
            use_sms = bool(person.phone)
        else:
            # Use person's preferences (respects opt-in settings)
            use_email = person.can_receive_email
            use_sms = person.can_receive_sms

        # Send email if applicable
        if use_email:
            if NotificationService.send_invitation_email(invitation, person):
                invitation.mark_as_sent()
                email_sent = True

        # Send SMS if applicable and enabled
        if use_sms and current_app.config.get("ENABLE_SMS"):
            # Ensure short token exists for SMS URL
            if not invitation.short_token:
                invitation.generate_short_token()

            if NotificationService.send_invitation_sms(invitation, person):
                invitation.mark_sms_as_sent()
                sms_sent = True

        if email_sent or sms_sent:
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
        email_sent = sum(1 for inv in invitations if inv.is_sent)
        sms_sent = sum(1 for inv in invitations if inv.is_sms_sent)
        pending = total - email_sent

        # Count households without email
        no_email = sum(1 for inv in invitations if not inv.household.contacts_with_email)

        # Count households with SMS-capable contacts
        sms_capable = sum(
            1 for inv in invitations
            if any(m.can_receive_sms for m in inv.household.active_members)
        )

        return {
            "total": total,
            "sent": email_sent,  # Backwards compatible
            "email_sent": email_sent,
            "sms_sent": sms_sent,
            "pending": pending,
            "no_email": no_email,
            "can_send": pending - no_email,
            "sms_capable": sms_capable,
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

