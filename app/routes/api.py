"""API routes - for AJAX requests and webhooks."""
from flask import Blueprint, jsonify, request, session
from app import db
from app.models import Event, RSVP, Notification, EventAdmin, Person, Tag, PersonTag, HouseholdMembership, EventInvitation
from app.services.rsvp_service import RSVPService
from app.services.invitation_service import InvitationService

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health")
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Holiday Party Planner API"})


@bp.route("/webhooks/brevo", methods=["POST"])
def brevo_webhook():
    """Handle Brevo email webhooks (bounces, opens, clicks)."""
    data = request.get_json()

    # TODO: Implement webhook handling
    # - Update notification status based on webhook events
    # - Handle bounces, opens, clicks, etc.

    return jsonify({"status": "received"}), 200


@bp.route("/webhooks/sms", methods=["POST"])
def sms_webhook():
    """Handle SMS webhooks (replies, delivery status)."""
    # TODO: Implement SMS webhook handling when SMS is enabled

    return jsonify({"status": "received"}), 200


@bp.route("/event/<uuid:event_uuid>/rsvp-stats")
def get_rsvp_stats(event_uuid):
    """Get RSVP statistics for an event (for live updates)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    stats = event.get_rsvp_stats()

    return jsonify(stats)


@bp.route("/event/<uuid:event_uuid>/invitation-stats")
def get_invitation_stats(event_uuid):
    """Get invitation statistics for an event (for live updates)."""
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()
    stats = InvitationService.get_invitation_stats(event)

    return jsonify(stats)


@bp.route("/event/<uuid:event_uuid>/invitation/<int:invitation_id>/send", methods=["POST"])
def send_single_invitation(event_uuid, invitation_id):
    """Send a single invitation via AJAX."""
    # Check if user is logged in and is admin
    person_id = session.get("person_id")
    if not person_id:
        return jsonify({"error": "Not authenticated"}), 401

    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Check if person is admin
    is_admin = EventAdmin.query.filter_by(
        event_id=event.id,
        person_id=person_id,
        removed_at=None
    ).first() is not None

    if not is_admin:
        return jsonify({"error": "Not authorized"}), 403

    # Get invitation
    invitation = EventInvitation.query.filter_by(
        id=invitation_id,
        event_id=event.id
    ).first_or_404()

    # Send invitation
    try:
        success = InvitationService.send_invitation(invitation)
        if success:
            return jsonify({
                "success": True,
                "message": f"Invitation sent to {invitation.household.name}",
                "invitation": invitation.to_dict()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Could not send invitation. Household may not have email addresses."
            }), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/event/<uuid:event_uuid>/rsvp/<int:rsvp_id>/update", methods=["POST"])
def update_rsvp_by_host(event_uuid, rsvp_id):
    """Update RSVP status on behalf of a guest (host/admin only).

    This endpoint allows event hosts/admins to manually update a guest's RSVP status,
    typically after receiving RSVP via phone, text, or in-person communication.

    Request JSON:
        {
            "status": "attending|not_attending|maybe|no_response",
            "notes": "Optional notes about the update"
        }

    Returns:
        JSON with updated RSVP data or error message
    """
    # Check authentication
    person_id = session.get("person_id")
    if not person_id:
        return jsonify({"error": "Authentication required"}), 401

    # Get event
    event = Event.query.filter_by(uuid=str(event_uuid)).first_or_404()

    # Check if person is an admin for this event
    is_admin = (
        EventAdmin.query.filter_by(
            event_id=event.id, person_id=person_id, removed_at=None
        ).first()
        is not None
    )

    if not is_admin:
        return jsonify({"error": "Permission denied. Only event admins can update RSVPs."}), 403

    # Get RSVP
    rsvp = RSVP.query.get_or_404(rsvp_id)

    # Verify RSVP belongs to this event
    if rsvp.event_id != event.id:
        return jsonify({"error": "RSVP does not belong to this event"}), 400

    # Verify the household is invited to this event
    invitation = event.invitations.filter_by(household_id=rsvp.household_id).first()
    if not invitation:
        return jsonify({"error": "Household is not invited to this event"}), 400

    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    status = data.get("status")
    notes = data.get("notes")

    if not status:
        return jsonify({"error": "Status is required"}), 400

    # Validate status
    valid_statuses = ["attending", "not_attending", "maybe", "no_response"]
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    try:
        # Update RSVP using service
        updated_rsvp = RSVPService.update_rsvp_by_host(
            rsvp=rsvp,
            status=status,
            host_person_id=person_id,
            notes=notes
        )

        return jsonify({
            "success": True,
            "message": "RSVP updated successfully",
            "rsvp": updated_rsvp.to_dict()
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update RSVP"}), 500


@bp.route("/tags")
def get_all_tags():
    """Get all available tags for autocomplete/selection.

    Query parameters:
        - q: Search query (optional)
        - limit: Maximum number of results (default: 20)

    Returns:
        JSON list of tags with usage counts
    """
    query = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 20)), 100)  # Max 100 results

    if query:
        # Search tags by prefix
        tags = Tag.search_tags(query, limit=limit)
    else:
        # Get popular tags
        tags = Tag.get_popular_tags(limit=limit)

    return jsonify({
        "tags": [tag.to_dict() for tag in tags]
    })


@bp.route("/person/<int:person_id>/tags")
def get_person_tags(person_id):
    """Get all tags for a specific person.

    Returns:
        JSON list of tags for the person
    """
    person = Person.query.get_or_404(person_id)

    return jsonify({
        "person_id": person.id,
        "person_name": person.full_name,
        "tags": [tag.name for tag in person.tags]
    })


@bp.route("/person/<int:person_id>/tags", methods=["POST"])
def add_person_tag(person_id):
    """Add a tag to a person.

    Request JSON:
        {
            "tag_name": "vegetarian",
            "category": "dietary"  # optional, defaults to "dietary"
        }

    Returns:
        JSON with success message and updated tags
    """
    # Check authentication
    current_person_id = session.get("person_id")
    if not current_person_id:
        return jsonify({"error": "Authentication required"}), 401

    person = Person.query.get_or_404(person_id)

    # Check if current user has permission to edit this person's tags
    # Users can edit tags for people in their household
    current_person = Person.query.get(current_person_id)
    person_household_ids = [h.id for h in person.active_households]
    current_household_ids = [h.id for h in current_person.active_households]

    # Check if they share a household
    has_permission = bool(set(person_household_ids) & set(current_household_ids))

    if not has_permission:
        return jsonify({"error": "Permission denied. You can only edit tags for people in your household."}), 403

    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    tag_name = data.get("tag_name", "").strip()
    category = data.get("category", "dietary").strip()

    if not tag_name:
        return jsonify({"error": "tag_name is required"}), 400

    try:
        # Add tag to person
        person_tag = person.add_tag(tag_name, added_by_person_id=current_person_id, category=category)

        if person_tag is None:
            return jsonify({"error": "Tag already exists for this person"}), 400

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Tag '{tag_name}' added to {person.full_name}",
            "tags": [tag.name for tag in person.tags]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add tag: {str(e)}"}), 500


@bp.route("/person/<int:person_id>/tags/<tag_name>", methods=["DELETE"])
def remove_person_tag(person_id, tag_name):
    """Remove a tag from a person.

    Returns:
        JSON with success message and updated tags
    """
    # Check authentication
    current_person_id = session.get("person_id")
    if not current_person_id:
        return jsonify({"error": "Authentication required"}), 401

    person = Person.query.get_or_404(person_id)

    # Check if current user has permission to edit this person's tags
    current_person = Person.query.get(current_person_id)
    person_household_ids = [h.id for h in person.active_households]
    current_household_ids = [h.id for h in current_person.active_households]

    # Check if they share a household
    has_permission = bool(set(person_household_ids) & set(current_household_ids))

    if not has_permission:
        return jsonify({"error": "Permission denied. You can only edit tags for people in your household."}), 403

    try:
        # Remove tag from person
        success = person.remove_tag(tag_name)

        if not success:
            return jsonify({"error": "Tag not found for this person"}), 404

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Tag '{tag_name}' removed from {person.full_name}",
            "tags": [tag.name for tag in person.tags]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to remove tag: {str(e)}"}), 500


@bp.errorhandler(404)
def api_not_found(error):
    """API 404 handler."""
    return jsonify({"error": "Not found"}), 404


@bp.errorhandler(500)
def api_internal_error(error):
    """API 500 handler."""
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

