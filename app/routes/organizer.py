"""Organizer routes - for event creators and admins."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models import Event, Person, Household, EventAdmin, EventInvitation, RSVP
from app.utils.decorators import login_required, event_admin_required
from app.forms.event_forms import EventForm
from app.services.event_service import EventService
from app.services.invitation_service import InvitationService
from app.services.rsvp_service import RSVPService

bp = Blueprint("organizer", __name__, url_prefix="/organizer")


@bp.route("/")
@login_required
def dashboard():
    """Organizer dashboard - list all events."""
    # Get current user from session
    person_id = session.get("person_id")
    person = Person.query.get_or_404(person_id)

    # Get events where person is an admin (hosting)
    admin_records = EventAdmin.query.filter_by(
        person_id=person_id, removed_at=None
    ).all()
    hosting_events = [admin.event for admin in admin_records]

    # Get events where person's household is invited (as guest)
    invited_events_data = []

    # Get person's primary household
    household = person.primary_household

    if household:
        # Get all invitations for this household
        invitations = EventInvitation.query.filter_by(household_id=household.id).all()

        # Filter to only published events and exclude events where person is admin
        hosting_event_ids = {event.id for event in hosting_events}

        for invitation in invitations:
            event = invitation.event

            # Only show published events that the person is not hosting
            if event.is_published and event.id not in hosting_event_ids:
                # Get RSVPs for this household and event
                rsvps = RSVP.query.filter_by(
                    event_id=event.id,
                    household_id=household.id
                ).all()

                # Calculate RSVP summary
                summary = {
                    'attending': sum(1 for r in rsvps if r.status == 'attending'),
                    'not_attending': sum(1 for r in rsvps if r.status == 'not_attending'),
                    'maybe': sum(1 for r in rsvps if r.status == 'maybe'),
                    'no_response': sum(1 for r in rsvps if r.status == 'no_response'),
                }

                invited_events_data.append({
                    'event': event,
                    'invitation': invitation,
                    'rsvps': rsvps,
                    'summary': summary
                })

        # Sort by event date (upcoming first)
        invited_events_data.sort(key=lambda x: x['event'].event_date)

    return render_template(
        "organizer/dashboard.html",
        person=person,
        events=hosting_events,
        invited_events=invited_events_data,
        household=household
    )


@bp.route("/event/new", methods=["GET", "POST"])
@login_required
def create_event():
    """Create a new event."""
    form = EventForm()
    person_id = session.get("person_id")
    person = Person.query.get_or_404(person_id)

    if form.validate_on_submit():
        try:
            # Create event using EventService
            event = EventService.create_event(
                title=form.title.data,
                description=form.description.data,
                event_date=form.event_date.data,
                venue_address=form.venue_address.data,
                venue_map_url=form.venue_map_url.data,
                rsvp_deadline=form.rsvp_deadline.data,
                created_by_person_id=person.id,
                status=form.status.data
            )

            flash(f"Event '{event.title}' created successfully!", "success")
            return redirect(url_for("organizer.event_dashboard", event_uuid=event.uuid))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating event: {str(e)}", "error")

    # Set default status to draft for new events
    if not form.status.data:
        form.status.data = 'draft'

    return render_template("organizer/create_event.html", form=form)


@bp.route("/event/<uuid:event_uuid>")
@login_required
@event_admin_required
def event_dashboard(event_uuid):
    """Event management dashboard."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Get invited households
    invitations = event.invitations.all()

    # Ensure all household members have RSVP records
    # This handles the case where new members are added to a household after initial invitation
    for invitation in invitations:
        RSVPService.create_rsvps_for_household(event, invitation.household)

    # Get RSVP statistics (after ensuring all RSVPs exist)
    rsvp_stats = event.get_rsvp_stats()

    # Get invitation statistics
    invitation_stats = InvitationService.get_invitation_stats(event)

    return render_template(
        "organizer/event_dashboard.html",
        event=event,
        rsvp_stats=rsvp_stats,
        invitations=invitations,
        invitation_stats=invitation_stats,
    )


@bp.route("/event/<uuid:event_uuid>/edit", methods=["GET", "POST"])
@login_required
@event_admin_required
def edit_event(event_uuid):
    """Edit event details."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    form = EventForm(obj=event)

    if form.validate_on_submit():
        try:
            # Update event using EventService
            EventService.update_event(
                event=event,
                title=form.title.data,
                description=form.description.data,
                event_date=form.event_date.data,
                venue_address=form.venue_address.data,
                venue_map_url=form.venue_map_url.data,
                rsvp_deadline=form.rsvp_deadline.data,
                status=form.status.data
            )

            flash(f"Event '{event.title}' updated successfully!", "success")
            return redirect(url_for("organizer.event_dashboard", event_uuid=event_uuid))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating event: {str(e)}", "error")

    return render_template("organizer/edit_event.html", event=event, form=form)


@bp.route("/event/<uuid:event_uuid>/guests")
@login_required
@event_admin_required
def manage_guests(event_uuid):
    """Manage event guests and households."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    invitations = event.invitations.all()

    return render_template(
        "organizer/manage_guests.html", event=event, invitations=invitations
    )


@bp.route("/event/<uuid:event_uuid>/guests/browse")
@login_required
@event_admin_required
def browse_households(event_uuid):
    """Browse available households to invite to event."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Get search query from request args
    search_query = request.args.get("search", "").strip()

    # Get all households
    households_query = Household.query.order_by(Household.name)

    # Apply search filter if provided
    if search_query:
        households_query = households_query.filter(
            Household.name.ilike(f"%{search_query}%")
        )

    households = households_query.all()

    # Get set of already invited household IDs for this event
    invited_household_ids = {inv.household_id for inv in event.invitations.all()}

    # Prepare household data with invitation status
    household_data = []
    for household in households:
        household_data.append({
            "household": household,
            "is_invited": household.id in invited_household_ids,
            "member_count": len(household.active_members),
            "contacts": household.contacts_with_email,
            "has_email": len(household.contacts_with_email) > 0
        })

    return render_template(
        "organizer/browse_households.html",
        event=event,
        household_data=household_data,
        search_query=search_query,
        invited_count=len(invited_household_ids),
        total_count=len(households)
    )


@bp.route("/event/<uuid:event_uuid>/guests/invite", methods=["POST"])
@login_required
@event_admin_required
def invite_households(event_uuid):
    """Invite selected households to event."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Get household IDs from form
    household_ids = request.form.getlist("household_ids")

    if not household_ids:
        flash("Please select at least one household to invite", "warning")
        return redirect(url_for("organizer.browse_households", event_uuid=event_uuid))

    # Convert to integers
    try:
        household_ids = [int(hid) for hid in household_ids]
    except ValueError:
        flash("Invalid household selection", "error")
        return redirect(url_for("organizer.browse_households", event_uuid=event_uuid))

    # Create invitations using service
    try:
        # Track which households were already invited
        existing_invitations = EventInvitation.query.filter(
            EventInvitation.event_id == event.id,
            EventInvitation.household_id.in_(household_ids)
        ).all()
        already_invited_ids = {inv.household_id for inv in existing_invitations}

        # Create invitations
        invitations = InvitationService.create_invitations_bulk(event, household_ids)

        # Count new invitations
        new_count = len(household_ids) - len(already_invited_ids)
        already_invited_count = len(already_invited_ids)

        if new_count > 0:
            flash(f"Successfully invited {new_count} household(s)!", "success")
        if already_invited_count > 0:
            flash(f"{already_invited_count} household(s) were already invited", "info")

    except Exception as e:
        db.session.rollback()
        flash(f"Error inviting households: {str(e)}", "error")

    return redirect(url_for("organizer.manage_guests", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/guests/<int:household_id>/remove", methods=["POST"])
@login_required
@event_admin_required
def remove_invitation(event_uuid, household_id):
    """Remove a household invitation from event."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Find the invitation
    invitation = EventInvitation.query.filter_by(
        event_id=event.id, household_id=household_id
    ).first()

    if not invitation:
        flash("Invitation not found", "error")
        return redirect(url_for("organizer.manage_guests", event_uuid=event_uuid))

    try:
        household_name = invitation.household.name

        # Delete associated RSVPs
        from app.models import RSVP
        RSVP.query.filter_by(
            event_id=event.id, household_id=household_id
        ).delete()

        # Delete invitation
        db.session.delete(invitation)
        db.session.commit()

        flash(f"Removed {household_name} from guest list", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error removing invitation: {str(e)}", "error")

    return redirect(url_for("organizer.manage_guests", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/invitations/send", methods=["POST"])
@login_required
@event_admin_required
def send_invitations(event_uuid):
    """Send invitations to all invited households."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Get invitation stats
    stats = InvitationService.get_invitation_stats(event)

    if stats["total"] == 0:
        flash("No households have been invited yet. Please add guests first.", "warning")
        return redirect(url_for("organizer.manage_guests", event_uuid=event_uuid))

    # Determine which invitations to send based on form parameter
    send_type = request.form.get("send_type", "pending")  # "pending" or "all"

    # Check if there are any pending invitations to send (only for "pending" mode)
    if send_type == "pending" and stats["pending"] == 0:
        flash("All invitations have already been sent!", "info")
        return redirect(url_for("organizer.event_dashboard", event_uuid=event_uuid))

    try:
        if send_type == "all":
            # Resend to all households
            result = InvitationService.send_invitations_bulk(event)
            action = "sent/resent"
        else:
            # Send only to pending (not yet sent)
            result = InvitationService.send_pending_invitations(event)
            action = "sent"

        success_count = result["success"]
        failure_count = result["failure"]

        if success_count > 0:
            flash(f"Successfully {action} {success_count} invitation(s)!", "success")

        if failure_count > 0:
            flash(
                f"{failure_count} invitation(s) could not be sent (households may not have email addresses).",
                "warning"
            )

        if success_count == 0 and failure_count == 0:
            flash("No invitations were sent. All households may lack email addresses.", "warning")

    except Exception as e:
        flash(f"Error sending invitations: {str(e)}", "error")

    return redirect(url_for("organizer.event_dashboard", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/invitations/<int:invitation_id>/resend", methods=["POST"])
@login_required
@event_admin_required
def resend_invitation(event_uuid, invitation_id):
    """Resend invitation to a specific household."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Get the invitation
    invitation = EventInvitation.query.filter_by(
        id=invitation_id,
        event_id=event.id
    ).first_or_404()

    try:
        if InvitationService.resend_invitation(invitation):
            flash(f"Invitation resent to {invitation.household.name}!", "success")
        else:
            flash(
                f"Could not send invitation to {invitation.household.name}. "
                "The household may not have any email addresses.",
                "warning"
            )
    except Exception as e:
        flash(f"Error resending invitation: {str(e)}", "error")

    return redirect(url_for("organizer.manage_guests", event_uuid=event_uuid))


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Organizer login (password or magic link)."""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email:
            flash("Email is required", "error")
            return redirect(url_for("organizer.login"))

        # Find person by email
        person = Person.query.filter_by(email=email).first()

        if not person:
            flash("No account found with that email address", "error")
            return redirect(url_for("organizer.login"))

        # Check if password was provided (password login)
        if password:
            if person.check_password(password):
                # Successful password login
                session.permanent = True  # Make session persistent across restarts
                session["person_id"] = person.id
                flash(f"Welcome back, {person.first_name}!", "success")
                return redirect(url_for("organizer.dashboard"))
            else:
                flash("Incorrect password", "error")
                return redirect(url_for("organizer.login"))
        else:
            # Magic link login
            from app.services.auth_service import AuthService
            from app.services.notification_service import NotificationService

            # Create magic link token
            token = AuthService.create_magic_link_token(person)

            if not token:
                flash(
                    "Too many login attempts. Please try again later or use password login.",
                    "error"
                )
                return redirect(url_for("organizer.login"))

            # Send magic link email
            if NotificationService.send_magic_link_email(person, token):
                flash(
                    f"A login link has been sent to {person.email}. Please check your email.",
                    "success"
                )
            else:
                flash(
                    "Unable to send login link. Please try password login or contact support.",
                    "error"
                )

            return redirect(url_for("organizer.login"))

    return render_template("organizer/login.html")


@bp.route("/logout")
def logout():
    """Logout organizer."""
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for("public.index"))


@bp.route("/verify-magic-link/<token>")
def verify_magic_link(token):
    """Verify magic link token and log user in."""
    from app.services.auth_service import AuthService

    person = AuthService.verify_magic_link_token(token)

    if person:
        # Successful magic link login
        session.permanent = True
        session["person_id"] = person.id
        flash(f"Welcome back, {person.first_name}!", "success")
        return redirect(url_for("organizer.dashboard"))
    else:
        flash("Invalid or expired login link. Please request a new one.", "error")
        return redirect(url_for("organizer.login"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Request password reset email."""
    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Email is required", "error")
            return redirect(url_for("organizer.forgot_password"))

        # Find person by email
        person = Person.query.filter_by(email=email).first()

        # Always show success message (security best practice - don't reveal if email exists)
        flash(
            "If an account exists with that email, you will receive a password reset link shortly.",
            "success"
        )

        # Only send email if person exists
        if person:
            from app.services.auth_service import AuthService
            from app.services.notification_service import NotificationService

            # Create password reset token
            token = AuthService.create_password_reset_token(person)

            # Send password reset email (only if not rate limited)
            if token:
                NotificationService.send_password_reset_email(person, token)

        return redirect(url_for("organizer.login"))

    return render_template("organizer/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password with token."""
    from app.services.auth_service import AuthService

    # Verify token
    auth_token = AuthService.verify_password_reset_token(token)

    if not auth_token:
        flash("Invalid or expired password reset link. Please request a new one.", "error")
        return redirect(url_for("organizer.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not password or not confirm_password:
            flash("Both password fields are required", "error")
            return redirect(url_for("organizer.reset_password", token=token))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("organizer.reset_password", token=token))

        if len(password) < 8:
            flash("Password must be at least 8 characters long", "error")
            return redirect(url_for("organizer.reset_password", token=token))

        # Update password
        person = auth_token.person
        person.set_password(password)
        db.session.commit()

        # Mark token as used
        AuthService.use_password_reset_token(auth_token)

        flash("Your password has been reset successfully. You can now log in.", "success")
        return redirect(url_for("organizer.login"))

    return render_template("organizer/reset_password.html", token=token)


@bp.route("/dev/switch-user/<int:person_id>", methods=["POST"])
def dev_switch_user(person_id):
    """Switch to a different user (development only)."""
    from flask import current_app

    # Only allow in development mode (not production or testing)
    is_dev = not current_app.config.get("TESTING") and current_app.config.get("ENV") != "production"
    if not is_dev:
        flash("User switching is only available in development mode", "error")
        return redirect(url_for("organizer.dashboard"))

    # Find the person
    person = Person.query.get(person_id)
    if not person:
        flash("User not found", "error")
        return redirect(url_for("organizer.dashboard"))

    # Check if person has a password (is an organizer)
    if not person.password_hash:
        flash("Cannot switch to a user without login credentials", "error")
        return redirect(url_for("organizer.dashboard"))

    # Get the current URL to redirect back to
    next_url = request.form.get("next") or request.referrer or url_for("organizer.dashboard")

    # Switch the session to the new user
    session["person_id"] = person.id
    session.permanent = True

    flash(f"Switched to {person.full_name}", "success")
    return redirect(next_url)

