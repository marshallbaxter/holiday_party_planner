"""Application entry point."""
import os
from app import create_app, db
from app.models import Person, Household, Event, RSVP  # noqa: F401

# Create Flask application
app = create_app(os.getenv("FLASK_ENV") or "default")


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        "db": db,
        "Person": Person,
        "Household": Household,
        "Event": Event,
        "RSVP": RSVP,
    }


@app.cli.command()
def test():
    """Run the unit tests."""
    import pytest

    pytest.main(["-v", "tests/"])


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")


@app.cli.command()
def seed_db():
    """Seed the database with sample data."""
    from app.utils.seed import seed_database

    seed_database()
    print("Database seeded with sample data!")


@app.cli.command()
def create_admin():
    """Create an admin/organizer account interactively."""
    import getpass
    from app.models import Household, HouseholdMembership

    print("\n" + "=" * 60)
    print("Create Admin/Organizer Account")
    print("=" * 60 + "\n")

    # Get user input
    first_name = input("First name: ").strip()
    if not first_name:
        print("❌ First name is required.")
        return

    last_name = input("Last name: ").strip()
    if not last_name:
        print("❌ Last name is required.")
        return

    email = input("Email address: ").strip().lower()
    if not email:
        print("❌ Email address is required.")
        return

    # Validate email format
    if "@" not in email or "." not in email.split("@")[1]:
        print("❌ Invalid email format.")
        return

    # Check if email already exists
    existing = Person.query.filter_by(email=email).first()
    if existing:
        print(f"\n❌ Error: A person with email {email} already exists.")
        return

    phone = input("Phone number (optional): ").strip() or None

    # Get password securely
    while True:
        password = getpass.getpass("Password (min 8 characters): ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords don't match. Try again.\n")
            continue

        if len(password) < 8:
            print("❌ Password must be at least 8 characters. Try again.\n")
            continue

        break

    # Create household
    household_name = input(
        f"\nHousehold name (default: {last_name} Family): "
    ).strip()
    if not household_name:
        household_name = f"{last_name} Family"

    try:
        # Create person
        person = Person(
            first_name=first_name, last_name=last_name, email=email, phone=phone, role="adult"
        )
        person.set_password(password)
        db.session.add(person)

        # Create household
        household = Household(name=household_name)
        db.session.add(household)
        db.session.flush()  # Get IDs

        # Create membership
        membership = HouseholdMembership(
            person_id=person.id, household_id=household.id
        )
        db.session.add(membership)

        db.session.commit()

        print("\n" + "=" * 60)
        print("✅ Admin account created successfully!")
        print("=" * 60)
        print(f"\nName: {person.full_name}")
        print(f"Email: {person.email}")
        print(f"Household: {household.name}")
        print(f"\nYou can now log in at: {app.config['APP_URL']}/organizer/login")
        print("=" * 60 + "\n")

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error creating admin account: {str(e)}")
        raise


if __name__ == "__main__":
    # For network access from other devices, use:
    # app.run(host="0.0.0.0", port=5000)
    # For localhost only, use:
    # app.run(host="127.0.0.1", port=5000)
    # Or simply: app.run()
    app.run(host="0.0.0.0")

