"""Tests for database models."""
import pytest
from app.models import Person, Household, Event, RSVP


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

