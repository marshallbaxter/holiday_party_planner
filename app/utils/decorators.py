"""Custom decorators for route protection."""
from functools import wraps
from flask import request, redirect, url_for, flash, g, session
from app.models import Person, Event, EventAdmin, EventInvitation


def login_required(f):
    """Decorator to require organizer login."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        person_id = session.get("person_id")
        if not person_id:
            flash("Please log in to access this page", "warning")
            return redirect(url_for("organizer.login"))

        # Load person into g for use in view
        g.current_person = Person.query.get(person_id)
        if not g.current_person:
            session.clear()
            flash("Invalid session. Please log in again", "error")
            return redirect(url_for("organizer.login"))

        return f(*args, **kwargs)

    return decorated_function


def event_admin_required(f):
    """Decorator to require admin access to an event."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get event_uuid from kwargs
        event_uuid = kwargs.get("event_uuid")
        if not event_uuid:
            flash("Event not found", "error")
            return redirect(url_for("organizer.dashboard"))

        # Get event
        event = Event.query.filter_by(uuid=str(event_uuid)).first()
        if not event:
            flash("Event not found", "error")
            return redirect(url_for("organizer.dashboard"))

        # Check if current person is an admin
        person_id = session.get("person_id")
        if not person_id:
            flash("Please log in to access this page", "warning")
            return redirect(url_for("organizer.login"))

        is_admin = (
            EventAdmin.query.filter_by(
                event_id=event.id, person_id=person_id, removed_at=None
            ).first()
            is not None
        )

        if not is_admin:
            flash("You don't have permission to manage this event", "error")
            return redirect(url_for("organizer.dashboard"))

        # Store event in g for use in view
        g.current_event = event

        return f(*args, **kwargs)

    return decorated_function


def valid_rsvp_token_required(f):
    """Decorator to require a valid RSVP token."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from query string
        token = request.args.get("token")
        if not token:
            flash("Invalid or missing invitation link", "error")
            return redirect(url_for("public.index"))

        # Verify token
        token_data = EventInvitation.verify_token(token)
        if not token_data:
            flash("Invalid or expired invitation link", "error")
            return redirect(url_for("public.index"))

        # Get invitation
        invitation = EventInvitation.query.filter_by(
            event_id=token_data["event_id"], household_id=token_data["household_id"]
        ).first()

        if not invitation:
            flash("Invitation not found", "error")
            return redirect(url_for("public.index"))

        # Store household in request for use in view
        request.household = invitation.household
        request.invitation = invitation

        return f(*args, **kwargs)

    return decorated_function

