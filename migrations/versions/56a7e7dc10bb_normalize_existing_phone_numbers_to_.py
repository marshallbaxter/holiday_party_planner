"""Normalize existing phone numbers to E164 format

Revision ID: 56a7e7dc10bb
Revises: 2ccd9d340ca5
Create Date: 2025-11-30 11:14:26.088548

"""
from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision = '56a7e7dc10bb'
down_revision = '2ccd9d340ca5'
branch_labels = None
depends_on = None


def format_phone_e164(phone, default_country_code="1"):
    """Format a phone number to E.164 format.

    This is a standalone version of the utility function for use in migrations.
    """
    if not phone:
        return None

    # Remove all non-digit characters except leading +
    has_plus = phone.strip().startswith("+")
    digits_only = re.sub(r"[^\d]", "", phone)

    if not digits_only:
        return None

    # Handle different lengths
    if len(digits_only) == 10:
        # Standard US number without country code: 5551234567
        formatted = f"+{default_country_code}{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith(default_country_code):
        # US number with country code: 15551234567
        formatted = f"+{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith("1"):
        # Assume US number starting with 1
        formatted = f"+{digits_only}"
    elif has_plus and len(digits_only) >= 10:
        # Already has + prefix, assume it's properly formatted
        formatted = f"+{digits_only}"
    else:
        # Invalid format - return original
        return phone

    # Validate final format: must be + followed by 11 digits for US
    if formatted.startswith(f"+{default_country_code}") and len(formatted) == 12:
        return formatted

    # For non-US numbers, allow if it looks valid (+ followed by 10-15 digits)
    if formatted.startswith("+") and 11 <= len(formatted) <= 16:
        return formatted

    return phone  # Return original if can't normalize


def upgrade():
    """Normalize all existing phone numbers to E.164 format."""
    # Get connection
    conn = op.get_bind()

    # Get all persons with phone numbers
    result = conn.execute(
        sa.text("SELECT id, phone FROM persons WHERE phone IS NOT NULL AND phone != ''")
    )
    rows = result.fetchall()

    # Update each phone number
    updated_count = 0
    for row in rows:
        person_id, phone = row
        normalized = format_phone_e164(phone)
        if normalized and normalized != phone:
            conn.execute(
                sa.text("UPDATE persons SET phone = :phone WHERE id = :id"),
                {"phone": normalized, "id": person_id}
            )
            updated_count += 1
            print(f"  Normalized phone for person {person_id}: {phone} -> {normalized}")

    if updated_count > 0:
        print(f"  Normalized {updated_count} phone numbers to E.164 format")
    else:
        print("  No phone numbers needed normalization")


def downgrade():
    """This migration only normalizes data format - no downgrade needed.

    Phone numbers in E.164 format are still valid, just normalized.
    """
    pass
