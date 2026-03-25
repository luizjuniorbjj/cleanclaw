"""
Xcleaners v3 — Setup Validator.

Validates onboarding step data before saving.
Returns (is_valid, errors) tuples.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger("xcleaners.setup_validator")


def validate_step1(data: dict) -> tuple[bool, list[str]]:
    """Validate Step 1: Business Info."""
    errors = []

    name = data.get("business_name", "").strip()
    if not name:
        errors.append("Business name is required.")
    elif len(name) > 255:
        errors.append("Business name must be 255 characters or fewer.")

    phone = data.get("phone", "").strip()
    if not phone:
        errors.append("Contact phone is required.")
    elif len(phone) < 5:
        errors.append("Phone number is too short.")

    address = data.get("address_line1", "").strip()
    if not address:
        errors.append("Address is required.")

    timezone = data.get("timezone", "").strip()
    if not timezone:
        errors.append("Timezone is required.")

    return (len(errors) == 0, errors)


def validate_step2(data: dict) -> tuple[bool, list[str]]:
    """Validate Step 2: Services."""
    errors = []

    services = data.get("services", [])
    selected = [s for s in services if s.get("is_selected", True)]

    if not selected:
        errors.append("Select at least one service.")

    for i, svc in enumerate(selected):
        name = svc.get("name", "").strip()
        if not name:
            errors.append(f"Service #{i + 1}: name is required.")

    return (len(errors) == 0, errors)


def validate_step3(data: dict) -> tuple[bool, list[str]]:
    """Validate Step 3: Service Area (optional, always valid if skipped)."""
    errors = []

    serve_all = data.get("serve_all_areas", False)
    areas = data.get("areas", [])

    if not serve_all and not areas:
        # Step 3 is skippable, but if areas are provided they must be valid
        pass  # Allow empty (will be skipped)

    for i, area in enumerate(areas):
        name = area.get("name", "").strip()
        if not name:
            errors.append(f"Area #{i + 1}: name is required.")

    return (len(errors) == 0, errors)


def validate_step4(data: dict) -> tuple[bool, list[str]]:
    """Validate Step 4: Pricing (optional, always valid if using defaults)."""
    errors = []

    extras = data.get("extras", [])
    for i, extra in enumerate(extras):
        name = extra.get("name", "").strip()
        if not name:
            errors.append(f"Pricing extra #{i + 1}: name is required.")

        rule_type = extra.get("rule_type", "")
        valid_types = ("surcharge", "multiplier", "discount_percent", "discount_fixed", "minimum", "package")
        if rule_type and rule_type not in valid_types:
            errors.append(f"Pricing extra #{i + 1}: invalid rule type '{rule_type}'.")

        value = extra.get("value")
        if value is None:
            errors.append(f"Pricing extra #{i + 1}: value is required.")

    return (len(errors) == 0, errors)


def validate_step5(data: dict) -> tuple[bool, list[str]]:
    """Validate Step 5: Team (optional)."""
    errors = []

    emails = data.get("invite_emails", [])
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    for email in emails:
        email = email.strip()
        if email and not email_pattern.match(email):
            errors.append(f"Invalid email address: {email}")

    team_name = data.get("team_name", "")
    if team_name and len(team_name) > 100:
        errors.append("Team name must be 100 characters or fewer.")

    return (len(errors) == 0, errors)


# Step validator dispatch
STEP_VALIDATORS = {
    1: validate_step1,
    2: validate_step2,
    3: validate_step3,
    4: validate_step4,
    5: validate_step5,
}


def validate_step(step: int, data: dict) -> tuple[bool, list[str]]:
    """Validate data for a given onboarding step."""
    validator = STEP_VALIDATORS.get(step)
    if not validator:
        return (False, [f"Invalid step number: {step}"])
    return validator(data)
