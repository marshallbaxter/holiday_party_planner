"""Tests for message wall functionality."""
import pytest
from app import db
from app.models import (
    Person, Household, Event, EventInvitation, EventAdmin,
    MessageWallPost, HouseholdMembership
)


class TestMessageWallPost:
    """Tests for the MessageWallPost model."""

    def test_message_post_creation(self, app, sample_event, sample_person):
        """Test creating a message wall post."""
        post = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Hello everyone!",
            is_organizer_post=False
        )
        db.session.add(post)
        db.session.commit()

        assert post.id is not None
        assert post.message == "Hello everyone!"
        assert post.is_organizer_post is False
        assert post.posted_at is not None
        assert post.person.full_name == "Test User"

    def test_message_post_organizer_flag(self, app, sample_event, sample_person):
        """Test message post with organizer flag."""
        post = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Organizer announcement",
            is_organizer_post=True
        )
        db.session.add(post)
        db.session.commit()

        assert post.is_organizer_post is True

    def test_message_post_to_dict(self, app, sample_event, sample_person):
        """Test message post serialization."""
        post = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Test message",
            is_organizer_post=False
        )
        db.session.add(post)
        db.session.commit()

        data = post.to_dict()
        assert data["id"] == post.id
        assert data["message"] == "Test message"
        assert data["person_name"] == "Test User"
        assert data["is_organizer_post"] is False
        assert data["posted_at"] is not None

    def test_event_message_posts_relationship(self, app, sample_event, sample_person):
        """Test that event has correct relationship to messages."""
        # Create multiple posts
        post1 = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="First message"
        )
        post2 = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Second message"
        )
        db.session.add_all([post1, post2])
        db.session.commit()

        # Query through relationship
        messages = sample_event.message_posts.all()
        assert len(messages) == 2


class TestPostMessageRoute:
    """Tests for the post_message route."""

    def test_post_message_requires_token(self, client, sample_event):
        """Test that posting a message requires a valid token."""
        response = client.post(
            f"/event/{sample_event.uuid}/message",
            data={"message": "Test message"},
            follow_redirects=False
        )
        # Should redirect to index with error (no token)
        assert response.status_code == 302
        assert "/" in response.location

    def test_post_message_success(self, client, app, sample_event, sample_household, sample_invitation):
        """Test successfully posting a message."""
        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.post(
            f"/event/{sample_event.uuid}/message?token={token}",
            data={"message": "Hello from test!"},
            follow_redirects=False
        )

        # Should redirect back to event page
        assert response.status_code == 302
        assert f"/event/{sample_event.uuid}" in response.location

        # Verify message was created
        messages = MessageWallPost.query.filter_by(event_id=sample_event.id).all()
        assert len(messages) == 1
        assert messages[0].message == "Hello from test!"

    def test_post_message_empty_rejected(self, client, sample_event, sample_household, sample_invitation):
        """Test that empty messages are rejected."""
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.post(
            f"/event/{sample_event.uuid}/message?token={token}",
            data={"message": "   "},  # Whitespace only
            follow_redirects=True
        )

        # Message should not be created
        messages = MessageWallPost.query.filter_by(event_id=sample_event.id).all()
        assert len(messages) == 0

    def test_post_message_too_long_rejected(self, client, sample_event, sample_household, sample_invitation):
        """Test that messages over 2000 characters are rejected."""
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        long_message = "x" * 2001

        response = client.post(
            f"/event/{sample_event.uuid}/message?token={token}",
            data={"message": long_message},
            follow_redirects=True
        )

        # Message should not be created
        messages = MessageWallPost.query.filter_by(event_id=sample_event.id).all()
        assert len(messages) == 0

    def test_post_message_organizer_flag_set(self, client, app, sample_event, sample_person, sample_household, sample_invitation):
        """Test that organizer posts get the is_organizer_post flag set."""
        # Make sample_person an admin of the event
        admin = EventAdmin(
            event_id=sample_event.id,
            person_id=sample_person.id,
            role="organizer"
        )
        db.session.add(admin)
        db.session.commit()

        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.post(
            f"/event/{sample_event.uuid}/message?token={token}",
            data={"message": "Announcement from organizer"},
            follow_redirects=False
        )

        # Verify message was created with organizer flag
        messages = MessageWallPost.query.filter_by(event_id=sample_event.id).all()
        assert len(messages) == 1
        assert messages[0].is_organizer_post is True

    def test_post_message_non_organizer_no_flag(self, client, app, sample_event):
        """Test that non-organizer posts don't have the is_organizer_post flag."""
        # Create a separate guest person and household (not the event creator)
        guest_person = Person(
            first_name="Guest",
            last_name="User",
            email="guest@example.com",
            role="adult"
        )
        db.session.add(guest_person)
        db.session.commit()

        guest_household = Household(name="Guest Household")
        db.session.add(guest_household)
        db.session.commit()

        membership = HouseholdMembership(
            person=guest_person,
            household=guest_household,
            role="adult"
        )
        db.session.add(membership)
        db.session.commit()

        # Create invitation for guest household
        invitation = EventInvitation(
            event_id=sample_event.id,
            household_id=guest_household.id
        )
        db.session.add(invitation)
        db.session.commit()

        # Generate token
        invitation.generate_token()
        db.session.commit()
        token = invitation.invitation_token

        response = client.post(
            f"/event/{sample_event.uuid}/message?token={token}",
            data={"message": "Regular guest message"},
            follow_redirects=False
        )

        # Verify message was created without organizer flag
        messages = MessageWallPost.query.filter_by(event_id=sample_event.id).all()
        assert len(messages) == 1
        assert messages[0].is_organizer_post is False
        assert messages[0].person_id == guest_person.id


class TestEventDetailMessageWall:
    """Tests for message wall display on event detail page."""

    def test_event_detail_shows_messages(self, client, app, sample_event, sample_person, sample_household, sample_invitation):
        """Test that event detail page shows existing messages."""
        # Create a message
        post = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Hello from the party!",
            is_organizer_post=False
        )
        db.session.add(post)

        # Publish the event so it's accessible
        sample_event.status = "published"
        db.session.commit()

        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.get(f"/event/{sample_event.uuid}?token={token}")

        assert response.status_code == 200
        assert b"Hello from the party!" in response.data
        assert b"Message Wall" in response.data

    def test_event_detail_shows_posting_form_for_authenticated(self, client, app, sample_event, sample_household, sample_invitation):
        """Test that authenticated users see the message posting form."""
        # Publish the event
        sample_event.status = "published"
        db.session.commit()

        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.get(f"/event/{sample_event.uuid}?token={token}")

        assert response.status_code == 200
        # Check for the posting form elements
        assert b"Posting as" in response.data
        assert b"Post Message" in response.data
        assert b'name="message"' in response.data

    def test_event_detail_shows_empty_state(self, client, app, sample_event, sample_household, sample_invitation):
        """Test that authenticated users see empty state when no messages."""
        # Publish the event
        sample_event.status = "published"
        db.session.commit()

        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.get(f"/event/{sample_event.uuid}?token={token}")

        assert response.status_code == 200
        # Check for empty state message
        assert b"No messages yet" in response.data
        assert b"Be the first to share a message" in response.data

    def test_event_detail_shows_organizer_badge(self, client, app, sample_event, sample_person, sample_household, sample_invitation):
        """Test that organizer posts display with the Organizer badge."""
        # Create an organizer message
        post = MessageWallPost(
            event_id=sample_event.id,
            person_id=sample_person.id,
            message="Important organizer announcement",
            is_organizer_post=True
        )
        db.session.add(post)

        # Publish the event
        sample_event.status = "published"
        db.session.commit()

        # Generate token
        sample_invitation.generate_token()
        db.session.commit()
        token = sample_invitation.invitation_token

        response = client.get(f"/event/{sample_event.uuid}?token={token}")

        assert response.status_code == 200
        assert b"Important organizer announcement" in response.data
        # Check for Organizer badge (in the message display)
        assert b"Organizer" in response.data

