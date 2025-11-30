"""Tests for database models."""
import pytest
from app.models import Person, Household, Event, RSVP, EventInvitation


def test_person_creation(sample_person):
    """Test person model creation."""
    assert sample_person.id is not None
    assert sample_person.full_name == "Test User"
    assert sample_person.is_adult is True
    assert sample_person.is_child is False


def test_household_creation(sample_household):
    """Test household model creation."""
    assert sample_household.id is not None
    assert sample_household.name == "Test Household"
    assert len(sample_household.active_members) == 1


def test_household_primary_contact(sample_household, sample_person):
    """Test household primary contact."""
    assert sample_household.primary_contact == sample_person
    assert sample_household.primary_contact_email == sample_person.email


def test_event_creation(sample_event):
    """Test event model creation."""
    assert sample_event.id is not None
    assert sample_event.uuid is not None
    assert sample_event.title == "Test Event"
    assert sample_event.is_draft is True


def test_event_url_generation(sample_event):
    """Test event URL generation."""
    url = sample_event.get_url(_external=False)
    assert f"/event/{sample_event.uuid}" in url


def test_rsvp_creation(app, sample_event, sample_person, sample_household):
    """Test RSVP model creation."""
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="attending"
    )
    
    from app import db
    db.session.add(rsvp)
    db.session.commit()
    
    assert rsvp.id is not None
    assert rsvp.is_attending is True
    assert rsvp.has_responded is True


def test_rsvp_status_update(app, sample_event, sample_person, sample_household):
    """Test RSVP status update."""
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="no_response"
    )

    from app import db
    db.session.add(rsvp)
    db.session.commit()

    assert rsvp.has_responded is False

    rsvp.update_status("attending", "Looking forward to it!")
    db.session.commit()

    assert rsvp.is_attending is True
    assert rsvp.has_responded is True
    assert rsvp.notes == "Looking forward to it!"
    assert rsvp.responded_at is not None
    assert rsvp.updated_by_host is False
    assert rsvp.updated_by_person_id is None


def test_rsvp_host_update(app, sample_event, sample_person, sample_household):
    """Test RSVP status update by host."""
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="no_response"
    )

    from app import db
    db.session.add(rsvp)
    db.session.commit()

    # Create a host person
    host = Person(
        first_name="Host",
        last_name="Admin",
        email="host@example.com",
        role="adult"
    )
    db.session.add(host)
    db.session.commit()

    # Update RSVP as host
    rsvp.update_status(
        "attending",
        notes="Guest called to confirm",
        updated_by_person_id=host.id,
        updated_by_host=True
    )
    db.session.commit()

    assert rsvp.is_attending is True
    assert rsvp.has_responded is True
    assert rsvp.notes == "Guest called to confirm"
    assert rsvp.updated_by_host is True
    assert rsvp.updated_by_person_id == host.id
    assert rsvp.updated_by is not None
    assert rsvp.updated_by.full_name == "Host Admin"


# EventInvitation Tests

def test_invitation_creation(sample_invitation):
    """Test invitation model creation."""
    assert sample_invitation.id is not None
    assert sample_invitation.event_id is not None
    assert sample_invitation.household_id is not None


def test_invitation_token_generation(sample_invitation):
    """Test invitation token generation."""
    # Token should not exist initially
    assert sample_invitation.invitation_token is None

    # Generate token
    token = sample_invitation.generate_token()

    assert token is not None
    assert sample_invitation.invitation_token == token
    assert sample_invitation.token_expires_at is not None


def test_invitation_token_verification(app, sample_invitation):
    """Test invitation token verification."""
    # Generate token
    sample_invitation.generate_token()
    token = sample_invitation.invitation_token

    # Verify token
    token_data = EventInvitation.verify_token(token)

    assert token_data is not None
    assert token_data["event_id"] == sample_invitation.event_id
    assert token_data["household_id"] == sample_invitation.household_id


def test_invitation_get_rsvp_url(sample_invitation, sample_event):
    """Test get_rsvp_url returns URL to RSVP form."""
    url = sample_invitation.get_rsvp_url(_external=False)

    # Should point to the RSVP form route
    assert "/rsvp" in url
    assert sample_event.uuid in url
    assert "token=" in url

    # Token should be generated if not exists
    assert sample_invitation.invitation_token is not None


def test_invitation_get_event_url(sample_invitation, sample_event):
    """Test get_event_url returns URL to event public page."""
    url = sample_invitation.get_event_url(_external=False)

    # Should point to the event detail route (not /rsvp)
    assert f"/event/{sample_event.uuid}" in url
    assert "/rsvp" not in url
    assert "token=" in url

    # Token should be generated if not exists
    assert sample_invitation.invitation_token is not None


def test_invitation_get_event_url_vs_rsvp_url(sample_invitation, sample_event):
    """Test that get_event_url and get_rsvp_url return different URLs."""
    event_url = sample_invitation.get_event_url(_external=False)
    rsvp_url = sample_invitation.get_rsvp_url(_external=False)

    # Both should include the event UUID
    assert sample_event.uuid in event_url
    assert sample_event.uuid in rsvp_url

    # Both should include the same token
    assert sample_invitation.invitation_token in event_url
    assert sample_invitation.invitation_token in rsvp_url

    # But they should be different routes
    assert event_url != rsvp_url
    assert "/rsvp" in rsvp_url
    assert "/rsvp" not in event_url


def test_invitation_url_auto_generates_token(app, sample_event, sample_household):
    """Test that URL methods auto-generate token if not exists."""
    from app import db

    # Create invitation without token
    invitation = EventInvitation(
        event_id=sample_event.id,
        household_id=sample_household.id
    )
    db.session.add(invitation)
    db.session.commit()

    assert invitation.invitation_token is None

    # get_event_url should auto-generate token
    url = invitation.get_event_url(_external=False)

    assert invitation.invitation_token is not None
    assert invitation.invitation_token in url


# RSVPService Individual Email Tests

def test_update_household_rsvps_sends_email_on_status_change(
    app, sample_event, sample_person, sample_household, sample_invitation
):
    """Test that emails are sent when RSVP status changes."""
    from unittest.mock import patch, MagicMock
    from app import db
    from app.services.rsvp_service import RSVPService

    # Create RSVP with initial status
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="no_response"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Mock the notification service
    with patch(
        "app.services.rsvp_service.NotificationService.send_individual_rsvp_confirmations"
    ) as mock_send:
        mock_send.return_value = {"success": 1, "failure": 0}

        # Update RSVP with changed status
        rsvp_data = {sample_person.id: {"status": "attending", "notes": "Looking forward to it!"}}
        updated_rsvps = RSVPService.update_household_rsvps(
            sample_event, sample_household, rsvp_data
        )

        # Verify email was sent
        assert mock_send.called
        call_args = mock_send.call_args
        assert call_args[0][0] == sample_event  # First arg is event
        assert len(call_args[0][1]) == 1  # Second arg is list of RSVPs with changed status
        assert call_args[0][1][0].status == "attending"


def test_update_household_rsvps_no_email_on_same_status(
    app, sample_event, sample_person, sample_household, sample_invitation
):
    """Test that no email is sent when RSVP status doesn't change."""
    from unittest.mock import patch
    from app import db
    from app.services.rsvp_service import RSVPService

    # Create RSVP with initial status
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Mock the notification service
    with patch(
        "app.services.rsvp_service.NotificationService.send_individual_rsvp_confirmations"
    ) as mock_send:
        # Update RSVP with SAME status (only notes changed)
        rsvp_data = {sample_person.id: {"status": "attending", "notes": "Updated notes"}}
        updated_rsvps = RSVPService.update_household_rsvps(
            sample_event, sample_household, rsvp_data
        )

        # Verify RSVP was updated
        assert len(updated_rsvps) == 1
        assert updated_rsvps[0].notes == "Updated notes"

        # Verify email was NOT sent (status didn't change)
        assert not mock_send.called


def test_update_household_rsvps_partial_status_change(app, sample_event, sample_household):
    """Test that only people with changed status receive emails in multi-person household."""
    from unittest.mock import patch
    from app import db
    from app.models import HouseholdMembership
    from app.services.rsvp_service import RSVPService

    # Create second person in household
    person2 = Person(
        first_name="Second",
        last_name="Person",
        email="second@example.com",
        role="adult"
    )
    db.session.add(person2)
    db.session.commit()

    membership2 = HouseholdMembership(
        person=person2,
        household=sample_household,
        role="adult"
    )
    db.session.add(membership2)
    db.session.commit()

    # Get first person from household
    person1 = sample_household.active_members[0]

    # Create RSVPs for both people
    rsvp1 = RSVP(
        event_id=sample_event.id,
        person_id=person1.id,
        household_id=sample_household.id,
        status="no_response"
    )
    rsvp2 = RSVP(
        event_id=sample_event.id,
        person_id=person2.id,
        household_id=sample_household.id,
        status="attending"  # Already attending
    )
    db.session.add_all([rsvp1, rsvp2])
    db.session.commit()

    # Mock the notification service
    with patch(
        "app.services.rsvp_service.NotificationService.send_individual_rsvp_confirmations"
    ) as mock_send:
        mock_send.return_value = {"success": 1, "failure": 0}

        # Update both RSVPs: person1 changes status, person2 keeps same status
        rsvp_data = {
            person1.id: {"status": "attending", "notes": ""},  # Status CHANGES
            person2.id: {"status": "attending", "notes": "Still coming!"}  # Status SAME
        }
        updated_rsvps = RSVPService.update_household_rsvps(
            sample_event, sample_household, rsvp_data
        )

        # Verify both RSVPs were updated
        assert len(updated_rsvps) == 2

        # Verify email was sent only for person1 (status changed)
        assert mock_send.called
        call_args = mock_send.call_args
        changed_rsvps = call_args[0][1]
        assert len(changed_rsvps) == 1
        assert changed_rsvps[0].person_id == person1.id


def test_send_individual_rsvp_confirmations_skips_no_email(app, sample_event, sample_household):
    """Test that people without email addresses are skipped."""
    from unittest.mock import patch
    from app import db
    from app.models import HouseholdMembership
    from app.services.notification_service import NotificationService

    # Create person without email
    person_no_email = Person(
        first_name="No",
        last_name="Email",
        email=None,  # No email
        role="adult"
    )
    db.session.add(person_no_email)
    db.session.commit()

    membership = HouseholdMembership(
        person=person_no_email,
        household=sample_household,
        role="adult"
    )
    db.session.add(membership)
    db.session.commit()

    # Create RSVP for person without email
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=person_no_email.id,
        household_id=sample_household.id,
        status="attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Mock the send_rsvp_confirmation method
    with patch.object(
        NotificationService, "send_rsvp_confirmation", return_value=True
    ) as mock_send:
        result = NotificationService.send_individual_rsvp_confirmations(
            sample_event, [rsvp]
        )

        # Verify no emails were sent (person has no email)
        assert not mock_send.called
        assert result["success"] == 0
        assert result["failure"] == 0


def test_send_individual_rsvp_confirmations_sends_to_people_with_email(
    app, sample_event, sample_person, sample_household, sample_invitation
):
    """Test that emails are sent to people with email addresses."""
    from unittest.mock import patch
    from app import db
    from app.services.notification_service import NotificationService

    # Create RSVP for person with email
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Mock the send_rsvp_confirmation method
    with patch.object(
        NotificationService, "send_rsvp_confirmation", return_value=True
    ) as mock_send:
        result = NotificationService.send_individual_rsvp_confirmations(
            sample_event, [rsvp]
        )

        # Verify email was sent
        assert mock_send.called
        assert mock_send.call_count == 1
        assert result["success"] == 1
        assert result["failure"] == 0


# Email Template Tests

def test_rsvp_confirmation_email_template_attending(app, sample_event, sample_person, sample_household, sample_invitation):
    """Test that RSVP confirmation email shows correct message for attending status."""
    from app import db
    from flask import render_template

    # Create RSVP with attending status
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the template
    html_content = render_template(
        "emails/rsvp_confirmation.html",
        rsvp=rsvp,
        event=sample_event,
        invitation=sample_invitation
    )

    # Verify the attending message is present
    assert "We're looking forward to seeing you there!" in html_content
    assert "We're sorry you can't make it" not in html_content
    assert "might be able to make it" not in html_content


def test_rsvp_confirmation_email_template_maybe(app, sample_event, sample_person, sample_household, sample_invitation):
    """Test that RSVP confirmation email shows correct message for maybe status."""
    from app import db
    from flask import render_template

    # Create RSVP with maybe status
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="maybe"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the template
    html_content = render_template(
        "emails/rsvp_confirmation.html",
        rsvp=rsvp,
        event=sample_event,
        invitation=sample_invitation
    )

    # Verify the maybe message is present
    assert "Thanks for letting us know you might be able to make it!" in html_content
    assert "We hope to see you there." in html_content
    assert "We're sorry you can't make it" not in html_content
    assert "We're looking forward to seeing you there!" not in html_content


def test_rsvp_confirmation_email_template_not_attending(app, sample_event, sample_person, sample_household, sample_invitation):
    """Test that RSVP confirmation email shows correct message for not_attending status."""
    from app import db
    from flask import render_template

    # Create RSVP with not_attending status
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="not_attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the template
    html_content = render_template(
        "emails/rsvp_confirmation.html",
        rsvp=rsvp,
        event=sample_event,
        invitation=sample_invitation
    )

    # Verify the not_attending message is present
    assert "We're sorry you can't make it" in html_content
    assert "Hope to see you at the next event!" in html_content
    assert "might be able to make it" not in html_content
    assert "We're looking forward to seeing you there!" not in html_content


def test_rsvp_form_excludes_no_response_option(app, sample_event, sample_person, sample_household, sample_invitation):
    """Test that the RSVP form does not include 'No Response' as a selectable option."""
    from app import db
    from flask import render_template

    # Create RSVP with no_response status (initial state)
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=sample_person.id,
        household_id=sample_household.id,
        status="no_response"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the RSVP form template
    html_content = render_template(
        "public/rsvp_form.html",
        event=sample_event,
        rsvps=[rsvp],
        request=type('obj', (object,), {'args': type('obj', (object,), {'get': lambda self, x: 'test_token'})()})()
    )

    # Verify that only the three valid options are present
    assert 'value="attending"' in html_content
    assert 'value="not_attending"' in html_content
    assert 'value="maybe"' in html_content

    # Verify that "no_response" is NOT an option in the form
    assert 'value="no_response"' not in html_content

    # Also verify the display text is correct
    assert "✓ Attending" in html_content
    assert "✗ Not Attending" in html_content
    assert "? Maybe" in html_content
    assert "No Response" not in html_content


def test_rsvp_form_shows_missing_contact_info_inline(app, sample_event, sample_household, sample_invitation):
    """Test that RSVP form shows inline inputs for members missing contact info."""
    from app import db
    from app.models import HouseholdMembership
    from flask import render_template

    # Create person without email or phone
    person_no_contact = Person(
        first_name="NoContact",
        last_name="Person",
        email=None,
        phone=None,
        role="adult"
    )
    db.session.add(person_no_contact)
    db.session.commit()

    membership = HouseholdMembership(
        person=person_no_contact,
        household=sample_household,
        role="adult"
    )
    db.session.add(membership)
    db.session.commit()

    # Create RSVP for person without contact info
    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=person_no_contact.id,
        household_id=sample_household.id,
        status="no_response"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the RSVP form template
    html_content = render_template(
        "public/rsvp_form.html",
        event=sample_event,
        household=sample_household,
        rsvps=[rsvp],
        token='test_token',
    )

    # Verify the inline email input is displayed
    assert "Add email to receive updates" in html_content
    assert "NoContact" in html_content
    assert f'name="email_{person_no_contact.id}"' in html_content

    # Verify the inline phone input is displayed
    assert "Add phone number" in html_content
    assert f'name="phone_{person_no_contact.id}"' in html_content


def test_rsvp_form_no_contact_inputs_when_all_have_info(app, sample_event, sample_household, sample_invitation):
    """Test that no inline contact inputs are shown when all members have contact info."""
    from app import db
    from flask import render_template

    # Create person with both email and phone
    person_with_contact = Person(
        first_name="HasContact",
        last_name="Person",
        email="hascontact@example.com",
        phone="555-123-4567",
        role="adult"
    )
    db.session.add(person_with_contact)
    db.session.commit()

    from app.models import HouseholdMembership
    membership = HouseholdMembership(
        person=person_with_contact,
        household=sample_household,
        role="adult"
    )
    db.session.add(membership)
    db.session.commit()

    rsvp = RSVP(
        event_id=sample_event.id,
        person_id=person_with_contact.id,
        household_id=sample_household.id,
        status="attending"
    )
    db.session.add(rsvp)
    db.session.commit()

    # Render the RSVP form template
    html_content = render_template(
        "public/rsvp_form.html",
        event=sample_event,
        household=sample_household,
        rsvps=[rsvp],
        token='test_token',
    )

    # Verify NO inline contact inputs are displayed
    assert "Add email to receive updates" not in html_content
    assert "Add phone number" not in html_content

