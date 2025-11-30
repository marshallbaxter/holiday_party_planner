"""Public routes - for guests and event viewing."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models import Event, EventInvitation, RSVP, PotluckItem, MessageWallPost, Person, EventAdmin
from app.utils.decorators import valid_rsvp_token_required
from app.services.rsvp_service import RSVPService
from app.services.potluck_service import PotluckService
from app.forms.potluck_forms import PotluckItemForm
from collections import defaultdict
import json

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    """Homepage."""
    return render_template("public/index.html")


@bp.route("/guest/dashboard")
@valid_rsvp_token_required
def guest_dashboard():
    """Guest dashboard showing all invitations for a household."""
    household = request.household  # Set by decorator

    # Get all invitations for this household
    invitations = EventInvitation.query.filter_by(household_id=household.id).all()

    # Filter to only show published events
    invitations = [inv for inv in invitations if inv.event.is_published]

    # Sort by event date (upcoming first)
    invitations.sort(key=lambda inv: inv.event.event_date)

    # Get RSVPs for each invitation
    invitation_rsvps = {}
    rsvp_summaries = {}

    for invitation in invitations:
        # Get RSVPs for this event and household
        rsvps = RSVP.query.filter_by(
            event_id=invitation.event_id,
            household_id=household.id
        ).all()

        invitation_rsvps[invitation.id] = rsvps

        # Calculate summary
        summary = {
            'attending': sum(1 for r in rsvps if r.status == 'attending'),
            'not_attending': sum(1 for r in rsvps if r.status == 'not_attending'),
            'maybe': sum(1 for r in rsvps if r.status == 'maybe'),
            'no_response': sum(1 for r in rsvps if r.status == 'no_response'),
        }
        rsvp_summaries[invitation.id] = summary

    return render_template(
        "public/guest_dashboard.html",
        household=household,
        invitations=invitations,
        invitation_rsvps=invitation_rsvps,
        rsvp_summaries=rsvp_summaries,
    )


@bp.route("/event/<uuid:event_uuid>")
def event_detail(event_uuid):
    """Public event detail page (read-only)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Only show published or archived events
    if event.status == "draft":
        flash("This event is not yet published", "warning")
        return redirect(url_for("public.index"))

    # Get RSVP statistics
    rsvp_stats = event.get_rsvp_stats()

    # Get dietary restrictions for attending guests
    dietary_restrictions = event.get_dietary_restrictions()

    # Get potluck items
    potluck_items = event.potluck_items.all()

    # Get message wall posts
    message_posts = event.message_posts.order_by(
        MessageWallPost.posted_at.desc()
    ).all()

    # Check for user authentication and RSVP status
    user_rsvp_data = None
    household = None
    invitation = None
    rsvps = []
    rsvp_summary = None
    rsvp_token = None

    # Method 1: Check if user is logged in (organizer)
    person_id = session.get("person_id")
    if person_id:
        from app.models import Person
        person = Person.query.get(person_id)
        if person:
            household = person.primary_household
            if household:
                # Check if household is invited to this event
                invitation = EventInvitation.query.filter_by(
                    event_id=event.id,
                    household_id=household.id
                ).first()

                if invitation:
                    # Get or generate token for RSVP link
                    if not invitation.invitation_token:
                        invitation.generate_token()
                        db.session.commit()
                    rsvp_token = invitation.invitation_token

                    # Get RSVPs for this household
                    rsvps = RSVP.query.filter_by(
                        event_id=event.id,
                        household_id=household.id
                    ).all()

                    # Calculate summary
                    rsvp_summary = {
                        'attending': sum(1 for r in rsvps if r.status == 'attending'),
                        'not_attending': sum(1 for r in rsvps if r.status == 'not_attending'),
                        'maybe': sum(1 for r in rsvps if r.status == 'maybe'),
                        'no_response': sum(1 for r in rsvps if r.status == 'no_response'),
                    }

    # Method 2: Check if accessing via RSVP token (guest)
    if not household:
        token = request.args.get("token")
        if token:
            # Verify token
            token_data = EventInvitation.verify_token(token)
            if token_data and token_data.get("event_id") == event.id:
                # Get invitation
                invitation = EventInvitation.query.filter_by(
                    event_id=token_data["event_id"],
                    household_id=token_data["household_id"]
                ).first()

                if invitation:
                    household = invitation.household
                    rsvp_token = token

                    # Get RSVPs for this household
                    rsvps = RSVP.query.filter_by(
                        event_id=event.id,
                        household_id=household.id
                    ).all()

                    # Calculate summary
                    rsvp_summary = {
                        'attending': sum(1 for r in rsvps if r.status == 'attending'),
                        'not_attending': sum(1 for r in rsvps if r.status == 'not_attending'),
                        'maybe': sum(1 for r in rsvps if r.status == 'maybe'),
                        'no_response': sum(1 for r in rsvps if r.status == 'no_response'),
                    }

    # Prepare user RSVP data if authenticated and invited
    if household and invitation:
        # Check for missing contact info in household members
        members_missing_email = []
        members_missing_phone = []
        for rsvp in rsvps:
            person = rsvp.person
            if not person.email:
                members_missing_email.append(person)
            if not person.phone:
                members_missing_phone.append(person)

        user_rsvp_data = {
            'household': household,
            'invitation': invitation,
            'rsvps': rsvps,
            'summary': rsvp_summary,
            'token': rsvp_token,
            'members_missing_email': members_missing_email,
            'members_missing_phone': members_missing_phone,
        }

    # Get current person ID for template
    current_person_id = session.get("person_id")

    return render_template(
        "public/event_detail.html",
        event=event,
        rsvp_stats=rsvp_stats,
        dietary_restrictions=dietary_restrictions,
        potluck_items=potluck_items,
        message_posts=message_posts,
        user_rsvp_data=user_rsvp_data,
        current_person_id=current_person_id,
    )


@bp.route("/event/<uuid:event_uuid>/rsvp")
@valid_rsvp_token_required
def rsvp_form(event_uuid):
    """RSVP form for a household (requires valid token)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator

    # Get existing RSVPs for this household
    rsvps = event.rsvps.filter_by(household_id=household.id).all()

    # Create RSVP records for household members if they don't exist
    for member in household.active_members:
        existing_rsvp = next((r for r in rsvps if r.person_id == member.id), None)
        if not existing_rsvp:
            new_rsvp = RSVP(
                event_id=event.id,
                person_id=member.id,
                household_id=household.id,
                status="no_response",
            )
            db.session.add(new_rsvp)
            rsvps.append(new_rsvp)

    db.session.commit()

    # Get the token from the request for the form action URLs
    token = request.args.get("token")

    return render_template(
        "public/rsvp_form.html",
        event=event,
        household=household,
        rsvps=rsvps,
        token=token,
    )


@bp.route("/event/<uuid:event_uuid>/rsvp/submit", methods=["POST"])
@valid_rsvp_token_required
def submit_rsvp(event_uuid):
    """Submit RSVP responses."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator

    try:
        # Parse form data for all household members
        rsvp_data = {}

        # Get all active household members to validate person_ids
        valid_person_ids = {member.id for member in household.active_members}

        # Extract RSVP status and notes for each person
        for key, value in request.form.items():
            if key.startswith("rsvp_"):
                # Extract person_id from field name (e.g., "rsvp_123" -> 123)
                try:
                    person_id = int(key.split("_")[1])
                except (IndexError, ValueError):
                    continue

                # Security check: Ensure person_id belongs to this household
                if person_id not in valid_person_ids:
                    flash(f"Invalid person ID in form submission.", "error")
                    return redirect(
                        url_for(
                            "public.rsvp_form",
                            event_uuid=event_uuid,
                            token=request.args.get("token"),
                        )
                    )

                # Get status value
                status = value.strip()

                # Validate status
                valid_statuses = ["attending", "not_attending", "maybe", "no_response"]
                if status not in valid_statuses:
                    flash(f"Invalid RSVP status: {status}", "error")
                    return redirect(
                        url_for(
                            "public.rsvp_form",
                            event_uuid=event_uuid,
                            token=request.args.get("token"),
                        )
                    )

                # Get optional notes for this person
                notes_key = f"notes_{person_id}"
                notes = request.form.get(notes_key, "").strip() or None

                # Get optional contact info for this person (if they're missing it)
                email_key = f"email_{person_id}"
                email = request.form.get(email_key, "").strip() or None

                phone_key = f"phone_{person_id}"
                phone = request.form.get(phone_key, "").strip() or None

                # Add to rsvp_data dictionary
                rsvp_data[person_id] = {
                    "status": status,
                    "notes": notes,
                    "email": email,
                    "phone": phone
                }

        # Update contact info for household members who are missing it
        # This must be committed BEFORE processing RSVPs so confirmation emails can be sent
        contact_updated = False
        for person_id, data in rsvp_data.items():
            person = Person.query.get(person_id)
            if person:
                if data.get("email") and not person.email:
                    person.email = data["email"]
                    contact_updated = True
                if data.get("phone") and not person.phone:
                    person.phone = data["phone"]
                    contact_updated = True

        if contact_updated:
            db.session.commit()

        # Check if we have any RSVP data to process
        if not rsvp_data:
            flash("No RSVP responses were submitted. Please select a response for at least one person.", "warning")
            return redirect(
                url_for(
                    "public.rsvp_form",
                    event_uuid=event_uuid,
                    token=request.args.get("token"),
                )
            )

        # Update RSVPs using the service layer
        updated_rsvps = RSVPService.update_household_rsvps(event, household, rsvp_data)

        # Success message
        if updated_rsvps:
            flash(f"Thank you! Your RSVP has been recorded for {len(updated_rsvps)} person(s).", "success")
        else:
            flash("No RSVPs were updated. Please try again.", "warning")

        # Redirect to event detail page on success
        return redirect(
            url_for(
                "public.event_detail",
                event_uuid=event_uuid,
                token=request.args.get("token"),
            )
        )

    except Exception as e:
        # Log the error and show user-friendly message
        db.session.rollback()
        flash(f"An error occurred while submitting your RSVP. Please try again or contact the organizer.", "error")
        # In production, you'd want to log this error: app.logger.error(f"RSVP submission error: {e}")

        # Redirect back to RSVP form on error so user can try again
        return redirect(
            url_for(
                "public.rsvp_form",
                event_uuid=event_uuid,
                token=request.args.get("token"),
            )
        )


@bp.route("/event/<uuid:event_uuid>/update-contact", methods=["POST"])
@valid_rsvp_token_required
def update_contact_info(event_uuid):
    """Update contact information for a household member."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator

    try:
        person_id = request.form.get("person_id")
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None

        if not person_id:
            flash("Invalid request: missing person ID.", "error")
            return redirect(
                url_for(
                    "public.rsvp_form",
                    event_uuid=event_uuid,
                    token=request.args.get("token"),
                )
            )

        # Validate person belongs to household
        person_id = int(person_id)
        valid_person_ids = {member.id for member in household.active_members}
        if person_id not in valid_person_ids:
            flash("You can only update contact info for members of your household.", "error")
            return redirect(
                url_for(
                    "public.rsvp_form",
                    event_uuid=event_uuid,
                    token=request.args.get("token"),
                )
            )

        # Get the person and update their contact info
        person = Person.query.get(person_id)
        if person:
            updated_fields = []
            if email and not person.email:
                person.email = email
                updated_fields.append("email")
            if phone and not person.phone:
                person.phone = phone
                updated_fields.append("phone")

            if updated_fields:
                db.session.commit()
                flash(f"Contact information updated for {person.first_name}.", "success")
            else:
                flash("No changes were made.", "info")

    except ValueError:
        flash("Invalid person ID.", "error")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating contact information.", "error")

    return redirect(
        url_for(
            "public.rsvp_form",
            event_uuid=event_uuid,
            token=request.args.get("token"),
        )
    )


@bp.route("/event/<uuid:event_uuid>/potluck/add", methods=["GET", "POST"])
def add_potluck_item(event_uuid):
    """Add a potluck item (guest or organizer)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Check authentication - either logged in or has valid token
    person = None
    token = request.args.get("token")

    # Method 1: Logged in user
    person_id = session.get("person_id")
    if person_id:
        person = Person.query.get(person_id)

    # Method 2: Token-based guest
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household:
                # Get a person from the household to associate the item
                # Note: active_members returns Person objects, not HouseholdMembership objects
                # Prefer adults with email
                person = next((m for m in invitation.household.active_members
                              if m.email and not m.is_child), None)
                if not person:
                    # Fall back to any active member
                    person = next((m for m in invitation.household.active_members), None)

    if not person:
        flash("Please log in or use your invitation link to add items", "warning")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Get household members for contributor selection
    household = person.primary_household
    household_members = household.active_members if household else []

    form = PotluckItemForm()

    if form.validate_on_submit():
        try:
            # Parse dietary tags from JSON string
            dietary_tags = []
            if form.dietary_tags.data:
                try:
                    dietary_tags = json.loads(form.dietary_tags.data)
                except (json.JSONDecodeError, TypeError):
                    dietary_tags = []

            # Parse contributor IDs from JSON string or list
            contributor_ids = []
            if form.contributor_ids.data:
                # Check if it's already a list (Flask may have parsed it)
                if isinstance(form.contributor_ids.data, list):
                    contributor_ids = form.contributor_ids.data
                else:
                    # Try to parse as JSON string
                    try:
                        contributor_ids = json.loads(form.contributor_ids.data)
                    except (json.JSONDecodeError, TypeError) as e:
                        contributor_ids = []

            # If no contributors specified, default to the current person
            if not contributor_ids:
                contributor_ids = [person.id]

            # Create potluck item
            item = PotluckService.create_item(
                event=event,
                name=form.name.data,
                category=form.category.data,
                dietary_tags=dietary_tags,
                notes=form.notes.data,
                quantity_needed=1,
                created_by_person_id=person.id,
                contributor_ids=contributor_ids
            )

            flash(f"Added '{item.name}' to the potluck!", "success")

            # Redirect back with token if present
            if token:
                return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
            else:
                return redirect(url_for("public.event_detail", event_uuid=event_uuid))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding item: {str(e)}", "error")

    # Pre-populate contributor with current person for new items
    if request.method == 'GET':
        form.contributor_ids.data = json.dumps([person.id])

    return render_template(
        "public/potluck_form.html",
        event=event,
        form=form,
        person=person,
        household_members=household_members,
        token=token,
        action="add"
    )


@bp.route("/event/<uuid:event_uuid>/potluck/<int:item_id>/edit", methods=["GET", "POST"])
def edit_potluck_item(event_uuid, item_id):
    """Edit a potluck item (owner or organizer only)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    item = PotluckItem.query.get_or_404(item_id)

    # Verify item belongs to this event
    if item.event_id != event.id:
        flash("Item not found", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authentication and authorization
    person = None
    token = request.args.get("token")
    is_organizer = False

    # Method 1: Logged in user
    person_id = session.get("person_id")
    if person_id:
        person = Person.query.get(person_id)
        # Check if organizer
        is_organizer = EventAdmin.query.filter_by(
            event_id=event.id,
            person_id=person.id,
            removed_at=None
        ).first() is not None

    # Method 2: Token-based guest
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household:
                # Find the person who created the item in this household
                person = Person.query.get(item.created_by_person_id)

    if not person:
        flash("Please log in or use your invitation link", "warning")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authorization: must be item creator, contributor, or organizer
    if not is_organizer and not item.is_contributor(person.id):
        flash("You can only edit items you're contributing to", "error")
        if token:
            return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
        else:
            return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Get household members for contributor selection
    household = person.primary_household
    household_members = household.active_members if household else []

    form = PotluckItemForm()

    if form.validate_on_submit():
        try:
            # Parse dietary tags from JSON string
            dietary_tags = []
            if form.dietary_tags.data:
                try:
                    dietary_tags = json.loads(form.dietary_tags.data)
                except (json.JSONDecodeError, TypeError):
                    dietary_tags = []

            # Parse contributor IDs from JSON string or list
            contributor_ids = []
            if form.contributor_ids.data:
                # Check if it's already a list (Flask may have parsed it)
                if isinstance(form.contributor_ids.data, list):
                    contributor_ids = form.contributor_ids.data
                else:
                    # Try to parse as JSON string
                    try:
                        contributor_ids = json.loads(form.contributor_ids.data)
                    except (json.JSONDecodeError, TypeError) as e:
                        contributor_ids = []

            # Update potluck item
            # Note: Always pass contributor_ids, even if empty list, to allow clearing contributors
            updated_item = PotluckService.update_item(
                item=item,
                name=form.name.data,
                category=form.category.data,
                dietary_tags=dietary_tags,
                notes=form.notes.data,
                contributor_ids=contributor_ids
            )

            # Verify the update persisted by refreshing from database
            db.session.expire(updated_item)
            db.session.refresh(updated_item)

            flash(f"Updated '{item.name}'", "success")

            # Redirect back with token if present
            if token:
                return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
            else:
                return redirect(url_for("public.event_detail", event_uuid=event_uuid))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating item: {str(e)}", "error")

    # Pre-populate form fields manually on GET
    if request.method == 'GET':
        form.name.data = item.name
        form.category.data = item.category
        form.notes.data = item.notes
        # Convert dietary_tags list to JSON string for the hidden field
        form.dietary_tags.data = json.dumps(item.dietary_tags if item.dietary_tags else [])
        # Convert contributor_ids list to JSON string for the hidden field
        form.contributor_ids.data = json.dumps(item.contributor_ids)

    return render_template(
        "public/potluck_form.html",
        event=event,
        form=form,
        item=item,
        person=person,
        household_members=household_members,
        token=token,
        action="edit"
    )


@bp.route("/event/<uuid:event_uuid>/potluck/<int:item_id>/delete", methods=["POST"])
def delete_potluck_item(event_uuid, item_id):
    """Delete a potluck item (owner or organizer only)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    item = PotluckItem.query.get_or_404(item_id)

    # Verify item belongs to this event
    if item.event_id != event.id:
        flash("Item not found", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authentication and authorization
    person = None
    token = request.args.get("token")
    is_organizer = False

    # Method 1: Logged in user
    person_id = session.get("person_id")
    if person_id:
        person = Person.query.get(person_id)
        # Check if organizer
        is_organizer = EventAdmin.query.filter_by(
            event_id=event.id,
            person_id=person.id,
            removed_at=None
        ).first() is not None

    # Method 2: Token-based guest
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household:
                # Find the person who created the item in this household
                person = Person.query.get(item.created_by_person_id)

    if not person:
        flash("Please log in or use your invitation link", "warning")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authorization: must be a contributor or organizer
    if not is_organizer and not item.is_contributor(person.id):
        flash("You can only delete items you're contributing to", "error")
        if token:
            return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
        else:
            return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    try:
        item_name = item.name
        PotluckService.delete_item(item)
        flash(f"Removed '{item_name}' from potluck", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", "error")

    # Redirect back with token if present
    if token:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
    else:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/message", methods=["POST"])
@valid_rsvp_token_required
def post_message(event_uuid):
    """Post a message to the event wall."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator

    # TODO: Implement message posting
    flash("Message posting not yet implemented", "info")

    return redirect(url_for("public.event_detail", event_uuid=event_uuid))

