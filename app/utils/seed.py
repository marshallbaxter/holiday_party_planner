"""Database seeding utilities for development."""
from datetime import datetime, timedelta
from app import db
from app.models import Person, Household, HouseholdMembership, Event, EventAdmin
from app.services import EventService, InvitationService


def seed_database():
    """Seed the database with sample data for development."""
    # Clear existing data
    db.drop_all()
    db.create_all()

    # Create people
    john = Person(
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone="555-0101",
        role="adult",
    )
    john.set_password("password123")  # Set password for login

    jane = Person(
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone="555-0102",
        role="adult",
    )
    jane.set_password("password123")  # Set password for login

    timmy = Person(
        first_name="Timmy", last_name="Smith", email=None, phone=None, role="child"
    )

    bob = Person(
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        phone="555-0201",
        role="adult",
    )
    bob.set_password("password123")  # Set password for login

    alice = Person(
        first_name="Alice",
        last_name="Johnson",
        email="alice.johnson@example.com",
        phone="555-0202",
        role="adult",
    )
    alice.set_password("password123")  # Set password for login

    mary = Person(
        first_name="Mary",
        last_name="Williams",
        email="mary.williams@example.com",
        phone="555-0301",
        role="adult",
    )
    mary.set_password("password123")  # Set password for login

    db.session.add_all([john, jane, timmy, bob, alice, mary])
    db.session.commit()

    # Create households
    smith_household = Household(name="Smith Family", address="123 Main St, Anytown, USA")
    johnson_household = Household(
        name="Johnson Family", address="456 Oak Ave, Anytown, USA"
    )
    williams_household = Household(
        name="Williams Household", address="789 Pine Rd, Anytown, USA"
    )

    db.session.add_all([smith_household, johnson_household, williams_household])
    db.session.commit()

    # Create household memberships
    memberships = [
        HouseholdMembership(
            person=john, household=smith_household, role="adult", is_primary_contact=True
        ),
        HouseholdMembership(
            person=jane, household=smith_household, role="adult", is_primary_contact=False
        ),
        HouseholdMembership(
            person=timmy, household=smith_household, role="child", is_primary_contact=False
        ),
        HouseholdMembership(
            person=bob, household=johnson_household, role="adult", is_primary_contact=True
        ),
        HouseholdMembership(
            person=alice,
            household=johnson_household,
            role="adult",
            is_primary_contact=False,
        ),
        HouseholdMembership(
            person=mary,
            household=williams_household,
            role="adult",
            is_primary_contact=True,
        ),
    ]

    db.session.add_all(memberships)
    db.session.commit()

    # Create an event
    event_date = datetime.now() + timedelta(days=30)
    rsvp_deadline = datetime.now() + timedelta(days=20)

    event = EventService.create_event(
        title="Annual Holiday Party 2024",
        description="Join us for our annual holiday celebration with food, games, and fun!",
        event_date=event_date,
        venue_address="Community Center, 100 Center St, Anytown, USA",
        venue_map_url="https://maps.google.com/?q=Community+Center+Anytown",
        rsvp_deadline=rsvp_deadline,
        created_by_person_id=john.id,
        is_recurring=True,
    )

    # Publish the event
    EventService.publish_event(event)

    # Create invitations
    InvitationService.create_invitation(event, smith_household)
    InvitationService.create_invitation(event, johnson_household)
    InvitationService.create_invitation(event, williams_household)

    print("\n" + "="*60)
    print("Database seeded successfully!")
    print("="*60)
    print(f"\n📅 Sample Event: {event.title}")
    print(f"🔗 Event URL: /event/{event.uuid}")
    print(f"\n👤 Organizer Login Credentials:")
    print(f"   Email: {john.email}")
    print(f"   Password: password123")
    print(f"\n💡 Other test accounts (all use password: password123):")
    print(f"   - jane.smith@example.com")
    print(f"   - bob.johnson@example.com")
    print(f"   - alice.johnson@example.com")
    print(f"   - mary.williams@example.com")
    print("\n" + "="*60 + "\n")

