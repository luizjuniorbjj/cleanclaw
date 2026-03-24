"""
MemoriesMixin — MEMORIES + PSYCHOLOGICAL PROFILE + LEARNING sections.
"""

import json
import logging
from typing import Optional, List

from app.core.db._base import _uuid

logger = logging.getLogger("clawin.database")


class MemoriesMixin:
    """Memory, psychological profile, and learning database operations."""

    # ============================================
    # USER MEMORIES (Intelligent Memory System)
    # ============================================

    # Semantic conflict fields for ClaWin1Click domain
    SEMANTIC_CONFLICT_FIELDS = {
        "SUBSCRIPTION": {
            "keywords": ["subscri", "plan", "paying", "paid", "cancel", "renew",
                         "monthly", "billing", "stripe", "charge"],
            "categories": ["SUBSCRIPTION", "BILLING", "EVENT"]
        },
        "INSTANCE": {
            "keywords": ["instance", "deploy", "server", "bot", "telegram", "discord",
                         "whatsapp", "openclaw", "channel", "model", "provider",
                         "claude", "gpt", "gemini", "anthropic", "openai", "google"],
            "categories": ["INSTANCE", "EVENT"]
        },
        "LOCATION": {
            "keywords": ["lives", "living", "moved", "city", "state", "country",
                         "brazil", "brasil", "portugal", "usa"],
            "categories": ["IDENTITY", "EVENT"]
        },
        "OCCUPATION": {
            "keywords": ["works", "working", "job", "occupation", "employed",
                         "freelancer", "developer", "empresa", "company"],
            "categories": ["IDENTITY", "EVENT"]
        },
    }

    @staticmethod
    def _keyword_match(keyword: str, text: str) -> bool:
        """Match keyword in text (word boundary for single words, contains for multi-word)"""
        import re
        if " " in keyword:
            return keyword in text
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))

    def _detect_semantic_field(self, fato: str, categoria: str) -> Optional[str]:
        """Detect which semantic field a fact belongs to"""
        fato_lower = fato.lower()
        for field_name, field_info in self.SEMANTIC_CONFLICT_FIELDS.items():
            if categoria not in field_info["categories"]:
                continue
            for kw in field_info["keywords"]:
                if self._keyword_match(kw, fato_lower):
                    return field_name
        return None

    async def _find_conflicting_memories(
        self, conn, user_id, categoria: str, semantic_field: str
    ) -> List[dict]:
        """Find memories that may conflict with a new memory"""
        field_info = self.SEMANTIC_CONFLICT_FIELDS.get(semantic_field)
        if not field_info:
            return []

        rows = await conn.fetch(
            """
            SELECT id, fato, categoria FROM user_memories
            WHERE user_id = $1
            AND categoria = ANY($2)
            AND status = 'active'
            """,
            user_id, field_info["categories"]
        )

        conflicting = []
        for row in rows:
            fato_lower = row["fato"].lower()
            for kw in field_info["keywords"]:
                if self._keyword_match(kw, fato_lower):
                    conflicting.append(dict(row))
                    break

        return conflicting

    # Categories that ALWAYS appear in context (pinned)
    PINNED_CATEGORIES = {"IDENTITY", "SUBSCRIPTION", "INSTANCE", "PREFERENCE"}

    # Maximum active memories per scored category
    CATEGORY_CAPS = {"SUPPORT": 5, "USAGE": 8, "BILLING": 10, "EVENT": 15}

    async def save_memory(
        self,
        user_id: str,
        categoria: str,
        fato: str,
        importancia: float = 0.50,
        source: str = "extraction",
        confianca: float = 0.80,
        action: str = "upsert"
    ) -> dict:
        """
        Save a fact to user's permanent memory.
        Actions: upsert (create/increment), supersede (replace old)
        """
        user_uuid = _uuid(user_id)
        is_pinned = categoria in self.PINNED_CATEGORIES

        async with self._conn() as conn:
            # Normalize fact for dedup
            fato_norm = await conn.fetchval("SELECT normalize_text($1)", fato)

            # Detect semantic field for conflicts
            semantic_field = self._detect_semantic_field(fato, categoria)

            # Find and supersede conflicting memories
            superseded_ids = []
            if semantic_field:
                conflicting = await self._find_conflicting_memories(
                    conn, user_uuid, categoria, semantic_field
                )
                for conf in conflicting:
                    conf_norm = await conn.fetchval("SELECT normalize_text($1)", conf["fato"])
                    if conf_norm != fato_norm:
                        await conn.execute(
                            """UPDATE user_memories
                            SET status = 'superseded'
                            WHERE id = $1""",
                            conf["id"]
                        )
                        superseded_ids.append(str(conf["id"]))
                        logger.info(f"[MEMORY] Superseded: '{conf['fato']}' -> '{fato}'")

            # Check for existing identical memory (dedup)
            existing = await conn.fetchrow(
                """
                SELECT id, mentions FROM user_memories
                WHERE user_id = $1
                AND categoria = $2
                AND fato_normalizado = $3
                AND status = 'active'
                """,
                user_uuid, categoria, fato_norm
            )

            if existing:
                if action == "supersede":
                    await conn.execute(
                        "UPDATE user_memories SET status = 'superseded' WHERE id = $1",
                        existing["id"]
                    )
                else:
                    # Upsert: increment mentions
                    await conn.execute(
                        """
                        UPDATE user_memories
                        SET mentions = mentions + 1,
                            confianca = GREATEST(confianca, $2)
                        WHERE id = $1
                        """,
                        existing["id"], confianca
                    )
                    return {
                        "id": str(existing["id"]),
                        "updated": True,
                        "mentions": existing["mentions"] + 1,
                        "superseded": superseded_ids
                    }

            # Apply category caps before inserting (scored categories only)
            cap = self.CATEGORY_CAPS.get(categoria)
            if cap:
                active_count = await conn.fetchval(
                    """SELECT COUNT(*) FROM user_memories
                    WHERE user_id = $1 AND categoria = $2 AND status = 'active'""",
                    user_uuid, categoria
                )
                if active_count >= cap:
                    least_important = await conn.fetchrow(
                        """SELECT id, importancia FROM user_memories
                        WHERE user_id = $1 AND categoria = $2 AND status = 'active'
                        ORDER BY importancia ASC, mentions ASC
                        LIMIT 1""",
                        user_uuid, categoria
                    )
                    if least_important and importancia >= float(least_important["importancia"] or 0):
                        await conn.execute(
                            "UPDATE user_memories SET status = 'superseded' WHERE id = $1",
                            least_important["id"]
                        )

            # Create new memory
            row = await conn.fetchrow(
                """
                INSERT INTO user_memories (
                    user_id, categoria, fato, importancia,
                    confianca, source, is_pinned
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                user_uuid, categoria, fato, importancia,
                confianca, source, is_pinned
            )

            new_id = row["id"]

            # Update superseded rows to point to the new memory
            if superseded_ids:
                for sid in superseded_ids:
                    await conn.execute(
                        "UPDATE user_memories SET superseded_by = $1 WHERE id = $2",
                        new_id, _uuid(sid)
                    )

            return {"id": str(new_id), "created": True, "superseded": superseded_ids}

    async def get_user_memories(
        self,
        user_id: str,
        categoria: str = None,
        limit: int = 50
    ) -> List[dict]:
        """Get user memories, ordered by importance"""
        user_uuid = _uuid(user_id)
        async with self._conn() as conn:
            if categoria:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND categoria = $2 AND status = 'active'
                    ORDER BY importancia DESC, updated_at DESC
                    LIMIT $3
                    """,
                    user_uuid, categoria, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM user_memories
                    WHERE user_id = $1 AND status = 'active'
                    ORDER BY importancia DESC, updated_at DESC
                    LIMIT $2
                    """,
                    user_uuid, limit
                )
            return [dict(row) for row in rows]

    async def get_relevant_memories(
        self,
        user_id: str,
        current_message: str = "",
        top_k: int = 20
    ) -> List[dict]:
        """
        Two-tier memory retrieval:
        - Tier 1 (Pinned): IDENTITY, SUBSCRIPTION, INSTANCE, PREFERENCE — always present
        - Tier 2 (Scored): SUPPORT, USAGE, BILLING, EVENT — Top-K by relevance
        """
        user_uuid = _uuid(user_id)
        async with self._conn() as conn:
            # TIER 1: Pinned categories
            pinned_rows = await conn.fetch(
                """
                SELECT *, 1.0 as final_score
                FROM user_memories
                WHERE user_id = $1 AND status = 'active'
                  AND categoria IN ('IDENTITY', 'SUBSCRIPTION', 'INSTANCE', 'PREFERENCE')
                ORDER BY importancia DESC, mentions DESC
                LIMIT 15
                """,
                user_uuid
            )
            pinned = [dict(row) for row in pinned_rows]
            pinned_ids = {row["id"] for row in pinned}

            # TIER 2: Scored categories
            remaining_slots = max(top_k - len(pinned), 5)

            if current_message and len(current_message) > 5:
                scored_rows = await conn.fetch(
                    """
                    WITH scored_memories AS (
                        SELECT *,
                            COALESCE(
                                ts_rank(
                                    to_tsvector('english', fato),
                                    plainto_tsquery('english', $2)
                                ),
                                0
                            ) as text_score,
                            CASE
                                WHEN updated_at > NOW() - INTERVAL '1 day' THEN 1.0
                                WHEN updated_at > NOW() - INTERVAL '7 days' THEN 0.8
                                WHEN updated_at > NOW() - INTERVAL '30 days' THEN 0.5
                                ELSE 0.2
                            END as recency_score
                        FROM user_memories
                        WHERE user_id = $1 AND status = 'active'
                          AND categoria NOT IN ('IDENTITY', 'SUBSCRIPTION', 'INSTANCE', 'PREFERENCE')
                    )
                    SELECT *,
                        (
                            text_score * 0.35 +
                            (importancia::float) * 0.35 +
                            recency_score * 0.15 +
                            LEAST(mentions::float / 5.0, 1.0) * 0.15
                        ) as final_score
                    FROM scored_memories
                    ORDER BY final_score DESC
                    LIMIT $3
                    """,
                    user_uuid, current_message, remaining_slots
                )
            else:
                scored_rows = await conn.fetch(
                    """
                    SELECT *,
                        (
                            (importancia::float) * 0.5 +
                            CASE
                                WHEN updated_at > NOW() - INTERVAL '7 days' THEN 0.3
                                ELSE 0.1
                            END +
                            LEAST(mentions::float / 5.0, 1.0) * 0.2
                        ) as final_score
                    FROM user_memories
                    WHERE user_id = $1 AND status = 'active'
                      AND categoria NOT IN ('IDENTITY', 'SUBSCRIPTION', 'INSTANCE', 'PREFERENCE')
                    ORDER BY final_score DESC
                    LIMIT $2
                    """,
                    user_uuid, remaining_slots
                )

            scored = [dict(row) for row in scored_rows if row["id"] not in pinned_ids]
            return pinned + scored

    async def get_all_memories_formatted(
        self,
        user_id: str,
        current_message: str = "",
        top_k: int = 20
    ) -> str:
        """Returns relevant memories formatted for the AI prompt"""
        memories = await self.get_relevant_memories(user_id, current_message, top_k)

        if not memories:
            return ""

        by_category = {}
        for mem in memories:
            cat = mem["categoria"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(mem)

        category_labels = {
            "IDENTITY": "Who they are",
            "SUBSCRIPTION": "Subscription status",
            "INSTANCE": "OpenClaw instance",
            "PREFERENCE": "Preferences",
            "SUPPORT": "Support history",
            "USAGE": "Usage patterns",
            "BILLING": "Billing history",
            "EVENT": "Important events"
        }

        result = "=== WHAT YOU KNOW ABOUT THIS USER ===\n"

        pinned_order = ["IDENTITY", "SUBSCRIPTION", "INSTANCE", "PREFERENCE"]
        scored_order = ["SUPPORT", "USAGE", "BILLING", "EVENT"]

        for cat in pinned_order + scored_order:
            mems = by_category.get(cat)
            if not mems:
                continue
            label = category_labels.get(cat, cat)
            result += f"[{label}]\n"
            for mem in mems:
                result += f"  - {mem['fato']}"
                if mem["mentions"] > 1:
                    result += f" (mentioned {mem['mentions']}x)"
                result += "\n"
            result += "\n"

        result += "Use this information naturally in the conversation.\n"
        return result

    async def deactivate_memory(self, memory_id: str, user_id: str):
        """Deactivate a memory (soft delete)"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE user_memories
                SET status = 'deleted'
                WHERE id = $1 AND user_id = $2
                """,
                _uuid(memory_id), _uuid(user_id)
            )

    async def delete_all_user_memories(self, user_id: str) -> int:
        """Delete ALL memories for a user (CW-003 — right to deletion)"""
        async with self._conn() as conn:
            result = await conn.execute(
                "DELETE FROM user_memories WHERE user_id = $1",
                _uuid(user_id)
            )
            # asyncpg returns "DELETE N"
            return int(result.split()[-1]) if result else 0

    # ============================================
    # PSYCHOLOGICAL PROFILE
    # ============================================

    async def get_psychological_profile(self, user_id: str) -> Optional[dict]:
        """Get user's psychological profile"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_psychological_profile WHERE user_id = $1",
                _uuid(user_id)
            )
            return dict(row) if row else None

    async def save_psychological_profile(self, user_id: str, profile_data: dict) -> dict:
        """Save or update user's psychological profile"""
        user_uuid = _uuid(user_id)

        async with self._conn() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM user_psychological_profile WHERE user_id = $1",
                user_uuid
            )

            if existing:
                await conn.execute(
                    """
                    UPDATE user_psychological_profile SET
                        communication_style = COALESCE($2, communication_style),
                        processing_style = COALESCE($3, processing_style),
                        preferred_response_length = COALESCE($4, preferred_response_length),
                        emotional_baseline = COALESCE($5, emotional_baseline),
                        interaction_count = interaction_count + 1,
                        last_analysis = NOW()
                    WHERE user_id = $1
                    """,
                    user_uuid,
                    profile_data.get("communication_style"),
                    profile_data.get("processing_style"),
                    profile_data.get("preferred_response_length"),
                    profile_data.get("emotional_baseline")
                )
                return {"updated": True}
            else:
                await conn.execute(
                    """
                    INSERT INTO user_psychological_profile (
                        user_id, communication_style, processing_style,
                        preferred_response_length, emotional_baseline,
                        interaction_count, last_analysis
                    ) VALUES ($1, $2, $3, $4, $5, 1, NOW())
                    """,
                    user_uuid,
                    profile_data.get("communication_style", "DIRECT"),
                    profile_data.get("processing_style", "PRACTICAL"),
                    profile_data.get("preferred_response_length", "BRIEF"),
                    profile_data.get("emotional_baseline", "NEUTRAL")
                )
                return {"created": True}

    async def get_psychological_context(self, user_id: str) -> str:
        """Returns formatted psychological context for the AI prompt"""
        profile = await self.get_psychological_profile(user_id)
        if not profile:
            return ""

        context = "=== USER COMMUNICATION PROFILE ===\n"

        styles = {
            "DIRECT": "Prefers direct, to-the-point communication",
            "DETAILED": "Likes thorough explanations",
            "CASUAL": "Prefers casual, friendly tone",
            "TECHNICAL": "Comfortable with technical language"
        }
        if profile.get("communication_style"):
            context += f"Style: {styles.get(profile['communication_style'], profile['communication_style'])}\n"

        proc = {
            "PRACTICAL": "Wants practical solutions quickly",
            "ANALYTICAL": "Wants data and comparisons",
            "EXPLORATORY": "Likes to explore options before deciding"
        }
        if profile.get("processing_style"):
            context += f"Processing: {proc.get(profile['processing_style'], profile['processing_style'])}\n"

        lengths = {
            "BRIEF": "Prefers short, concise answers",
            "MODERATE": "Medium-length responses",
            "DETAILED": "Wants comprehensive explanations"
        }
        if profile.get("preferred_response_length"):
            context += f"Response length: {lengths.get(profile['preferred_response_length'], profile['preferred_response_length'])}\n"

        return context

    # ============================================
    # LEARNING INTERACTIONS
    # ============================================

    async def save_learning_interaction(
        self,
        user_id: str,
        conversation_id: str = None,
        strategy_used: str = None,
        feedback_type: str = None,
        feedback_score: float = None,
        context: dict = None
    ):
        """Save a learning interaction"""
        async with self._conn() as conn:
            await conn.execute(
                """
                INSERT INTO learning_interactions (
                    user_id, conversation_id,
                    strategy_used, feedback_type, feedback_score, context
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                _uuid(user_id),
                _uuid(conversation_id) if conversation_id else None,
                strategy_used, feedback_type, feedback_score,
                json.dumps(context or {})
            )

    async def get_strategy_scores(self, user_id: str) -> dict:
        """Get strategy effectiveness scores"""
        try:
            async with self._conn() as conn:
                rows = await conn.fetch(
                    """
                    SELECT strategy_used,
                           COUNT(*) as uses,
                           AVG(COALESCE(feedback_score, 0.5)) as score
                    FROM learning_interactions
                    WHERE user_id = $1
                      AND strategy_used IS NOT NULL
                    GROUP BY strategy_used
                    ORDER BY score DESC
                    """,
                    _uuid(user_id)
                )
                return {row["strategy_used"]: float(row["score"]) for row in rows}
        except Exception:
            return {}

    async def save_learning_feedback(
        self, user_id: str, feedback_type: str,
        strategy_used: str = None, context: dict = None
    ):
        """Save implicit learning feedback from user behavior"""
        try:
            await self.save_learning_interaction(
                user_id=user_id,
                strategy_used=strategy_used,
                feedback_type=feedback_type,
                context=context
            )
        except Exception:
            pass

    async def update_user_preferred_style(self, user_id: str, adjustments: dict):
        """Apply communication style adjustments"""
        try:
            async with self._conn() as conn:
                profile = await conn.fetchrow(
                    "SELECT id FROM user_psychological_profile WHERE user_id = $1",
                    _uuid(user_id)
                )
                if profile:
                    if "communication_style" in adjustments:
                        await conn.execute(
                            "UPDATE user_psychological_profile SET communication_style = $1 WHERE user_id = $2",
                            adjustments["communication_style"], _uuid(user_id)
                        )
                    if "processing_style" in adjustments:
                        await conn.execute(
                            "UPDATE user_psychological_profile SET processing_style = $1 WHERE user_id = $2",
                            adjustments["processing_style"], _uuid(user_id)
                        )
        except Exception:
            pass
