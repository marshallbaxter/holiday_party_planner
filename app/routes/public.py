"""Public routes - for guests and event viewing."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models import Event, EventInvitation, RSVP, PotluckItem, MessageWallPost, Person, EventAdmin, GuestReferral
from app.utils.decorators import valid_rsvp_token_required
from app.services.rsvp_service import RSVPService
from app.services.potluck_service import PotluckService
from app.services.bring_friend_service import BringFriendService
from app.forms.potluck_forms import PotluckItemForm, ClaimSuggestedItemForm
from collections import defaultdict
import json

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    """Homepage."""
    return render_template("public/index.html")


@bp.route("/r/<short_token>")
def short_rsvp_redirect(short_token):
    """Redirect from short SMS-friendly URL to full event detail page.

    This route is used in SMS invitations to provide a short, SMS-friendly URL
    that redirects to the full event detail page with the proper authentication token.
    This is the household-level short link (legacy).
    """
    invitation = EventInvitation.get_by_short_token(short_token)

    if not invitation:
        flash("Invalid or expired invitation link.", "error")
        return redirect(url_for("public.index"))

    # Ensure the invitation has a full token
    if not invitation.invitation_token:
        invitation.generate_token()
        db.session.commit()

    # Redirect to event detail page with full token
    return redirect(url_for(
        "public.event_detail",
        event_uuid=invitation.event.uuid,
        token=invitation.invitation_token,
    ))


@bp.route("/i/<short_token>")
def person_short_redirect(short_token):
    """Redirect from person-specific short URL to event detail page.

    This route handles person-specific invitation links, which allows:
    - Personalized landing page experience (showing the person's name)
    - Individual RSVP tracking
    - Pre-filling forms with the person's information

    The person_id is stored in the session for personalization.
    """
    from app.models.person_invitation_link import PersonInvitationLink

    link = PersonInvitationLink.get_by_short_token(short_token)

    if not link:
        flash("Invalid or expired invitation link.", "error")
        return redirect(url_for("public.index"))

    invitation = link.invitation
    person = link.person

    # Ensure the invitation has a full token
    if not invitation.invitation_token:
        invitation.generate_token()
        db.session.commit()

    # Store the person_id in session for personalization
    session["invited_person_id"] = person.id

    # Redirect to event detail page with full token
    return redirect(url_for(
        "public.event_detail",
        event_uuid=invitation.event.uuid,
        token=invitation.invitation_token,
    ))


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

    # Get potluck items - separate freeform and suggested
    potluck_items = PotluckService.get_freeform_items(event)
    suggested_items = PotluckService.get_suggested_items(event)
    suggested_items_by_category = PotluckService.get_suggested_items_by_category(event)

    # Get message wall posts (oldest first for conversation flow)
    message_posts = event.message_posts.order_by(
        MessageWallPost.posted_at.asc()
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

    # Method 3: Check if accessing via friend referral token (brought friend)
    friend_referral = None
    friend_person = None
    friend_rsvp = None
    if not household:
        token = request.args.get("token")
        if token:
            # Try to verify as a friend referral token
            token_data = GuestReferral.verify_token(token)
            if token_data and token_data.get("event_id") == event.id:
                friend_referral = GuestReferral.query.get(token_data.get("referral_id"))
                if friend_referral:
                    friend_person = friend_referral.referred
                    friend_rsvp = RSVP.query.filter_by(
                        event_id=event.id,
                        person_id=friend_person.id
                    ).first()
                    rsvp_token = token

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
            'is_brought_friend': False,
        }

    # Build user_rsvp_data for brought friends
    elif friend_referral and friend_person:
        user_rsvp_data = {
            'household': None,
            'invitation': None,
            'rsvps': [friend_rsvp] if friend_rsvp else [],
            'summary': None,
            'token': rsvp_token,
            'members_missing_email': [],
            'members_missing_phone': [],
            'is_brought_friend': True,
            'referral': friend_referral,
            'referrer': friend_referral.referrer,
            'person': friend_person,
            'rsvp': friend_rsvp,
        }

    # Get current person for template (for message posting attribution)
    # Priority: 1) Logged in user, 2) Person-specific invite link, 3) First household member, 4) Brought friend
    current_person = None
    current_person_id = session.get("person_id")
    if current_person_id:
        current_person = Person.query.get(current_person_id)

    # Check if accessed via person-specific invitation link
    if not current_person:
        invited_person_id = session.get("invited_person_id")
        if invited_person_id and household:
            # Verify the person is in this household
            invited_person = Person.query.get(invited_person_id)
            if invited_person and invited_person in household.active_members:
                current_person = invited_person
                current_person_id = invited_person_id

    # Fall back to first household member
    if not current_person and household and household.active_members:
        current_person = household.active_members[0]
        current_person_id = current_person.id

    # Fall back to brought friend person
    if not current_person and friend_person:
        current_person = friend_person
        current_person_id = friend_person.id

    # Check if current person is an event admin (for organizer badge on messages)
    is_event_admin = False
    if current_person:
        is_event_admin = EventAdmin.query.filter_by(
            event_id=event.id,
            person_id=current_person.id,
            removed_at=None
        ).first() is not None

    # Category display names for suggested items
    category_names = {
        "main": "🍖 Main Dishes",
        "side": "🥗 Side Dishes",
        "dessert": "🍰 Desserts",
        "drink": "🥤 Beverages",
        "other": "📦 Other",
    }

    # Get brought friends for this event
    brought_friends = BringFriendService.get_friends_for_event(event)

    # Get all attending guests for the "Who's Coming" section
    # Group by household for regular invitations, separate section for brought friends
    attending_rsvps = RSVP.query.filter_by(
        event_id=event.id,
        status="attending"
    ).all()

    # Organize attending guests by household
    attending_by_household = {}
    attending_friends = []

    for rsvp in attending_rsvps:
        if rsvp.household_id:
            # Regular invitation - group by household
            if rsvp.household_id not in attending_by_household:
                attending_by_household[rsvp.household_id] = {
                    "household": rsvp.household,
                    "members": []
                }
            attending_by_household[rsvp.household_id]["members"].append(rsvp.person)
        else:
            # Brought friend - no household
            # Find who invited them
            referral = GuestReferral.query.filter_by(
                event_id=event.id,
                referred_person_id=rsvp.person_id
            ).first()
            attending_friends.append({
                "person": rsvp.person,
                "referrer": referral.referrer if referral else None
            })

    attending_households = list(attending_by_household.values())

    return render_template(
        "public/event_detail.html",
        event=event,
        rsvp_stats=rsvp_stats,
        dietary_restrictions=dietary_restrictions,
        potluck_items=potluck_items,
        suggested_items=suggested_items,
        suggested_items_by_category=suggested_items_by_category,
        category_names=category_names,
        message_posts=message_posts,
        user_rsvp_data=user_rsvp_data,
        current_person_id=current_person_id,
        current_person=current_person,
        is_event_admin=is_event_admin,
        brought_friends=brought_friends,
        attending_households=attending_households,
        attending_friends=attending_friends,
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
    token = request.args.get("token")

    # Get the message content
    message_text = request.form.get("message", "").strip()

    if not message_text:
        flash("Please enter a message.", "warning")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Limit message length (prevent abuse)
    max_length = 2000
    if len(message_text) > max_length:
        flash(f"Message is too long. Please keep it under {max_length} characters.", "warning")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Determine the posting person
    # Priority: 1) Logged in user, 2) Person-specific invite link, 3) Form-provided person_id
    person = None
    person_id = session.get("person_id")
    if person_id:
        person = Person.query.get(person_id)

    # Check if accessed via person-specific invitation link
    if not person:
        invited_person_id = session.get("invited_person_id")
        if invited_person_id:
            invited_person = Person.query.get(invited_person_id)
            if invited_person and invited_person in household.active_members:
                person = invited_person

    # Fall back to form-provided person_id (validated against household)
    if not person:
        form_person_id = request.form.get("person_id")
        if form_person_id:
            try:
                form_person = Person.query.get(int(form_person_id))
                if form_person and form_person in household.active_members:
                    person = form_person
            except (ValueError, TypeError):
                pass

    # Last resort: first household member
    if not person and household.active_members:
        person = household.active_members[0]

    if not person:
        flash("Unable to determine who is posting. Please try again.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Check if the person is an event admin (for organizer badge)
    is_organizer = EventAdmin.query.filter_by(
        event_id=event.id,
        person_id=person.id,
        removed_at=None
    ).first() is not None

    # Create the message post
    try:
        message_post = MessageWallPost(
            event_id=event.id,
            person_id=person.id,
            message=message_text,
            is_organizer_post=is_organizer
        )
        db.session.add(message_post)
        db.session.commit()
        flash("Your message has been posted!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while posting your message. Please try again.", "error")

    return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))


# ==================== Suggested Potluck Item Claim Routes ====================


@bp.route("/event/<uuid:event_uuid>/potluck/suggested/<int:item_id>/claim", methods=["POST"])
def claim_suggested_item(event_uuid, item_id):
    """Claim a suggested potluck item with optional notes and dietary tags.

    Supports multiple claims per item - each person can claim the same item.
    """
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    item = PotluckItem.query.get_or_404(item_id)

    # Verify item belongs to this event and is a suggested item
    if item.event_id != event.id or not item.is_suggested:
        flash("Item not found.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authentication - either logged in or has valid token
    person = None
    token = request.args.get("token") or request.form.get("token")

    # Check session first (logged in organizer)
    if session.get("person_id"):
        person = Person.query.get(session.get("person_id"))

    # Check token (guest with invitation)
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            # Get the invitation and household
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household and invitation.household.active_members:
                person = invitation.household.active_members[0]

    if not person:
        flash("Please log in or use your invitation link to claim items.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check if person has already claimed this item
    if item.has_claim_by_person(person.id):
        flash("You've already claimed this item.", "info")
    else:
        # Get optional notes and dietary tags from form
        claimer_notes = request.form.get("claimer_notes", "").strip() or None
        claimer_dietary_tags_str = request.form.get("claimer_dietary_tags", "")
        claimer_dietary_tags = None
        if claimer_dietary_tags_str:
            try:
                claimer_dietary_tags = json.loads(claimer_dietary_tags_str)
            except (json.JSONDecodeError, TypeError):
                claimer_dietary_tags = None

        result = PotluckService.claim_suggested_item(
            item, person,
            claimer_notes=claimer_notes,
            claimer_dietary_tags=claimer_dietary_tags
        )
        if result:
            flash(f"You're bringing '{item.name}'!", "success")
        else:
            flash("Unable to add this item.", "error")

    # Redirect back with token if present
    if token:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
    else:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/potluck/suggested/<int:item_id>/unclaim", methods=["POST"])
def unclaim_suggested_item(event_uuid, item_id):
    """Unclaim a suggested potluck item (only removes the current user's claim)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    item = PotluckItem.query.get_or_404(item_id)

    # Verify item belongs to this event and is a suggested item
    if item.event_id != event.id or not item.is_suggested:
        flash("Item not found.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authentication - either logged in or has valid token
    person = None
    token = request.args.get("token") or request.form.get("token")

    # Check session first (logged in organizer)
    if session.get("person_id"):
        person = Person.query.get(session.get("person_id"))

    # Check token (guest with invitation)
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            # Get the invitation and household
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household and invitation.household.active_members:
                person = invitation.household.active_members[0]

    if not person:
        flash("Please log in or use your invitation link to unclaim items.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check if item is claimed by this person
    if not item.has_claim_by_person(person.id):
        flash("You can only remove items you're bringing.", "error")
    else:
        result = PotluckService.unclaim_suggested_item(item, person)
        if result:
            flash(f"You're no longer bringing '{item.name}'.", "success")
        else:
            flash("Unable to remove this item.", "error")

    # Redirect back with token if present
    if token:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
    else:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))


@bp.route("/event/<uuid:event_uuid>/potluck/suggested/<int:item_id>/edit-claim", methods=["POST"])
def edit_claim_details(event_uuid, item_id):
    """Edit the details (notes, dietary tags) of a claimed suggested item."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    item = PotluckItem.query.get_or_404(item_id)

    # Verify item belongs to this event and is a suggested item
    if item.event_id != event.id or not item.is_suggested:
        flash("Item not found.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check authentication - either logged in or has valid token
    person = None
    token = request.args.get("token") or request.form.get("token")

    # Check session first (logged in organizer)
    if session.get("person_id"):
        person = Person.query.get(session.get("person_id"))

    # Check token (guest with invitation)
    if not person and token:
        token_data = EventInvitation.verify_token(token)
        if token_data and token_data.get("event_id") == event.id:
            # Get the invitation and household
            invitation = EventInvitation.query.filter_by(
                event_id=token_data["event_id"],
                household_id=token_data["household_id"]
            ).first()
            if invitation and invitation.household and invitation.household.active_members:
                person = invitation.household.active_members[0]

    if not person:
        flash("Please log in or use your invitation link to edit items.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))

    # Check if item is claimed by this person
    if not item.has_claim_by_person(person.id):
        flash("You can only edit items you're bringing.", "error")
    else:
        # Get notes and dietary tags from form
        claimer_notes = request.form.get("claimer_notes", "").strip() or None
        claimer_dietary_tags_str = request.form.get("claimer_dietary_tags", "")
        claimer_dietary_tags = None
        if claimer_dietary_tags_str:
            try:
                claimer_dietary_tags = json.loads(claimer_dietary_tags_str)
            except (json.JSONDecodeError, TypeError):
                claimer_dietary_tags = None

        result = PotluckService.update_claim_details(
            item, person,
            claimer_notes=claimer_notes,
            claimer_dietary_tags=claimer_dietary_tags
        )
        if result:
            flash(f"Updated details for '{item.name}'.", "success")
        else:
            flash("Unable to update this item.", "error")

    # Redirect back with token if present
    if token:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
    else:
        return redirect(url_for("public.event_detail", event_uuid=event_uuid))


# ==================== Bring a Friend Routes ====================


@bp.route("/f/<short_token>")
def friend_short_redirect(short_token):
    """Redirect from friend-specific short URL to event detail page.

    This route handles friend invitation links for "bring a friend" feature.
    """
    referral = GuestReferral.get_by_short_token(short_token)

    if not referral:
        flash("Invalid or expired invitation link.", "error")
        return redirect(url_for("public.index"))

    # Ensure the referral has a full token
    if not referral.invitation_token:
        referral.generate_token()
        db.session.commit()

    # Store the referred person_id in session for personalization
    session["invited_person_id"] = referral.referred_person_id
    session["is_brought_friend"] = True

    # Redirect to main event detail page with friend token
    return redirect(url_for(
        "public.event_detail",
        event_uuid=referral.event.uuid,
        token=referral.invitation_token,
    ))


@bp.route("/event/<uuid:event_uuid>/friend")
def event_detail_friend(event_uuid):
    """Legacy route - redirects to main event detail page.

    This route is kept for backward compatibility with existing email links.
    New links should use the main event_detail route with friend token.
    """
    token = request.args.get("token")
    return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))


@bp.route("/event/<uuid:event_uuid>/bring-friend", methods=["GET", "POST"])
@valid_rsvp_token_required
def bring_friend_form(event_uuid):
    """Form to invite a friend to an event."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    household = request.household  # Set by decorator
    token = request.args.get("token")

    # Get the current person (the one inviting the friend)
    current_person = None
    person_id = session.get("person_id")
    if person_id:
        current_person = Person.query.get(person_id)

    # Check if accessed via person-specific invitation link
    if not current_person:
        invited_person_id = session.get("invited_person_id")
        if invited_person_id and household:
            invited_person = Person.query.get(invited_person_id)
            if invited_person and invited_person in household.active_members:
                current_person = invited_person

    # Fall back to first household member
    if not current_person and household and household.active_members:
        current_person = household.active_members[0]

    if not current_person:
        flash("Unable to determine who is inviting the friend.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Check if person can invite friends
    if not BringFriendService.can_person_invite_friends(event, current_person):
        flash("You must be invited to this event to bring a friend.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    if request.method == "POST":
        # Get form data
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip() or None
        email = request.form.get("email", "").strip() or None
        phone = request.form.get("phone", "").strip() or None

        # Validate required fields
        if not first_name:
            flash("Friend's first name is required.", "error")
            return render_template(
                "public/bring_friend_form.html",
                event=event,
                token=token,
                current_person=current_person,
            )

        try:
            # Create the friend invitation
            result = BringFriendService.invite_friend(
                event=event,
                referrer_person=current_person,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
            )

            # Redirect to confirmation page with short link
            referral = result["referral"]
            return redirect(url_for(
                "public.bring_friend_confirmation",
                event_uuid=event_uuid,
                referral_id=referral.id,
                token=token
            ))

        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while inviting your friend. Please try again.", "error")

    # Get friends already invited by this person
    friends_invited = BringFriendService.get_friends_invited_by_person(event, current_person)

    return render_template(
        "public/bring_friend_form.html",
        event=event,
        token=token,
        current_person=current_person,
        friends_invited=friends_invited,
    )


@bp.route("/event/<uuid:event_uuid>/bring-friend/confirmation")
@valid_rsvp_token_required
def bring_friend_confirmation(event_uuid):
    """Confirmation page after inviting a friend."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    token = request.args.get("token")
    referral_id = request.args.get("referral_id")

    if not referral_id:
        flash("Invalid request.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Get the referral
    referral = GuestReferral.query.get(referral_id)
    if not referral or referral.event_id != event.id:
        flash("Invalid invitation reference.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Construct the short link
    short_link = url_for("public.friend_short_redirect", short_token=referral.short_token, _external=True)

    return render_template(
        "public/bring_friend_confirmation.html",
        event=event,
        token=token,
        friend=referral.referred,
        referral=referral,
        short_link=short_link,
    )


@bp.route("/event/<uuid:event_uuid>/bring-friend/<int:referral_id>/resend-email", methods=["POST"])
@valid_rsvp_token_required
def resend_friend_invitation_email(event_uuid, referral_id):
    """Resend invitation email to a brought friend."""
    from app.services.notification_service import NotificationService

    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    token = request.args.get("token") or request.form.get("token")

    # Get the referral
    referral = GuestReferral.query.get(referral_id)
    if not referral or referral.event_id != event.id:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": False, "message": "Invalid referral."}, 400
        flash("Invalid referral.", "error")
        return redirect(url_for("public.bring_friend_form", event_uuid=event_uuid, token=token))

    # Check if friend has email
    friend = referral.referred
    if not friend.email:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": False, "message": "This friend does not have an email address."}, 400
        flash("This friend does not have an email address.", "error")
        return redirect(url_for("public.bring_friend_form", event_uuid=event_uuid, token=token))

    # Send the email
    try:
        success = NotificationService.send_friend_invitation_email(referral, friend)
        if success:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"success": True, "message": f"Invitation email sent to {friend.email}"}
            flash(f"Invitation email sent to {friend.email}", "success")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"success": False, "message": "Failed to send email. Please try again."}, 500
            flash("Failed to send email. Please try again.", "error")
    except Exception as e:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return {"success": False, "message": "An error occurred while sending the email."}, 500
        flash("An error occurred while sending the email.", "error")

    return redirect(url_for("public.bring_friend_form", event_uuid=event_uuid, token=token))


@bp.route("/event/<uuid:event_uuid>/friend/rsvp", methods=["POST"])
def submit_friend_rsvp(event_uuid):
    """Submit RSVP for a brought friend."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    token = request.args.get("token") or request.form.get("token")

    if not token:
        flash("Invalid request.", "error")
        return redirect(url_for("public.index"))

    # Verify friend token
    token_data = GuestReferral.verify_token(token)
    if not token_data or token_data.get("event_id") != event.id:
        flash("Invalid or expired invitation link.", "error")
        return redirect(url_for("public.index"))

    # Get the referral and person
    referral = GuestReferral.query.get(token_data.get("referral_id"))
    if not referral:
        flash("Invalid invitation link.", "error")
        return redirect(url_for("public.index"))

    referred_person = referral.referred

    # Get the RSVP
    rsvp = RSVP.query.filter_by(
        event_id=event.id,
        person_id=referred_person.id
    ).first()

    if not rsvp:
        flash("RSVP not found.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Get form data
    status = request.form.get("status", "").strip()
    notes = request.form.get("notes", "").strip() or None

    # Validate status
    valid_statuses = ["attending", "not_attending", "maybe", "no_response"]
    if status not in valid_statuses:
        flash("Invalid RSVP status.", "error")
        return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))

    # Update the RSVP
    try:
        RSVPService.update_rsvp(rsvp, status, notes)
        flash("Your RSVP has been recorded. Thank you!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while submitting your RSVP. Please try again.", "error")

    return redirect(url_for("public.event_detail", event_uuid=event_uuid, token=token))
