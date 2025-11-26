"""Forms for event management."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeLocalField, SelectField, URLField
from wtforms.validators import DataRequired, Optional, Length, URL


class EventForm(FlaskForm):
    """Form for creating and editing events."""
    
    title = StringField(
        'Event Title',
        validators=[
            DataRequired(message="Event title is required"),
            Length(min=3, max=200, message="Title must be between 3 and 200 characters")
        ],
        render_kw={"placeholder": "e.g., Annual Holiday Party 2024"}
    )
    
    description = TextAreaField(
        'Description',
        validators=[Optional()],
        render_kw={
            "placeholder": "Describe your event...",
            "rows": 5
        }
    )
    
    event_date = DateTimeLocalField(
        'Event Date & Time',
        validators=[DataRequired(message="Event date and time are required")],
        format='%Y-%m-%dT%H:%M'
    )
    
    venue_address = TextAreaField(
        'Venue Address',
        validators=[Optional()],
        render_kw={
            "placeholder": "e.g., 123 Main St, City, State ZIP",
            "rows": 2
        }
    )
    
    venue_map_url = URLField(
        'Map URL',
        validators=[Optional(), URL(message="Please enter a valid URL")],
        render_kw={"placeholder": "https://maps.google.com/?q=..."}
    )
    
    rsvp_deadline = DateTimeLocalField(
        'RSVP Deadline',
        validators=[Optional()],
        format='%Y-%m-%dT%H:%M'
    )
    
    status = SelectField(
        'Event Status',
        choices=[
            ('draft', 'Draft - Not visible to guests'),
            ('published', 'Published - Visible to invited guests'),
            ('archived', 'Archived - Read-only')
        ],
        validators=[DataRequired()]
    )
    
    def validate(self, extra_validators=None):
        """Custom validation."""
        if not super().validate(extra_validators):
            return False
        
        # Validate that RSVP deadline is before event date
        if self.rsvp_deadline.data and self.event_date.data:
            if self.rsvp_deadline.data >= self.event_date.data:
                self.rsvp_deadline.errors.append(
                    "RSVP deadline must be before the event date"
                )
                return False
        
        return True

