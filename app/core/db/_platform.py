"""
PlatformMixin — AUDIT + TOKENS + ADMIN/PLATFORM + LEADS + PUSH + FOLLOWUPS sections.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List

from app.core.db._base import _uuid

logger = logging.getLogger("clawin.database")


class PlatformMixin:
    """Platform admin, push, tokens, followups, audit, and moderation database operations."""

    # ============================================
    # AUDIT LOG
    # ============================================

    async def log_audit(
        self,
        action: str,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: dict = None
    ):
        """Log an auditable action"""
        async with self._conn() as conn:
            await conn.execute(
                """
                INSERT INTO audit_log (user_id, action, ip_address, user_agent, details)
                VALUES ($1, $2, $3, $4, $5)
                """,
                _uuid(user_id) if user_id else None,
                action, ip_address, user_agent,
                json.dumps(details or {})
            )

    # ============================================
    # PASSWORD RESET TOKENS
    # ============================================

    async def save_reset_token(self, user_id: str, token: str, expires_at) -> dict:
        """Save password reset token"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                VALUES ($1, $2, $3)
                RETURNING id, expires_at
                """,
                _uuid(user_id), token, expires_at
            )
            return dict(row)

    async def verify_reset_token(self, token: str) -> Optional[dict]:
        """Verify a reset token is valid"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, expires_at
                FROM password_reset_tokens
                WHERE token_hash = $1
                  AND used = FALSE
                  AND expires_at > NOW()
                """,
                token
            )
            return dict(row) if row else None

    async def use_reset_token(self, token: str):
        """Mark a reset token as used"""
        async with self._conn() as conn:
            await conn.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE token_hash = $1",
                token
            )

    # ============================================
    # ADMIN / PLATFORM STATS
    # ============================================

    async def get_platform_stats(self) -> dict:
        """Get platform-wide statistics for admin dashboard"""
        async with self._conn() as conn:
            total_users = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE is_active = TRUE"
            )
            subscribers = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE role = 'subscriber' AND is_active = TRUE"
            )
            leads = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE role = 'lead' AND is_active = TRUE"
            )
            active_instances = await conn.fetchval(
                "SELECT COUNT(*) FROM instances WHERE status = 'active'"
            )
            active_subs = await conn.fetchval(
                "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
            )
            mrr = await conn.fetchval(
                """SELECT COUNT(*) * 29.90 FROM subscriptions
                WHERE status = 'active'"""
            )
            total_affiliates = await conn.fetchval(
                "SELECT COUNT(*) FROM affiliates WHERE status = 'active'"
            )
            messages_this_month = await conn.fetchval(
                """SELECT COUNT(*) FROM messages
                WHERE created_at >= DATE_TRUNC('month', NOW())"""
            )

            return {
                "total_users": total_users or 0,
                "subscribers": subscribers or 0,
                "leads": leads or 0,
                "active_instances": active_instances or 0,
                "active_subscriptions": active_subs or 0,
                "mrr": float(mrr or 0),
                "total_affiliates": total_affiliates or 0,
                "messages_this_month": messages_this_month or 0
            }

    async def get_all_subscribers(self, limit: int = 100) -> List[dict]:
        """Get all subscribers with their subscription info"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT u.id, u.email, u.nome, u.role, u.created_at, u.last_login,
                       s.status as sub_status, s.plan, s.current_period_end,
                       i.status as instance_status, i.server_ip, i.ai_model
                FROM users u
                LEFT JOIN subscriptions s ON s.user_id = u.id
                    AND s.status IN ('active', 'past_due', 'trialing')
                LEFT JOIN instances i ON i.user_id = u.id
                    AND i.status IN ('active', 'provisioning')
                WHERE u.role IN ('subscriber', 'admin')
                ORDER BY u.created_at DESC LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    async def get_all_leads(self, limit: int = 100) -> List[dict]:
        """Get all leads (non-subscribers)"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT u.id, u.email, u.nome, u.message_count,
                       u.created_at, u.last_login
                FROM users u
                WHERE u.role = 'lead' AND u.is_active = TRUE
                ORDER BY u.last_login DESC NULLS LAST LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    # ============================================
    # PUSH SUBSCRIPTIONS
    # ============================================

    async def save_push_subscription(self, user_id: str, endpoint: str, p256dh: str, auth: str, user_agent: str = None):
        """Save or update a push subscription"""
        async with self._conn() as conn:
            await conn.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, user_agent)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, endpoint)
                DO UPDATE SET p256dh = $3, auth = $4, user_agent = $5,
                              is_active = TRUE, updated_at = NOW()
                """,
                _uuid(user_id), endpoint, p256dh, auth, user_agent
            )

    async def get_push_subscriptions(self, user_id: str) -> List[dict]:
        """Get active push subscriptions for a user"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT id, endpoint, p256dh, auth
                FROM push_subscriptions
                WHERE user_id = $1 AND is_active = TRUE
                """,
                _uuid(user_id)
            )
            return [dict(row) for row in rows]

    async def delete_push_subscription(self, user_id: str, endpoint: str):
        """Remove a push subscription"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE push_subscriptions SET is_active = FALSE, updated_at = NOW()
                WHERE user_id = $1 AND endpoint = $2
                """,
                _uuid(user_id), endpoint
            )

    async def get_all_active_push_subscriptions(self) -> List[dict]:
        """Get all active push subscriptions (for broadcast)"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT ps.user_id, ps.endpoint, ps.p256dh, ps.auth
                FROM push_subscriptions ps
                WHERE ps.is_active = TRUE
                """
            )
            return [dict(row) for row in rows]

    # ============================================
    # FOLLOWUPS
    # ============================================

    async def create_followup(
        self,
        user_id: str,
        conversation_id: Optional[str],
        message_draft: str,
        followup_note: str,
        scheduled_for: datetime,
        lead_temperature: str = "warm",
        channel: str = "telegram",
        created_by: str = "ai"
    ) -> dict:
        """Create a suggested follow-up (status=suggested by default)."""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO followups (
                    user_id, conversation_id, channel, status,
                    scheduled_for, message_draft, followup_note,
                    lead_temperature, created_by
                )
                VALUES ($1, $2, $3, 'suggested', $4, $5, $6, $7, $8)
                RETURNING id, user_id, conversation_id, channel, status,
                          scheduled_for, message_draft, followup_note,
                          lead_temperature, created_by, created_at
                """,
                _uuid(user_id),
                _uuid(conversation_id) if conversation_id else None,
                channel,
                scheduled_for,
                message_draft,
                followup_note,
                lead_temperature,
                created_by
            )
            return dict(row)

    async def get_pending_followup_approvals(self, limit: int = 50) -> list:
        """Get suggested follow-ups awaiting admin approval."""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT f.id, f.user_id, f.conversation_id, f.channel,
                       f.status, f.scheduled_for, f.message_draft,
                       f.followup_note, f.lead_temperature, f.created_by,
                       f.created_at,
                       u.nome, u.email, u.oauth_id AS chat_id
                FROM followups f
                JOIN users u ON f.user_id = u.id
                WHERE f.status = 'suggested'
                ORDER BY f.created_at ASC
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    async def approve_followup(
        self,
        followup_id: str,
        message_draft: Optional[str] = None,
        scheduled_for: Optional[datetime] = None
    ) -> Optional[dict]:
        """Approve a suggested follow-up (optionally edit draft/time)."""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                UPDATE followups
                SET status = 'approved',
                    message_draft = COALESCE($2, message_draft),
                    scheduled_for = COALESCE($3, scheduled_for),
                    updated_at = NOW()
                WHERE id = $1 AND status = 'suggested'
                RETURNING id, status, scheduled_for, message_draft
                """,
                _uuid(followup_id),
                message_draft,
                scheduled_for
            )
            return dict(row) if row else None

    async def cancel_followup(self, followup_id: str) -> bool:
        """Cancel a suggested or approved follow-up."""
        async with self._conn() as conn:
            result = await conn.execute(
                """
                UPDATE followups SET status = 'cancelled', updated_at = NOW()
                WHERE id = $1 AND status IN ('suggested', 'approved')
                """,
                _uuid(followup_id)
            )
            return result == "UPDATE 1"

    async def cancel_pending_followups_for_user(self, user_id: str) -> int:
        """Cancel all pending follow-ups for a user (opt-out / user replied)."""
        async with self._conn() as conn:
            result = await conn.execute(
                """
                UPDATE followups SET status = 'cancelled', updated_at = NOW()
                WHERE user_id = $1 AND status IN ('suggested', 'approved')
                """,
                _uuid(user_id)
            )
            # Parse "UPDATE N" -> int
            try:
                return int(result.split()[-1])
            except (ValueError, IndexError):
                return 0

    async def get_followups_to_send(self, limit: int = 20) -> list:
        """
        Get approved follow-ups ready to send.
        Respects: status=approved, scheduled_for <= NOW(), opt_out=FALSE,
                  cooldown expired, hour 08-20 BRT.
        """
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT f.id, f.user_id, f.conversation_id, f.channel,
                       f.message_draft, f.followup_note, f.lead_temperature,
                       f.attempt_count, u.oauth_id AS chat_id, u.nome
                FROM followups f
                JOIN users u ON f.user_id = u.id
                WHERE f.status = 'approved'
                  AND f.scheduled_for <= NOW()
                  AND u.followup_opt_out = FALSE
                  AND (u.followup_cooldown_until IS NULL OR u.followup_cooldown_until < NOW())
                  AND EXTRACT(HOUR FROM NOW() AT TIME ZONE 'America/Sao_Paulo') BETWEEN 8 AND 20
                ORDER BY f.scheduled_for ASC
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    async def mark_followup_sent(self, followup_id: str, user_id: str):
        """Mark follow-up as sent and apply 48h cooldown to user."""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE followups
                SET status = 'sent', sent_at = NOW(), updated_at = NOW()
                WHERE id = $1
                """,
                _uuid(followup_id)
            )
            await conn.execute(
                """
                UPDATE users
                SET followup_cooldown_until = NOW() + INTERVAL '48 hours',
                    updated_at = NOW()
                WHERE id = $1
                """,
                _uuid(user_id)
            )

    async def mark_followup_failed(self, followup_id: str, reason: str):
        """Increment attempt_count; mark as failed after 2 attempts."""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE followups
                SET attempt_count = attempt_count + 1,
                    failure_reason = $2,
                    status = CASE WHEN attempt_count + 1 >= 2 THEN 'failed' ELSE status END,
                    updated_at = NOW()
                WHERE id = $1
                """,
                _uuid(followup_id),
                reason
            )

    async def set_followup_opt_out(self, user_id: str, opt_out: bool):
        """Set follow-up opt-out for a user."""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE users SET followup_opt_out = $2, updated_at = NOW()
                WHERE id = $1
                """,
                _uuid(user_id),
                opt_out
            )

    async def count_sent_followups_for_conversation(self, conversation_id: str) -> int:
        """Count sent follow-ups for a conversation (max 3 rule)."""
        async with self._conn() as conn:
            return await conn.fetchval(
                """
                SELECT COUNT(*) FROM followups
                WHERE conversation_id = $1 AND status = 'sent'
                """,
                _uuid(conversation_id)
            ) or 0

    async def get_followup_history(self, user_id: str, limit: int = 20) -> list:
        """Get all follow-ups for a user (admin view)."""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT id, conversation_id, channel, status, scheduled_for,
                       message_draft, followup_note, lead_temperature,
                       created_by, attempt_count, sent_at, created_at
                FROM followups
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                _uuid(user_id),
                limit
            )
            return [dict(row) for row in rows]

    async def get_all_followups(self, status: Optional[str] = None, limit: int = 100) -> list:
        """Get all follow-ups across all users (global admin history view)."""
        async with self._conn() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT f.id, f.user_id, f.channel, f.status, f.scheduled_for,
                           f.message_draft, f.followup_note, f.lead_temperature,
                           f.attempt_count, f.sent_at, f.created_at,
                           u.nome, u.email
                    FROM followups f
                    JOIN users u ON f.user_id = u.id
                    WHERE f.status = $1
                    ORDER BY f.created_at DESC
                    LIMIT $2
                    """,
                    status, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT f.id, f.user_id, f.channel, f.status, f.scheduled_for,
                           f.message_draft, f.followup_note, f.lead_temperature,
                           f.attempt_count, f.sent_at, f.created_at,
                           u.nome, u.email
                    FROM followups f
                    JOIN users u ON f.user_id = u.id
                    ORDER BY f.created_at DESC
                    LIMIT $1
                    """,
                    limit
                )
            return [dict(row) for row in rows]
