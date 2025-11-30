"""Phone number utility functions for formatting and validation."""

import re
from typing import Optional


def format_phone_e164(phone: str, default_country_code: str = "1") -> Optional[str]:
    """Format a phone number to E.164 format.

    E.164 format: +[country code][subscriber number]
    Example: +12025551234

    Handles common US phone number formats:
    - (555) 123-4567
    - 555-123-4567
    - 555.123.4567
    - 5551234567
    - +1 555 123 4567
    - 1-555-123-4567

    Args:
        phone: The phone number string to format
        default_country_code: Country code to add if not present (default: "1" for US)

    Returns:
        The phone number in E.164 format (e.g., +12025551234), or None if invalid
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
        # Invalid format - return None
        return None

    # Validate final format: must be + followed by 11 digits for US
    if formatted.startswith(f"+{default_country_code}") and len(formatted) == 12:
        return formatted

    # For non-US numbers, allow if it looks valid (+ followed by 10-15 digits)
    if formatted.startswith("+") and 11 <= len(formatted) <= 16:
        return formatted

    return None


def format_phone_display(phone: str) -> str:
    """Format a phone number for display in user-friendly format.

    Converts E.164 format to a human-readable format.
    Example: +12025551234 -> (202) 555-1234

    Args:
        phone: The phone number (preferably in E.164 format)

    Returns:
        Human-readable phone number string, or original if not parseable
    """
    if not phone:
        return ""

    # Extract just the digits
    digits_only = re.sub(r"[^\d]", "", phone)

    # Handle US numbers (10 or 11 digits)
    if len(digits_only) == 11 and digits_only.startswith("1"):
        # Remove leading 1 for display
        digits_only = digits_only[1:]

    if len(digits_only) == 10:
        # Format as (XXX) XXX-XXXX
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"

    # For other formats, return the original
    return phone


def is_valid_phone(phone: str) -> bool:
    """Check if a phone number is valid (can be formatted to E.164).

    Args:
        phone: The phone number to validate

    Returns:
        True if the phone number can be formatted to E.164, False otherwise
    """
    return format_phone_e164(phone) is not None


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize a phone number for storage.

    This is an alias for format_phone_e164 for semantic clarity.

    Args:
        phone: The phone number to normalize

    Returns:
        The normalized phone number in E.164 format, or None if invalid
    """
    return format_phone_e164(phone)

