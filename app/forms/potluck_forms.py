"""Forms for potluck management."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Optional, Length


class PotluckItemForm(FlaskForm):
    """Form for adding and editing potluck items."""

    name = StringField(
        'Item Name',
        validators=[
            DataRequired(message="Item name is required"),
            Length(min=2, max=200, message="Item name must be between 2 and 200 characters")
        ],
        render_kw={"placeholder": "e.g., Green Bean Casserole, Apple Pie"}
    )

    category = SelectField(
        'Category',
        choices=[
            ('main', '🍖 Main Dish'),
            ('side', '🥗 Side Dish'),
            ('dessert', '🍰 Dessert'),
            ('drink', '🥤 Drink'),
            ('other', '📦 Other')
        ],
        validators=[Optional()],
        default='other'
    )

    dietary_tags = HiddenField(
        'Dietary Tags',
        validators=[Optional()]
    )

    contributor_ids = HiddenField(
        'Contributors',
        validators=[Optional()]
    )

    notes = TextAreaField(
        'Notes',
        validators=[
            Optional(),
            Length(max=500, message="Notes must be less than 500 characters")
        ],
        render_kw={
            "placeholder": "e.g., Serves 8-10 people, will be hot and ready to serve",
            "rows": 3
        }
    )

