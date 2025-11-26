"""Global guest management routes - for system organizers only."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db
from app.models import Household, Person, HouseholdMembership
from app.utils.decorators import login_required
from app.forms.guest_forms import HouseholdForm, PersonForm

bp = Blueprint("guests", __name__, url_prefix="/organizer/guests")


@bp.route("/")
@login_required
def index():
    """List all households in the system (global view)."""
    # Get all households with their members
    households = Household.query.order_by(Household.name).all()
    
    return render_template(
        "guests/index.html",
        households=households
    )


@bp.route("/household/new", methods=["GET", "POST"])
@login_required
def create_household():
    """Create a new household."""
    form = HouseholdForm()
    
    if form.validate_on_submit():
        try:
            # Create household
            household = Household(
                name=form.name.data,
                address=form.address.data
            )
            db.session.add(household)
            db.session.commit()
            
            flash(f"Household '{household.name}' created successfully!", "success")
            return redirect(url_for("guests.view_household", household_id=household.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating household: {str(e)}", "error")
    
    return render_template("guests/household_form.html", form=form, title="Create Household")


@bp.route("/household/<int:household_id>")
@login_required
def view_household(household_id):
    """View household details and members."""
    household = Household.query.get_or_404(household_id)
    
    # Get all active members
    members = household.active_members
    
    return render_template(
        "guests/household_detail.html",
        household=household,
        members=members
    )


@bp.route("/household/<int:household_id>/edit", methods=["GET", "POST"])
@login_required
def edit_household(household_id):
    """Edit household details."""
    household = Household.query.get_or_404(household_id)
    form = HouseholdForm(obj=household)
    
    if form.validate_on_submit():
        try:
            household.name = form.name.data
            household.address = form.address.data
            db.session.commit()
            
            flash(f"Household '{household.name}' updated successfully!", "success")
            return redirect(url_for("guests.view_household", household_id=household.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating household: {str(e)}", "error")
    
    return render_template(
        "guests/household_form.html",
        form=form,
        household=household,
        title="Edit Household"
    )


@bp.route("/household/<int:household_id>/delete", methods=["POST"])
@login_required
def delete_household(household_id):
    """Delete a household (soft delete - mark members as left)."""
    household = Household.query.get_or_404(household_id)
    
    try:
        # Mark all members as having left
        for membership in household.memberships:
            if not membership.left_at:
                membership.left_at = db.func.now()
        
        db.session.commit()
        flash(f"Household '{household.name}' archived successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error archiving household: {str(e)}", "error")
    
    return redirect(url_for("guests.index"))


@bp.route("/household/<int:household_id>/person/new", methods=["GET", "POST"])
@login_required
def add_person(household_id):
    """Add a new person to a household."""
    household = Household.query.get_or_404(household_id)
    form = PersonForm()
    
    # Pre-populate household field
    form.household_id.choices = [(household.id, household.name)]
    form.household_id.data = household.id
    
    if form.validate_on_submit():
        try:
            # Create person
            person = Person(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                role=form.role.data
            )
            db.session.add(person)
            db.session.flush()  # Get person.id
            
            # Create household membership
            membership = HouseholdMembership(
                person_id=person.id,
                household_id=household.id,
                role=form.role.data
            )
            db.session.add(membership)
            db.session.commit()
            
            flash(f"{person.full_name} added to {household.name}!", "success")
            return redirect(url_for("guests.view_household", household_id=household.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding person: {str(e)}", "error")
    
    return render_template(
        "guests/person_form.html",
        form=form,
        household=household,
        title=f"Add Person to {household.name}"
    )


@bp.route("/person/<int:person_id>/edit", methods=["GET", "POST"])
@login_required
def edit_person(person_id):
    """Edit person details."""
    person = Person.query.get_or_404(person_id)

    # Get person's current household membership
    membership = HouseholdMembership.query.filter_by(
        person_id=person.id,
        left_at=None
    ).first()

    if not membership:
        flash("Person is not currently in a household.", "error")
        return redirect(url_for("guests.index"))

    form = PersonForm(obj=person)

    # Populate household choices
    households = Household.query.order_by(Household.name).all()
    form.household_id.choices = [(h.id, h.name) for h in households]
    form.household_id.data = membership.household_id

    if form.validate_on_submit():
        try:
            # Update person details
            person.first_name = form.first_name.data
            person.last_name = form.last_name.data
            person.email = form.email.data
            person.phone = form.phone.data
            person.role = form.role.data

            # Update membership
            membership.role = form.role.data

            # If household changed, move person to new household
            if membership.household_id != form.household_id.data:
                # Mark old membership as left
                membership.left_at = db.func.now()

                # Create new membership
                new_membership = HouseholdMembership(
                    person_id=person.id,
                    household_id=form.household_id.data,
                    role=form.role.data
                )
                db.session.add(new_membership)

            db.session.commit()

            flash(f"{person.full_name} updated successfully!", "success")
            return redirect(url_for("guests.view_household", household_id=form.household_id.data))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating person: {str(e)}", "error")

    return render_template(
        "guests/person_form.html",
        form=form,
        person=person,
        household=membership.household,
        title=f"Edit {person.full_name}"
    )


@bp.route("/person/<int:person_id>/delete", methods=["POST"])
@login_required
def delete_person(person_id):
    """Remove person from household (soft delete)."""
    person = Person.query.get_or_404(person_id)

    # Get active membership
    membership = HouseholdMembership.query.filter_by(
        person_id=person.id,
        left_at=None
    ).first()

    if not membership:
        flash("Person is not currently in a household.", "error")
        return redirect(url_for("guests.index"))

    try:
        # Mark as left
        membership.left_at = db.func.now()
        db.session.commit()

        flash(f"{person.full_name} removed from {membership.household.name}.", "success")
        return redirect(url_for("guests.view_household", household_id=membership.household_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error removing person: {str(e)}", "error")
        return redirect(url_for("guests.index"))

