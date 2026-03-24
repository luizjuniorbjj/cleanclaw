"""
AffiliatesMixin — AFFILIATES + REFERRALS + AFFILIATE PAYOUTS sections.
"""

import logging
from typing import Optional, List

from app.core.db._base import _uuid
from app.security import encrypt_data

logger = logging.getLogger("clawin.database")


class AffiliatesMixin:
    """Affiliate, referral, and payout database operations."""

    # ============================================
    # AFFILIATES
    # ============================================

    async def create_affiliate(self, user_id: str, slug: str, commission_rate: float = 0.30) -> dict:
        """Create affiliate record and upgrade user role"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliates (user_id, slug, commission_rate)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                _uuid(user_id), slug, commission_rate
            )

            # Upgrade user role to affiliate (if not already admin)
            await conn.execute(
                "UPDATE users SET role = 'affiliate' WHERE id = $1 AND role != 'admin'",
                _uuid(user_id)
            )

            return dict(row)

    async def get_affiliate_by_user(self, user_id: str) -> Optional[dict]:
        """Get affiliate record for a user"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM affiliates WHERE user_id = $1",
                _uuid(user_id)
            )
            return dict(row) if row else None

    async def get_affiliate_by_user_or_id(self, identifier: str) -> Optional[dict]:
        """Get affiliate by affiliate_id or user_id"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM affiliates WHERE id = $1 OR user_id = $1",
                _uuid(identifier)
            )
            return dict(row) if row else None

    async def get_affiliate_by_slug(self, slug: str) -> Optional[dict]:
        """Get affiliate by slug (for referral tracking)"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM affiliates WHERE slug = $1 AND status = 'active'",
                slug
            )
            return dict(row) if row else None

    async def get_affiliate_stats(self, affiliate_id: str) -> dict:
        """Get stats for an affiliate (referrals, earnings)"""
        aff_uuid = _uuid(affiliate_id)
        async with self._conn() as conn:
            total_referrals = await conn.fetchval(
                "SELECT COUNT(*) FROM referrals WHERE affiliate_id = $1",
                aff_uuid
            )
            active_referrals = await conn.fetchval(
                "SELECT COUNT(*) FROM referrals WHERE affiliate_id = $1 AND status = 'active'",
                aff_uuid
            )
            total_earned = await conn.fetchval(
                "SELECT COALESCE(SUM(commission_amount), 0) FROM referrals WHERE affiliate_id = $1",
                aff_uuid
            )
            total_paid = await conn.fetchval(
                """SELECT COALESCE(SUM(amount), 0) FROM affiliate_payouts
                WHERE affiliate_id = $1 AND status = 'completed'""",
                aff_uuid
            )
            return {
                "total_referrals": total_referrals or 0,
                "active_referrals": active_referrals or 0,
                "total_earned": float(total_earned or 0),
                "total_paid": float(total_paid or 0),
                "balance": float((total_earned or 0) - (total_paid or 0))
            }

    async def update_affiliate_payout_info(
        self, affiliate_id: str, payout_method: str, payout_details: str, user_id: str
    ):
        """Update affiliate payout method (encrypted)"""
        encrypted = encrypt_data(payout_details, user_id)
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE affiliates
                SET payout_method = $2, payout_details_encrypted = $3
                WHERE id = $1
                """,
                _uuid(affiliate_id), payout_method, encrypted
            )

    async def get_all_affiliates(self, limit: int = 100) -> List[dict]:
        """Get all affiliates (admin)"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT a.*, u.email, u.nome
                FROM affiliates a
                JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    # ============================================
    # REFERRALS
    # ============================================

    async def create_referral(
        self,
        affiliate_id: str,
        referred_user_id: str,
        subscription_id: str = None
    ) -> dict:
        """Create referral record"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO referrals (affiliate_id, referred_user_id, subscription_id)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                _uuid(affiliate_id), _uuid(referred_user_id),
                _uuid(subscription_id) if subscription_id else None
            )
            return dict(row)

    async def update_referral_status(
        self, referral_id: str, status: str, commission_amount: float = None
    ):
        """Update referral status and commission"""
        async with self._conn() as conn:
            if commission_amount is not None:
                await conn.execute(
                    """
                    UPDATE referrals SET status = $2, commission_amount = $3
                    WHERE id = $1
                    """,
                    _uuid(referral_id), status, commission_amount
                )
            else:
                await conn.execute(
                    "UPDATE referrals SET status = $2 WHERE id = $1",
                    _uuid(referral_id), status
                )

    async def get_referrals_by_affiliate(self, affiliate_id: str, limit: int = 50) -> List[dict]:
        """Get referrals for an affiliate"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT r.*, u.email, u.nome
                FROM referrals r
                JOIN users u ON r.referred_user_id = u.id
                WHERE r.affiliate_id = $1
                ORDER BY r.created_at DESC LIMIT $2
                """,
                _uuid(affiliate_id), limit
            )
            return [dict(row) for row in rows]

    async def get_referral_by_user(self, referred_user_id: str) -> Optional[dict]:
        """Check if a user was referred"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM referrals WHERE referred_user_id = $1",
                _uuid(referred_user_id)
            )
            return dict(row) if row else None

    async def add_commission(self, affiliate_id: str, amount: float):
        """Add commission to affiliate totals"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE affiliates SET total_earned = total_earned + $2
                WHERE id = $1
                """,
                _uuid(affiliate_id), amount
            )

    # ============================================
    # AFFILIATE PAYOUTS
    # ============================================

    async def create_payout(
        self, affiliate_id: str, amount: float, method: str, reference: str = None
    ) -> dict:
        """Create payout record"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliate_payouts (affiliate_id, amount, method, reference)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                _uuid(affiliate_id), amount, method, reference
            )
            return dict(row)

    async def update_payout_status(self, payout_id: str, status: str):
        """Update payout status"""
        async with self._conn() as conn:
            if status == "completed":
                await conn.execute(
                    """
                    UPDATE affiliate_payouts
                    SET status = $2, processed_at = NOW()
                    WHERE id = $1
                    """,
                    _uuid(payout_id), status
                )
                # Also update affiliate total_paid
                payout = await conn.fetchrow(
                    "SELECT affiliate_id, amount FROM affiliate_payouts WHERE id = $1",
                    _uuid(payout_id)
                )
                if payout:
                    await conn.execute(
                        "UPDATE affiliates SET total_paid = total_paid + $2 WHERE id = $1",
                        payout["affiliate_id"], payout["amount"]
                    )
            else:
                await conn.execute(
                    "UPDATE affiliate_payouts SET status = $2 WHERE id = $1",
                    _uuid(payout_id), status
                )

    async def get_affiliate_payouts(self, affiliate_id: str, limit: int = 20) -> List[dict]:
        """Get payout history for an affiliate"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM affiliate_payouts
                WHERE affiliate_id = $1
                ORDER BY created_at DESC LIMIT $2
                """,
                _uuid(affiliate_id), limit
            )
            return [dict(row) for row in rows]

    async def update_affiliate_wallet(
        self, affiliate_id: str, wallet_address_encrypted: bytes,
        wallet_network: str
    ):
        """Update affiliate crypto wallet (encrypted)"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE affiliates
                SET wallet_address_encrypted = $2, wallet_network = $3,
                    payout_method = 'crypto'
                WHERE id = $1
                """,
                _uuid(affiliate_id), wallet_address_encrypted, wallet_network
            )

    async def create_crypto_payout(
        self, affiliate_id: str, amount: float,
        network: str, token: str, tx_hash: str = None
    ) -> dict:
        """Create crypto payout record"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO affiliate_payouts
                    (affiliate_id, amount, method, network, token, tx_hash, status)
                VALUES ($1, $2, 'crypto', $3, $4, $5, $6)
                RETURNING *
                """,
                _uuid(affiliate_id), amount, network, token, tx_hash,
                "completed" if tx_hash else "pending"
            )
            return dict(row)

    async def confirm_crypto_payout(self, payout_id: str, tx_hash: str):
        """Confirm a pending crypto payout with transaction hash"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE affiliate_payouts
                SET tx_hash = $2, status = 'completed', processed_at = NOW()
                WHERE id = $1
                """,
                _uuid(payout_id), tx_hash
            )
            payout = await conn.fetchrow(
                "SELECT affiliate_id, amount FROM affiliate_payouts WHERE id = $1",
                _uuid(payout_id)
            )
            if payout:
                await conn.execute(
                    "UPDATE affiliates SET total_paid = total_paid + $2 WHERE id = $1",
                    payout["affiliate_id"], payout["amount"]
                )

    async def get_pending_payouts(self, limit: int = 50) -> List[dict]:
        """Get all pending payouts (admin)"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT ap.*, a.slug, a.wallet_network,
                       a.wallet_address_encrypted, a.user_id,
                       u.email, u.nome
                FROM affiliate_payouts ap
                JOIN affiliates a ON ap.affiliate_id = a.id
                JOIN users u ON a.user_id = u.id
                WHERE ap.status = 'pending'
                ORDER BY ap.created_at ASC LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    async def get_affiliates_for_payout(self, min_balance: float) -> List[dict]:
        """Get affiliates with crypto wallet and balance >= threshold"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT a.*, u.email, u.nome,
                       (a.total_earned - a.total_paid) as balance
                FROM affiliates a
                JOIN users u ON a.user_id = u.id
                WHERE a.status = 'active'
                  AND a.payout_method = 'crypto'
                  AND a.wallet_address_encrypted IS NOT NULL
                  AND (a.total_earned - a.total_paid) >= $1
                """,
                min_balance
            )
            return [dict(row) for row in rows]
