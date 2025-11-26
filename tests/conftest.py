"""Pytest configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import Person, Household, Event


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app("testing")
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_person(app):
    """Create a sample person for testing."""
    person = Person(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone="555-0100",
        role="adult"
    )
    db.session.add(person)
    db.session.commit()
    return person


@pytest.fixture
def sample_household(app, sample_person):
    """Create a sample household for testing."""
    from app.models import HouseholdMembership
    
    household = Household(
        name="Test Household",
        address="123 Test St"
    )
    db.session.add(household)
    db.session.commit()
    
    membership = HouseholdMembership(
        person=sample_person,
        household=household,
        role="adult"
    )
    db.session.add(membership)
    db.session.commit()
    
    return household


@pytest.fixture
def sample_event(app, sample_person):
    """Create a sample event for testing."""
    from datetime import datetime, timedelta
    from app.services import EventService
    
    event = EventService.create_event(
        title="Test Event",
        event_date=datetime.now() + timedelta(days=30),
        created_by_person_id=sample_person.id,
        description="Test event description"
    )
    
    return event

