"""Bring-a-Friend service - business logic for guest referrals."""
from datetime import datetime
from app import db
from app.models import Person, RSVP, Event, GuestReferral


class BringFriendService:
    """Service for managing 'bring a friend' functionality."""

    @staticmethod
    def create_friend(first_name, last_name=None, email=None, phone=None):
        """Create a new Person record for a brought friend.
        
        Friends don't require household association.
        
        Args:
            first_name: Friend's first name (required)
            last_name: Friend's last name (optional)
            email: Friend's email (optional)
            phone: Friend's phone number (optional)
            
        Returns:
            Created Person object
        """
        person = Person(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role="adult",  # Friends are assumed to be adults
        )
        db.session.add(person)
        db.session.flush()  # Get the ID without committing
        return person

    @staticmethod
    def create_referral(event, referrer_person, referred_person):
        """Create a GuestReferral record linking referrer to referred friend.
        
        Args:
            event: Event object
            referrer_person: Person object of the guest who is inviting the friend
            referred_person: Person object of the friend being invited
            
        Returns:
            Created GuestReferral object
        """
        # Check if referral already exists
        existing = GuestReferral.query.filter_by(
            event_id=event.id,
            referred_person_id=referred_person.id
        ).first()
        
        if existing:
            return existing
            
        referral = GuestReferral(
            event_id=event.id,
            referrer_person_id=referrer_person.id,
            referred_person_id=referred_person.id,
        )
        db.session.add(referral)
        db.session.flush()  # Get the ID for token generation
        
        # Generate tokens for the friend to access the event
        referral.generate_token()
        referral.generate_short_token()
        
        return referral

    @staticmethod
    def create_rsvp_for_friend(event, referred_person):
        """Create an RSVP record for a brought friend.
        
        Friends have RSVPs without household association.
        
        Args:
            event: Event object
            referred_person: Person object of the friend
            
        Returns:
            Created RSVP object
        """
        # Check if RSVP already exists
        existing = RSVP.query.filter_by(
            event_id=event.id,
            person_id=referred_person.id
        ).first()
        
        if existing:
            return existing
            
        rsvp = RSVP(
            event_id=event.id,
            person_id=referred_person.id,
            household_id=None,  # Friends don't have household association
            status="no_response",
        )
        db.session.add(rsvp)
        return rsvp

    @staticmethod
    def invite_friend(event, referrer_person, first_name, last_name=None, email=None, phone=None):
        """Complete flow to invite a friend to an event.

        Creates the Person, GuestReferral, and RSVP records.
        Sends an invitation email if the friend has an email address.

        Args:
            event: Event object
            referrer_person: Person object of the guest inviting the friend
            first_name: Friend's first name
            last_name: Friend's last name (optional)
            email: Friend's email (optional)
            phone: Friend's phone number (optional)

        Returns:
            Dictionary with created objects: {person, referral, rsvp, email_sent}
        """
        # Check if a person with this email already exists
        if email:
            existing_person = Person.query.filter_by(email=email).first()
            if existing_person:
                # Check if they're already invited to this event
                existing_rsvp = RSVP.query.filter_by(
                    event_id=event.id,
                    person_id=existing_person.id
                ).first()
                if existing_rsvp:
                    raise ValueError(f"A person with email {email} is already invited to this event")
                # Use existing person
                person = existing_person
            else:
                person = BringFriendService.create_friend(first_name, last_name, email, phone)
        else:
            person = BringFriendService.create_friend(first_name, last_name, email, phone)

        # Create the referral record
        referral = BringFriendService.create_referral(event, referrer_person, person)

        # Create the RSVP
        rsvp = BringFriendService.create_rsvp_for_friend(event, person)

        db.session.commit()

        # Send invitation email if friend has email
        email_sent = False
        if person.email:
            from app.services.notification_service import NotificationService
            try:
                email_sent = NotificationService.send_friend_invitation_email(referral, person)
            except Exception:
                # Log but don't fail the invitation if email fails
                pass

        return {
            "person": person,
            "referral": referral,
            "rsvp": rsvp,
            "email_sent": email_sent,
        }

    @staticmethod
    def get_friends_for_event(event):
        """Get all brought friends for an event.

        Args:
            event: Event object

        Returns:
            List of dictionaries with friend info and referrer info
        """
        referrals = GuestReferral.query.filter_by(event_id=event.id).all()

        friends = []
        for referral in referrals:
            rsvp = RSVP.query.filter_by(
                event_id=event.id,
                person_id=referral.referred_person_id
            ).first()

            friends.append({
                "person": referral.referred,
                "referrer": referral.referrer,
                "referral": referral,
                "rsvp": rsvp,
            })

        return friends

    @staticmethod
    def get_friends_invited_by_person(event, referrer_person):
        """Get all friends invited by a specific person for an event.

        Args:
            event: Event object
            referrer_person: Person object of the referrer

        Returns:
            List of GuestReferral objects
        """
        return GuestReferral.query.filter_by(
            event_id=event.id,
            referrer_person_id=referrer_person.id
        ).all()

    @staticmethod
    def can_person_invite_friends(event, person):
        """Check if a person can invite friends to an event.

        A person can invite friends if:
        - They have an RSVP for the event (either through household or as a brought friend)
        - They are attending or have responded positively

        Args:
            event: Event object
            person: Person object

        Returns:
            Boolean
        """
        rsvp = RSVP.query.filter_by(
            event_id=event.id,
            person_id=person.id
        ).first()

        # Must have an RSVP to invite friends
        if not rsvp:
            return False

        # For now, allow anyone with an RSVP to invite friends
        # Could be restricted to only "attending" status if desired
        return True

    @staticmethod
    def get_referral_by_token(token):
        """Get a GuestReferral by its invitation token.

        Args:
            token: The invitation token string

        Returns:
            GuestReferral object or None
        """
        token_data = GuestReferral.verify_token(token)
        if not token_data:
            return None

        return GuestReferral.query.get(token_data.get("referral_id"))

    @staticmethod
    def get_referral_by_short_token(short_token):
        """Get a GuestReferral by its short token.

        Args:
            short_token: The short token string

        Returns:
            GuestReferral object or None
        """
        return GuestReferral.get_by_short_token(short_token)

    @staticmethod
    def remove_friend(referral):
        """Remove a brought friend from an event.

        Deletes the referral and RSVP records. The Person record is kept.

        Args:
            referral: GuestReferral object

        Returns:
            Boolean indicating success
        """
        # Delete the RSVP
        rsvp = RSVP.query.filter_by(
            event_id=referral.event_id,
            person_id=referral.referred_person_id
        ).first()

        if rsvp:
            db.session.delete(rsvp)

        # Delete the referral
        db.session.delete(referral)
        db.session.commit()

        return True

