"""Forms for guest and household management."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, EmailField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Length, Email
from wtforms.widgets import CheckboxInput, ListWidget


class HouseholdForm(FlaskForm):
    """Form for creating and editing households."""
    
    name = StringField(
        'Household Name',
        validators=[
            DataRequired(message="Household name is required"),
            Length(min=2, max=200, message="Name must be between 2 and 200 characters")
        ],
        render_kw={"placeholder": "e.g., The Smith Family"}
    )
    
    address = TextAreaField(
        'Address',
        validators=[Optional()],
        render_kw={
            "placeholder": "123 Main St\nCity, State ZIP",
            "rows": 3
        }
    )


class PersonForm(FlaskForm):
    """Form for creating and editing people."""
    
    first_name = StringField(
        'First Name',
        validators=[
            DataRequired(message="First name is required"),
            Length(min=1, max=100, message="First name must be between 1 and 100 characters")
        ],
        render_kw={"placeholder": "John"}
    )
    
    last_name = StringField(
        'Last Name',
        validators=[
            DataRequired(message="Last name is required"),
            Length(min=1, max=100, message="Last name must be between 1 and 100 characters")
        ],
        render_kw={"placeholder": "Smith"}
    )
    
    email = EmailField(
        'Email',
        validators=[
            Optional(),
            Email(message="Please enter a valid email address")
        ],
        render_kw={"placeholder": "john.smith@example.com"}
    )
    
    phone = StringField(
        'Phone',
        validators=[Optional()],
        render_kw={"placeholder": "(555) 123-4567"}
    )
    
    role = SelectField(
        'Role',
        choices=[
            ('adult', 'Adult'),
            ('child', 'Child')
        ],
        validators=[DataRequired()],
        default='adult'
    )
    
    household_id = SelectField(
        'Household',
        coerce=int,
        validators=[DataRequired(message="Please select a household")],
        render_kw={"class": "household-select"}
    )


class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkboxes."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class InviteHouseholdsForm(FlaskForm):
    """Form for inviting households to an event."""
    
    household_ids = MultiCheckboxField(
        'Select Households to Invite',
        coerce=int,
        validators=[DataRequired(message="Please select at least one household")]
    )


class QuickInviteForm(FlaskForm):
    """Quick form for inviting a single household (used in event context)."""
    
    household_id = SelectField(
        'Select Household',
        coerce=int,
        validators=[DataRequired(message="Please select a household")]
    )

