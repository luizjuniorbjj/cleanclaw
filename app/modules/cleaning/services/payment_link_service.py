"""
CleanClaw v3 — Payment Link Service (Sprint 4).

Stripe payment link generation for invoices and subscriptions.
Handles Checkout Sessions, webhook verification, and payment status.

Env vars:
  STRIPE_SECRET_KEY         — Stripe API key
  STRIPE_WEBHOOK_SECRET     — Webhook endpoint secret
  STRIPE_PRICE_BASIC        — Price ID for Basic plan
  STRIPE_PRICE_INTERMEDIATE — Price ID for Intermediate plan
  STRIPE_PRICE_MAXIMUM      — Price ID for Maximum plan
"""

import logging
import os
from typing import Dict, Optional

import stripe

from app.config import STRIPE_SECRET_KEY, APP_URL
from app.database import Database

logger = logging.getLogger("cleanclaw.payment_link_service")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Plan tier -> Stripe Price ID mapping
STRIPE_PRICE_BASIC = os.getenv("STRIPE_PRICE_BASIC", "")
STRIPE_PRICE_INTERMEDIATE = os.getenv("STRIPE_PRICE_INTERMEDIATE", "")
STRIPE_PRICE_MAXIMUM = os.getenv("STRIPE_PRICE_MAXIMUM", "")

PLAN_PRICE_MAP = {
    "basic": STRIPE_PRICE_BASIC,
    "intermediate": STRIPE_PRICE_INTERMEDIATE,
    "maximum": STRIPE_PRICE_MAXIMUM,
}


# ============================================
# PAYMENT LINK (one-time invoice payment)
# ============================================

async def create_payment_link(
    invoice_id: str,
    amount_cents: int,
    client_email: str,
    description: str,
    metadata: Optional[Dict] = None,
) -> str:
    """
    Create a Stripe Checkout Session for a one-time payment.

    Args:
        invoice_id: CleanClaw invoice UUID
        amount_cents: Amount in cents (e.g. 15000 = $150.00)
        client_email: Pre-fill customer email
        description: Line item description
        metadata: Extra metadata for the session

    Returns: Checkout session URL

    Raises: ValueError if Stripe not configured, stripe.error.StripeError on API failure
    """
    if not STRIPE_SECRET_KEY:
        raise ValueError("Stripe not configured (STRIPE_SECRET_KEY missing)")

    session_metadata = {
        "cleanclaw_invoice_id": invoice_id,
        "type": "invoice_payment",
    }
    if metadata:
        session_metadata.update(metadata)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=client_email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": description,
                    },
                },
                "quantity": 1,
            }],
            metadata=session_metadata,
            success_url=f"{APP_URL}/cleaning/app?payment=success&invoice={invoice_id}",
            cancel_url=f"{APP_URL}/cleaning/app?payment=cancelled&invoice={invoice_id}",
        )

        logger.info(
            "[PAYMENT] Checkout session created for invoice %s: %s",
            invoice_id, session.id,
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error("[PAYMENT] Stripe error creating payment link: %s", e)
        raise


# ============================================
# SUBSCRIPTION LINK (business plan)
# ============================================

async def create_subscription_link(
    business_id: str,
    plan_tier: str,
    owner_email: str,
) -> str:
    """
    Create a Stripe Checkout Session for a subscription.

    Args:
        business_id: CleanClaw business UUID
        plan_tier: One of 'basic', 'intermediate', 'maximum'
        owner_email: Business owner email

    Returns: Checkout session URL

    Raises: ValueError if plan not found or Stripe not configured
    """
    if not STRIPE_SECRET_KEY:
        raise ValueError("Stripe not configured (STRIPE_SECRET_KEY missing)")

    price_id = PLAN_PRICE_MAP.get(plan_tier.lower())
    if not price_id:
        available = [k for k, v in PLAN_PRICE_MAP.items() if v]
        raise ValueError(
            f"Unknown or unconfigured plan tier: {plan_tier}. "
            f"Available: {available}"
        )

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=owner_email,
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            metadata={
                "cleanclaw_business_id": business_id,
                "plan_tier": plan_tier,
                "type": "subscription",
            },
            success_url=f"{APP_URL}/cleaning/app?subscription=success&plan={plan_tier}",
            cancel_url=f"{APP_URL}/cleaning/app?subscription=cancelled",
        )

        logger.info(
            "[PAYMENT] Subscription session created for business %s (%s): %s",
            business_id, plan_tier, session.id,
        )
        return session.url

    except stripe.error.StripeError as e:
        logger.error("[PAYMENT] Stripe error creating subscription: %s", e)
        raise


# ============================================
# WEBHOOK HANDLER
# ============================================

async def handle_payment_webhook(
    payload: bytes,
    sig_header: str,
    db: Database,
) -> dict:
    """
    Verify and handle Stripe webhook events.

    Handles:
      - checkout.session.completed — mark invoice as paid
      - invoice.paid — subscription renewal confirmation
      - invoice.payment_failed — mark payment failure

    Args:
        payload: Raw request body bytes
        sig_header: Stripe-Signature header value
        db: Database instance

    Returns: {event_type, handled, details}
    """
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("[WEBHOOK] STRIPE_WEBHOOK_SECRET not configured")
        return {"event_type": "unknown", "handled": False, "error": "Webhook secret not configured"}

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("[WEBHOOK] Invalid signature")
        return {"event_type": "unknown", "handled": False, "error": "Invalid signature"}
    except ValueError:
        logger.warning("[WEBHOOK] Invalid payload")
        return {"event_type": "unknown", "handled": False, "error": "Invalid payload"}

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("[WEBHOOK] Received event: %s", event_type)

    if event_type == "checkout.session.completed":
        return await _handle_checkout_completed(db, data)

    elif event_type == "invoice.paid":
        return await _handle_invoice_paid(db, data)

    elif event_type == "invoice.payment_failed":
        return await _handle_payment_failed(db, data)

    else:
        logger.info("[WEBHOOK] Unhandled event type: %s", event_type)
        return {"event_type": event_type, "handled": False}


async def _handle_checkout_completed(db: Database, session: dict) -> dict:
    """Handle checkout.session.completed — mark CleanClaw invoice as paid."""
    metadata = session.get("metadata", {})
    invoice_id = metadata.get("cleanclaw_invoice_id")
    payment_type = metadata.get("type", "")

    if payment_type == "invoice_payment" and invoice_id:
        amount_total = session.get("amount_total", 0) / 100.0
        await db.pool.execute(
            """UPDATE cleaning_invoices
               SET status = 'paid',
                   amount_paid = total,
                   payment_method = 'stripe',
                   payment_reference = $2,
                   stripe_invoice_id = $3,
                   paid_at = NOW(),
                   updated_at = NOW()
               WHERE id = $1 AND balance_due > 0""",
            invoice_id,
            session.get("payment_intent", session.get("id")),
            session.get("id"),
        )
        logger.info("[WEBHOOK] Invoice %s marked as paid ($%.2f)", invoice_id, amount_total)
        return {
            "event_type": "checkout.session.completed",
            "handled": True,
            "invoice_id": invoice_id,
            "amount": amount_total,
        }

    elif payment_type == "subscription":
        business_id = metadata.get("cleanclaw_business_id")
        plan_tier = metadata.get("plan_tier")
        if business_id:
            await db.pool.execute(
                """UPDATE businesses
                   SET metadata = COALESCE(metadata, '{}'::JSONB) ||
                       jsonb_build_object(
                           'stripe_customer_id', $2::TEXT,
                           'subscription_id', $3::TEXT,
                           'plan_tier', $4::TEXT
                       ),
                       updated_at = NOW()
                   WHERE id = $1""",
                business_id,
                session.get("customer"),
                session.get("subscription"),
                plan_tier,
            )
            logger.info("[WEBHOOK] Business %s subscribed to %s", business_id, plan_tier)
        return {
            "event_type": "checkout.session.completed",
            "handled": True,
            "business_id": business_id,
            "plan": plan_tier,
        }

    return {"event_type": "checkout.session.completed", "handled": False}


async def _handle_invoice_paid(db: Database, invoice: dict) -> dict:
    """Handle invoice.paid — subscription renewal."""
    subscription_id = invoice.get("subscription")
    if subscription_id:
        logger.info("[WEBHOOK] Subscription invoice paid: %s", subscription_id)
    return {"event_type": "invoice.paid", "handled": True, "subscription": subscription_id}


async def _handle_payment_failed(db: Database, invoice: dict) -> dict:
    """Handle invoice.payment_failed — log failure."""
    subscription_id = invoice.get("subscription")
    customer = invoice.get("customer")
    logger.warning(
        "[WEBHOOK] Payment failed for customer %s, subscription %s",
        customer, subscription_id,
    )
    return {
        "event_type": "invoice.payment_failed",
        "handled": True,
        "customer": customer,
        "subscription": subscription_id,
    }


# ============================================
# PAYMENT STATUS CHECK
# ============================================

async def get_payment_status(session_id: str) -> dict:
    """
    Check the status of a Stripe Checkout Session.

    Args:
        session_id: Stripe session ID

    Returns: {session_id, status, payment_status, amount_total, customer_email}
    """
    if not STRIPE_SECRET_KEY:
        return {"error": "Stripe not configured"}

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "session_id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": (session.amount_total or 0) / 100.0,
            "customer_email": session.customer_email,
            "metadata": dict(session.metadata) if session.metadata else {},
        }
    except stripe.error.StripeError as e:
        logger.error("[PAYMENT] Error retrieving session %s: %s", session_id, e)
        return {"error": str(e), "session_id": session_id}
