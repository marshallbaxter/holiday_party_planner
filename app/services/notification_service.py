"""Notification service - handles email/SMS sending via Brevo."""
from flask import current_app, render_template, url_for
from app import db
from app.models import Notification, EventInvitation
from app.models.guest_referral import GuestReferral
from app.utils.phone_utils import format_phone_e164
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


class NotificationService:
    """Service for sending notifications via email and SMS."""

    @staticmethod
    def _get_brevo_email_api_instance():
        """Get configured Brevo Email API instance."""
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = current_app.config["BREVO_API_KEY"]
        return sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    @staticmethod
    def _get_brevo_sms_api_instance():
        """Get configured Brevo SMS API instance."""
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = current_app.config["BREVO_API_KEY"]
        return sib_api_v3_sdk.TransactionalSMSApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    # Backwards compatibility alias
    @staticmethod
    def _get_brevo_api_instance():
        """Get configured Brevo API instance (backwards compatibility)."""
        return NotificationService._get_brevo_email_api_instance()

    @staticmethod
    def send_email(to_email, to_name, subject, html_content, event=None, person=None):
        """Send an email via Brevo.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML email content
            event: Event object (optional, for logging)
            person: Person object (optional, for logging)

        Returns:
            Boolean indicating success
        """
        if not current_app.config.get("BREVO_API_KEY"):
            current_app.logger.warning("Brevo API key not configured, skipping email")
            return False

        try:
            api_instance = NotificationService._get_brevo_api_instance()

            sender = {
                "name": current_app.config["BREVO_SENDER_NAME"],
                "email": current_app.config["BREVO_SENDER_EMAIL"],
            }
            to = [{"email": to_email, "name": to_name}]

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to, sender=sender, subject=subject, html_content=html_content
            )

            api_response = api_instance.send_transac_email(send_smtp_email)

            # Log notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="email",
                    channel="email",
                )
                notification.mark_sent(provider_message_id=api_response.message_id)
                db.session.add(notification)
                db.session.commit()

            current_app.logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except ApiException as e:
            current_app.logger.error(f"Brevo API error sending to {to_email}: {e}")

            # Log failed notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="email",
                    channel="email",
                )
                notification.mark_failed(error_message=str(e))
                db.session.add(notification)
                db.session.commit()

            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error sending email to {to_email}: {e}")

            # Log failed notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="email",
                    channel="email",
                )
                notification.mark_failed(error_message=str(e))
                db.session.add(notification)
                db.session.commit()

            return False

    @staticmethod
    def send_sms(to_phone, content, event=None, person=None):
        """Send an SMS via Brevo.

        Args:
            to_phone: Recipient phone number (E.164 format preferred, e.g., +12025551234)
            content: SMS message content (max 160 chars for single SMS)
            event: Event object (optional, for logging)
            person: Person object (optional, for logging)

        Returns:
            Boolean indicating success
        """
        if not current_app.config.get("ENABLE_SMS"):
            current_app.logger.warning("SMS is disabled, skipping SMS send")
            return False

        if not current_app.config.get("BREVO_API_KEY"):
            current_app.logger.warning("Brevo API key not configured, skipping SMS")
            return False

        # Validate and format phone number to E.164
        if not to_phone:
            current_app.logger.warning("No phone number provided for SMS")
            return False

        # Format to E.164 (e.g., +12025551234)
        formatted_phone = format_phone_e164(to_phone)
        if not formatted_phone:
            current_app.logger.warning(
                f"Invalid phone number format: {to_phone}. "
                "Could not convert to E.164 format."
            )
            return False

        try:
            api_instance = NotificationService._get_brevo_sms_api_instance()

            sender = current_app.config.get("BREVO_SMS_SENDER_NAME", "HolidayParty")

            send_transac_sms = sib_api_v3_sdk.SendTransacSms(
                sender=sender,
                recipient=formatted_phone,
                content=content,
                type="transactional"
            )

            api_response = api_instance.send_transac_sms(send_transac_sms)

            # Log notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="invitation",
                    channel="sms",
                )
                notification.mark_sent(provider_message_id=str(api_response.message_id))
                db.session.add(notification)
                db.session.commit()

            current_app.logger.info(f"SMS sent successfully to {formatted_phone}")
            return True

        except ApiException as e:
            current_app.logger.error(f"Brevo API error sending SMS to {formatted_phone}: {e}")

            # Log failed notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="invitation",
                    channel="sms",
                )
                notification.mark_failed(error_message=str(e))
                db.session.add(notification)
                db.session.commit()

            return False
        except Exception as e:
            current_app.logger.error(f"Unexpected error sending SMS to {formatted_phone}: {e}")

            # Log failed notification
            if event and person:
                notification = Notification(
                    event_id=event.id,
                    person_id=person.id,
                    notification_type="invitation",
                    channel="sms",
                )
                notification.mark_failed(error_message=str(e))
                db.session.add(notification)
                db.session.commit()

            return False

    @staticmethod
    def send_invitation_email(invitation, contact_person):
        """Send invitation email to a specific household member.

        Args:
            invitation: EventInvitation object
            contact_person: Person object to send invitation to

        Returns:
            Boolean indicating success
        """
        event = invitation.event
        household = invitation.household

        if not contact_person or not contact_person.email:
            return False

        subject = f"You're invited to {event.title}"
        html_content = render_template(
            "emails/invitation.html",
            event=event,
            household=household,
            invitation=invitation,
            recipient=contact_person
        )

        return NotificationService.send_email(
            to_email=contact_person.email,
            to_name=contact_person.full_name,
            subject=subject,
            html_content=html_content,
            event=event,
            person=contact_person,
        )

    @staticmethod
    def send_invitation_sms(invitation, contact_person):
        """Send invitation SMS to a specific household member.

        Args:
            invitation: EventInvitation object
            contact_person: Person object to send invitation to

        Returns:
            Boolean indicating success
        """
        if not current_app.config.get("ENABLE_SMS"):
            return False

        event = invitation.event

        if not contact_person or not contact_person.phone:
            return False

        # Note: opt-in check is handled at the service layer (InvitationService)
        # When an organizer explicitly sends SMS, we allow it if person has a phone

        # Generate SMS content using template
        sms_content = render_template(
            "sms/invitation.txt",
            event=event,
            invitation=invitation,
            recipient=contact_person
        )

        return NotificationService.send_sms(
            to_phone=contact_person.phone,
            content=sms_content,
            event=event,
            person=contact_person,
        )

    @staticmethod
    def send_friend_invitation_email(referral, friend_person):
        """Send invitation email to a brought friend.

        Args:
            referral: GuestReferral object containing the referral relationship
            friend_person: Person object of the friend being invited

        Returns:
            Boolean indicating success
        """
        from flask import url_for

        if not friend_person or not friend_person.email:
            return False

        event = referral.event
        referrer = referral.referrer

        # Construct the event URL using the referral's invitation token
        event_url = url_for(
            "public.event_detail",
            event_uuid=event.uuid,
            token=referral.invitation_token,
            _external=True
        )

        subject = f"{referrer.first_name} invited you to {event.title}"
        html_content = render_template(
            "emails/friend_invitation.html",
            event=event,
            referrer=referrer,
            recipient=friend_person,
            referral=referral,
            event_url=event_url
        )

        success = NotificationService.send_email(
            to_email=friend_person.email,
            to_name=friend_person.full_name,
            subject=subject,
            html_content=html_content,
            event=event,
            person=friend_person,
        )

        # Log the notification with friend_invitation type
        if success:
            notification = Notification(
                event_id=event.id,
                person_id=friend_person.id,
                notification_type="friend_invitation",
                channel="email",
            )
            notification.mark_sent()
            db.session.add(notification)
            db.session.commit()

        return success

    @staticmethod
    def send_rsvp_confirmation(rsvp):
        """Send RSVP confirmation email.

        Args:
            rsvp: RSVP object

        Returns:
            Boolean indicating success
        """
        person = rsvp.person
        event = rsvp.event

        if not person.email:
            return False

        # Determine the event URL based on whether this is a household guest or brought friend
        event_url = None
        invitation = None
        referral = None

        if rsvp.household_id:
            # Regular household guest - get their invitation
            invitation = EventInvitation.query.filter_by(
                event_id=event.id, household_id=rsvp.household_id
            ).first()
            if invitation:
                event_url = invitation.get_event_url()
        else:
            # Brought friend - look up their referral
            referral = GuestReferral.query.filter_by(
                event_id=event.id, referred_person_id=person.id
            ).first()
            if referral and referral.invitation_token:
                event_url = url_for(
                    "public.event_detail",
                    event_uuid=event.uuid,
                    token=referral.invitation_token,
                    _external=True
                )

        subject = f"RSVP Confirmed for {event.title}"
        html_content = render_template(
            "emails/rsvp_confirmation.html",
            rsvp=rsvp,
            event=event,
            invitation=invitation,
            referral=referral,
            event_url=event_url
        )

        return NotificationService.send_email(
            to_email=person.email,
            to_name=person.full_name,
            subject=subject,
            html_content=html_content,
            event=event,
            person=person,
        )

    @staticmethod
    def send_individual_rsvp_confirmations(event, rsvps):
        """Send individual RSVP confirmation emails to people whose status changed.

        Each person receives their own personalized email with their individual
        RSVP status. Only sends to people who have an email address.

        Args:
            event: Event object
            rsvps: List of RSVP objects for people whose status changed

        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0

        for rsvp in rsvps:
            person = rsvp.person
            if not person.email:
                # Skip people without email addresses
                continue

            if NotificationService.send_rsvp_confirmation(rsvp):
                success_count += 1
            else:
                failure_count += 1

        return {"success": success_count, "failure": failure_count}

    @staticmethod
    def send_household_rsvp_confirmation(event, household, rsvps):
        """Send RSVP confirmation email to all household members with email.

        DEPRECATED: Use send_individual_rsvp_confirmations() instead for
        individual personalized emails.

        Args:
            event: Event object
            household: Household object
            rsvps: List of RSVP objects

        Returns:
            Boolean indicating if at least one email was sent successfully
        """
        contacts = household.contacts_with_email

        if not contacts:
            return False

        # Get invitation for dashboard link
        invitation = EventInvitation.query.filter_by(
            event_id=event.id, household_id=household.id
        ).first()

        subject = f"RSVP Confirmed for {event.title}"

        success_count = 0
        for contact in contacts:
            html_content = render_template(
                "emails/household_rsvp_confirmation.html",
                event=event,
                household=household,
                rsvps=rsvps,
                recipient=contact,
                invitation=invitation
            )

            if NotificationService.send_email(
                to_email=contact.email,
                to_name=contact.full_name,
                subject=subject,
                html_content=html_content,
                event=event,
                person=contact,
            ):
                success_count += 1

        return success_count > 0

    @staticmethod
    def send_rsvp_reminders(event):
        """Send RSVP reminders to households who haven't responded.

        Args:
            event: Event object

        Returns:
            Dictionary with success and failure counts
        """
        from app.services.rsvp_service import RSVPService

        households = RSVPService.get_households_without_response(event)
        success_count = 0
        failure_count = 0

        for household in households:
            # TODO: Implement RSVP reminder email
            pass

        return {"success": success_count, "failure": failure_count}

    @staticmethod
    def send_potluck_reminders(event):
        """Send potluck reminders to attending households.

        Args:
            event: Event object

        Returns:
            Dictionary with success and failure counts
        """
        # TODO: Implement potluck reminder logic
        return {"success": 0, "failure": 0}

    @staticmethod
    def send_magic_link_email(person, token):
        """Send magic link login email.

        Args:
            person: Person object
            token: AuthToken object

        Returns:
            Boolean indicating success
        """
        if not person.email:
            return False

        from flask import url_for

        magic_link_url = url_for(
            "organizer.verify_magic_link",
            token=token.token,
            _external=True
        )

        subject = f"Your login link for {current_app.config['APP_NAME']}"
        html_content = render_template(
            "emails/magic_link.html",
            person=person,
            magic_link_url=magic_link_url,
            expiration_minutes=current_app.config["MAGIC_LINK_EXPIRATION_MINUTES"]
        )

        return NotificationService.send_email(
            to_email=person.email,
            to_name=person.full_name,
            subject=subject,
            html_content=html_content,
            person=person,
        )

    @staticmethod
    def send_password_reset_email(person, token):
        """Send password reset email.

        Args:
            person: Person object
            token: AuthToken object

        Returns:
            Boolean indicating success
        """
        if not person.email:
            return False

        from flask import url_for

        reset_url = url_for(
            "organizer.reset_password",
            token=token.token,
            _external=True
        )

        subject = f"Reset your password for {current_app.config['APP_NAME']}"
        html_content = render_template(
            "emails/password_reset.html",
            person=person,
            reset_url=reset_url,
            expiration_minutes=current_app.config["PASSWORD_RESET_EXPIRATION_MINUTES"]
        )

        return NotificationService.send_email(
            to_email=person.email,
            to_name=person.full_name,
            subject=subject,
            html_content=html_content,
            person=person,
        )

