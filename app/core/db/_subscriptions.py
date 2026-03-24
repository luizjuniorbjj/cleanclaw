"""
SubscriptionsMixin — SUBSCRIPTIONS + INSTANCES + DEPLOYMENTS + HOSTINGER sections.
"""

import json
import logging
from datetime import datetime
from typing import Optional, List

from app.core.db._base import _uuid
from app.security import encrypt_data

logger = logging.getLogger("clawin.database")


class SubscriptionsMixin:
    """Subscription, instance, and deployment database operations."""

    # ============================================
    # SUBSCRIPTIONS (Stripe)
    # ============================================

    async def create_subscription(
        self,
        user_id: str,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        plan: str = "standard",
        status: str = "active",
        current_period_start: datetime = None,
        current_period_end: datetime = None
    ) -> dict:
        """Create subscription record after Stripe checkout"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO subscriptions (
                    user_id, stripe_subscription_id, stripe_customer_id,
                    plan, status, current_period_start, current_period_end
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                _uuid(user_id), stripe_subscription_id, stripe_customer_id,
                plan, status, current_period_start, current_period_end
            )
            return dict(row)

    async def get_subscription_by_user(self, user_id: str) -> Optional[dict]:
        """Get active subscription for a user"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM subscriptions
                WHERE user_id = $1 AND status IN ('active', 'trialing', 'past_due')
                ORDER BY created_at DESC LIMIT 1
                """,
                _uuid(user_id)
            )
            return dict(row) if row else None

    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[dict]:
        """Get subscription by Stripe subscription ID"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM subscriptions WHERE stripe_subscription_id = $1",
                stripe_subscription_id
            )
            return dict(row) if row else None

    async def update_subscription_status(
        self, stripe_subscription_id: str, status: str,
        current_period_start: datetime = None,
        current_period_end: datetime = None,
        cancelled_at: datetime = None
    ):
        """Update subscription status (from Stripe webhook)"""
        async with self._conn() as conn:
            if current_period_start and current_period_end:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = $2, current_period_start = $3, current_period_end = $4,
                        cancelled_at = $5
                    WHERE stripe_subscription_id = $1
                    """,
                    stripe_subscription_id, status,
                    current_period_start, current_period_end, cancelled_at
                )
            else:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = $2, cancelled_at = $3
                    WHERE stripe_subscription_id = $1
                    """,
                    stripe_subscription_id, status, cancelled_at
                )

    async def get_active_subscriptions(self, limit: int = 100) -> List[dict]:
        """Get all active subscriptions (admin)"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT s.*, u.email, u.nome, u.role
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE s.status IN ('active', 'trialing')
                ORDER BY s.created_at DESC
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    # ============================================
    # INSTANCES (OpenClaw deploys)
    # ============================================

    async def create_instance(
        self,
        user_id: str,
        subscription_id: str,
        ai_provider: str = "proxy",
        ai_model: str = "gpt-5.2-codex",
        channel: str = "telegram"
    ) -> dict:
        """Create new OpenClaw instance"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO instances (
                    user_id, subscription_id, ai_provider, ai_model, channel
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                _uuid(user_id), _uuid(subscription_id),
                ai_provider, ai_model, channel
            )
            return dict(row)

    async def get_instance_by_user(self, user_id: str) -> Optional[dict]:
        """Get active instance for a user"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM instances
                WHERE user_id = $1 AND status IN ('provisioning', 'active')
                ORDER BY created_at DESC LIMIT 1
                """,
                _uuid(user_id)
            )
            return dict(row) if row else None

    async def get_instance_by_id(self, instance_id: str) -> Optional[dict]:
        """Get instance by ID"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM instances WHERE id = $1",
                _uuid(instance_id)
            )
            return dict(row) if row else None

    async def update_instance_status(self, instance_id: str, status: str):
        """Update instance status"""
        async with self._conn() as conn:
            await conn.execute(
                "UPDATE instances SET status = $2 WHERE id = $1",
                _uuid(instance_id), status
            )

    async def update_instance_config(
        self, instance_id: str,
        server_ip: str = None,
        hostname: str = None,
        ai_provider: str = None,
        ai_model: str = None,
        ai_api_key: str = None,
        telegram_bot_token: str = None,
        channel: str = None,
        config: dict = None,
        user_id: str = None
    ):
        """Update instance configuration. Encrypts sensitive fields."""
        updates = {}
        if server_ip is not None:
            updates["server_ip"] = server_ip
        if hostname is not None:
            updates["hostname"] = hostname
        if ai_provider is not None:
            updates["ai_provider"] = ai_provider
        if ai_model is not None:
            updates["ai_model"] = ai_model
        if channel is not None:
            updates["channel"] = channel
        if config is not None:
            updates["config"] = json.dumps(config)

        # Encrypt sensitive fields
        enc_updates = {}
        if ai_api_key is not None and user_id:
            enc_updates["ai_api_key_encrypted"] = encrypt_data(ai_api_key, user_id)
        if telegram_bot_token is not None and user_id:
            enc_updates["telegram_bot_token_encrypted"] = encrypt_data(telegram_bot_token, user_id)

        all_updates = {**updates, **enc_updates}
        if not all_updates:
            return

        set_clauses = []
        values = []
        for i, (key, val) in enumerate(all_updates.items(), 1):
            set_clauses.append(f"{key} = ${i}")
            values.append(val)

        values.append(_uuid(instance_id))

        async with self._conn() as conn:
            await conn.execute(
                f"""
                UPDATE instances
                SET {', '.join(set_clauses)}
                WHERE id = ${len(values)}
                """,
                *values
            )

    async def update_instance_heartbeat(self, instance_id: str):
        """Update instance heartbeat timestamp"""
        async with self._conn() as conn:
            await conn.execute(
                "UPDATE instances SET last_heartbeat = NOW() WHERE id = $1",
                _uuid(instance_id)
            )

    async def get_all_instances(self, status: str = None, limit: int = 100) -> List[dict]:
        """Get all instances (admin)"""
        async with self._conn() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT i.*, u.email, u.nome
                    FROM instances i
                    JOIN users u ON i.user_id = u.id
                    WHERE i.status = $1
                    ORDER BY i.created_at DESC LIMIT $2
                    """,
                    status, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT i.*, u.email, u.nome
                    FROM instances i
                    JOIN users u ON i.user_id = u.id
                    ORDER BY i.created_at DESC LIMIT $1
                    """,
                    limit
                )
            return [dict(row) for row in rows]

    # ============================================
    # DEPLOYMENTS (instance lifecycle)
    # ============================================

    async def create_deployment(
        self, instance_id: str, action: str
    ) -> dict:
        """Create deployment record"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO deployments (instance_id, action, status)
                VALUES ($1, $2, 'pending')
                RETURNING *
                """,
                _uuid(instance_id), action
            )
            return dict(row)

    async def update_deployment_status(
        self, deployment_id: str, status: str, error_log: str = None
    ):
        """Update deployment status"""
        async with self._conn() as conn:
            if status in ("completed", "failed"):
                await conn.execute(
                    """
                    UPDATE deployments
                    SET status = $2, error_log = $3, completed_at = NOW()
                    WHERE id = $1
                    """,
                    _uuid(deployment_id), status, error_log
                )
            else:
                await conn.execute(
                    "UPDATE deployments SET status = $2 WHERE id = $1",
                    _uuid(deployment_id), status
                )

    async def get_instance_deployments(self, instance_id: str, limit: int = 20) -> List[dict]:
        """Get deployment history for an instance"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM deployments
                WHERE instance_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                _uuid(instance_id), limit
            )
            return [dict(row) for row in rows]

    # ============================================
    # HOSTINGER PROVISIONING
    # ============================================

    async def update_instance_hostinger(
        self,
        instance_id: str,
        hostinger_vm_id: int,
        hostinger_datacenter: str,
    ):
        """Store Hostinger VM ID and datacenter on an instance."""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE instances
                SET hostinger_vm_id = $2, hostinger_datacenter = $3
                WHERE id = $1
                """,
                _uuid(instance_id), hostinger_vm_id, hostinger_datacenter
            )

    async def update_deployment_external(
        self,
        deployment_id: str,
        external_action_id: int,
        external_provider: str = "hostinger",
    ):
        """Store external action ID on a deployment record."""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE deployments
                SET external_action_id = $2, external_provider = $3
                WHERE id = $1
                """,
                _uuid(deployment_id), external_action_id, external_provider
            )

    async def get_instance_by_hostinger_vm(self, vm_id: int) -> Optional[dict]:
        """Look up instance by Hostinger VM ID."""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM instances WHERE hostinger_vm_id = $1",
                vm_id,
            )
            return dict(row) if row else None
