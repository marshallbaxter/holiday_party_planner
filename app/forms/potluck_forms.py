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


class SuggestedPotluckItemForm(FlaskForm):
    """Form for adding and editing suggested potluck items (organizer-created)."""

    name = StringField(
        'Item Name',
        validators=[
            DataRequired(message="Item name is required"),
            Length(min=2, max=200, message="Item name must be between 2 and 200 characters")
        ],
        render_kw={"placeholder": "e.g., Appetizers, Main Dish, Dessert"}
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

    notes = TextAreaField(
        'Description/Notes',
        validators=[
            Optional(),
            Length(max=500, message="Notes must be less than 500 characters")
        ],
        render_kw={
            "placeholder": "e.g., Something to feed 8-10 people, homemade or store-bought",
            "rows": 2
        }
    )


class ClaimSuggestedItemForm(FlaskForm):
    """Form for claiming a suggested potluck item with optional details."""

    claimer_notes = TextAreaField(
        'What are you bringing?',
        validators=[
            Optional(),
            Length(max=500, message="Notes must be less than 500 characters")
        ],
        render_kw={
            "placeholder": "e.g., Homemade mac and cheese with three cheeses",
            "rows": 2
        }
    )

    claimer_dietary_tags = HiddenField(
        'Dietary Tags',
        validators=[Optional()]
    )

