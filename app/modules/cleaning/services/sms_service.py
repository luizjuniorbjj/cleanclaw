"""
CleanClaw v3 — SMS Service (Sprint 4).

Twilio integration for sending SMS notifications.
Handles: send_sms, send_template, validate_phone, format_number,
cost tracking, retry logic, and quota enforcement.

Config via environment variables:
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
"""

import logging
import re
from typing import Optional

from app.database import Database
from app.modules.cleaning.middleware.plan_guard import get_business_plan
from app.modules.cleaning.models.auth import PLAN_LIMITS

logger = logging.getLogger("cleanclaw.sms_service")

# Twilio client — lazy loaded
_twilio_client = None


def _get_twilio_config() -> tuple:
    """Get Twilio config from environment."""
    import os
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    phone = os.getenv("TWILIO_PHONE_NUMBER", "")
    return sid, token, phone


def _get_client():
    """Lazy-load Twilio client."""
    global _twilio_client
    if _twilio_client is not None:
        return _twilio_client

    sid, token, _ = _get_twilio_config()
    if not sid or not token:
        logger.warning("[SMS] Twilio not configured (missing SID/TOKEN)")
        return None

    try:
        from twilio.rest import Client
        _twilio_client = Client(sid, token)
        return _twilio_client
    except ImportError:
        logger.error("[SMS] twilio package not installed. Run: pip install twilio")
        return None
    except Exception as e:
        logger.error("[SMS] Failed to create Twilio client: %s", e)
        return None


# ============================================
# PHONE NUMBER FORMATTING
# ============================================

def format_number(phone: str) -> str:
    """
    Format a phone number to E.164 format (+1XXXXXXXXXX).
    Strips non-digit chars, adds +1 if missing country code.
    """
    if not phone:
        return ""

    # Strip everything except digits and leading +
    cleaned = re.sub(r"[^\d+]", "", phone)

    # If starts with +, keep as-is
    if cleaned.startswith("+"):
        return cleaned

    # Remove leading 1 if 11 digits (US)
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) > 10:
        return f"+{digits}"

    # Return with + prefix as best effort
    return f"+{digits}" if digits else ""


def validate_phone(phone: str) -> bool:
    """Validate that a phone number is in E.164 format."""
    formatted = format_number(phone)
    # E.164: + followed by 10-15 digits
    return bool(re.match(r"^\+\d{10,15}$", formatted))


# ============================================
# SMS QUOTA CHECK
# ============================================

async def check_sms_quota(
    db: Database,
    business_id: str,
) -> dict:
    """
    Check current SMS usage against plan quota.
    Returns: {used, limit, remaining, allowed}
    """
    plan = await get_business_plan(business_id, db)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])
    monthly_limit = limits.get("sms_monthly", 50)

    # Count SMS sent this month
    used = await db.pool.fetchval(
        """SELECT COUNT(*) FROM cleaning_notifications
           WHERE business_id = $1
             AND channel = 'sms'
             AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
             AND status IN ('sent', 'delivered', 'pending')""",
        business_id,
    )
    used = used or 0

    if monthly_limit == -1:
        return {"used": used, "limit": -1, "remaining": -1, "allowed": True}

    remaining = max(0, monthly_limit - used)
    return {
        "used": used,
        "limit": monthly_limit,
        "remaining": remaining,
        "allowed": remaining > 0,
    }


# ============================================
# SEND SMS
# ============================================

async def send_sms(
    db: Database,
    business_id: str,
    to_phone: str,
    message: str,
    target_type: str = "client",
    target_id: Optional[str] = None,
    template_key: str = "custom",
    max_retries: int = 3,
) -> dict:
    """
    Send an SMS via Twilio with cost tracking and retry logic.

    Returns: {success, message_sid, cost, status}
    """
    formatted = format_number(to_phone)
    if not validate_phone(formatted):
        return {"success": False, "error": "Invalid phone number", "status": "failed"}

    # Quota check
    quota = await check_sms_quota(db, business_id)
    if not quota["allowed"]:
        return {
            "success": False,
            "error": f"SMS quota exceeded ({quota['used']}/{quota['limit']} this month)",
            "status": "quota_exceeded",
        }

    client = _get_client()
    if not client:
        return {"success": False, "error": "Twilio not configured", "status": "failed"}

    _, _, from_phone = _get_twilio_config()
    if not from_phone:
        return {"success": False, "error": "Twilio phone number not configured", "status": "failed"}

    # Retry loop
    last_error = None
    for attempt in range(max_retries):
        try:
            msg = client.messages.create(
                body=message,
                from_=from_phone,
                to=formatted,
            )

            # Estimate cost (US domestic ~$0.0079)
            cost = 0.0079

            # Record in notifications table
            await db.pool.execute(
                """INSERT INTO cleaning_notifications
                   (business_id, channel, provider, target_type, target_id,
                    phone_number, template_key, payload_json,
                    status, cost, sent_at, retry_count)
                   VALUES ($1, 'sms', 'twilio', $2, $3, $4, $5,
                           $6::JSONB, 'sent', $7, NOW(), $8)""",
                business_id, target_type, target_id,
                formatted, template_key,
                f'{{"message": "{message[:200]}", "sid": "{msg.sid}"}}',
                cost, attempt,
            )

            return {
                "success": True,
                "message_sid": msg.sid,
                "cost": cost,
                "status": "sent",
            }

        except Exception as e:
            last_error = str(e)
            logger.warning(
                "[SMS] Attempt %d/%d failed for %s: %s",
                attempt + 1, max_retries, formatted, e,
            )
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(1 * (attempt + 1))

    # All retries exhausted
    await db.pool.execute(
        """INSERT INTO cleaning_notifications
           (business_id, channel, provider, target_type, target_id,
            phone_number, template_key, status, retry_count, error_message)
           VALUES ($1, 'sms', 'twilio', $2, $3, $4, $5, 'failed', $6, $7)""",
        business_id, target_type, target_id,
        formatted, template_key, max_retries, last_error,
    )

    return {
        "success": False,
        "error": f"All {max_retries} retries failed: {last_error}",
        "status": "failed",
    }


# ============================================
# SEND TEMPLATE SMS
# ============================================

# Template definitions
SMS_TEMPLATES = {
    "booking_confirmation": (
        "CleanClaw: Your cleaning is confirmed for {date} at {time}. "
        "Address: {address}. Questions? Reply to this message."
    ),
    "reminder_24h": (
        "CleanClaw Reminder: Your cleaning is tomorrow ({date}) at {time}. "
        "Our team will arrive at {address}. See you then!"
    ),
    "invoice_sent": (
        "CleanClaw: Invoice {invoice_number} for ${total} is ready. "
        "Due: {due_date}. Pay online: {payment_url}"
    ),
    "payment_reminder": (
        "CleanClaw: Invoice {invoice_number} is {days_overdue} days overdue. "
        "Balance: ${balance_due}. Please pay at your earliest convenience."
    ),
    "schedule_changed": (
        "CleanClaw: Your cleaning has been rescheduled to {new_date} at {new_time}. "
        "Contact us if you have questions."
    ),
    "checkin_alert": (
        "CleanClaw: Your cleaning team has arrived at {address} and started working."
    ),
}


async def send_template_sms(
    db: Database,
    business_id: str,
    to_phone: str,
    template_key: str,
    data: dict,
    target_type: str = "client",
    target_id: Optional[str] = None,
) -> dict:
    """Send a templated SMS."""
    template = SMS_TEMPLATES.get(template_key)
    if not template:
        return {"success": False, "error": f"Unknown template: {template_key}"}

    try:
        message = template.format(**{k: v or "" for k, v in data.items()})
    except KeyError as e:
        return {"success": False, "error": f"Missing template variable: {e}"}

    return await send_sms(
        db, business_id, to_phone, message,
        target_type=target_type, target_id=target_id,
        template_key=template_key,
    )
