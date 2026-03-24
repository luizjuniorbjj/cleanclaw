"""
ConversationsMixin — CONVERSATIONS + MESSAGES + ADMIN CONVERSATIONS sections.
"""

import logging
from typing import Optional, List

from app.core.db._base import _uuid
from app.security import encrypt_data, decrypt_data

logger = logging.getLogger("clawin.database")


class ConversationsMixin:
    """Conversation and message database operations."""

    # ============================================
    # CONVERSATIONS
    # ============================================

    async def create_conversation(
        self,
        user_id: str,
        channel: str = "web"
    ) -> dict:
        """Create new conversation"""
        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversations (user_id, channel)
                VALUES ($1, $2)
                RETURNING *
                """,
                _uuid(user_id), channel
            )
            return dict(row)

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str = None
    ) -> Optional[dict]:
        """Get conversation by ID with optional ownership validation"""
        async with self._conn() as conn:
            if user_id:
                row = await conn.fetchrow(
                    "SELECT * FROM conversations WHERE id = $1 AND user_id = $2",
                    _uuid(conversation_id), _uuid(user_id)
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM conversations WHERE id = $1",
                    _uuid(conversation_id)
                )
            return dict(row) if row else None

    async def get_recent_conversations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[dict]:
        """Get recent conversations for a user"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM conversations
                WHERE user_id = $1 AND is_archived = FALSE
                ORDER BY last_message_at DESC
                LIMIT $2
                """,
                _uuid(user_id), limit
            )
            return [dict(row) for row in rows]

    async def update_conversation_summary(self, conversation_id: str, resumo: str):
        """Update conversation summary"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE conversations
                SET resumo = $2, last_message_at = NOW()
                WHERE id = $1
                """,
                _uuid(conversation_id), resumo
            )

    async def archive_conversation(self, conversation_id: str, user_id: str):
        """Archive a conversation"""
        async with self._conn() as conn:
            await conn.execute(
                """
                UPDATE conversations SET is_archived = TRUE
                WHERE id = $1 AND user_id = $2
                """,
                _uuid(conversation_id), _uuid(user_id)
            )

    # ============================================
    # MESSAGES
    # ============================================

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: str = None
    ) -> dict:
        """Save encrypted message"""
        conv_uuid = _uuid(conversation_id)
        # Use conversation owner for encryption key
        if not user_id:
            async with self._conn() as conn:
                conv = await conn.fetchrow(
                    "SELECT user_id FROM conversations WHERE id = $1", conv_uuid
                )
                user_id = str(conv["user_id"]) if conv else "system"

        encrypted_content = encrypt_data(content, user_id)

        async with self._conn() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (conversation_id, role, content_encrypted)
                VALUES ($1, $2, $3)
                RETURNING id, role, created_at
                """,
                conv_uuid, role, encrypted_content
            )

            # Update conversation timestamp
            await conn.execute(
                "UPDATE conversations SET last_message_at = NOW() WHERE id = $1",
                conv_uuid
            )

            return dict(row)

    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[dict]:
        """Get decrypted messages for a conversation"""
        async with self._conn() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                _uuid(conversation_id), limit
            )

            messages = []
            for row in rows:
                msg = dict(row)
                try:
                    msg["content"] = decrypt_data(msg["content_encrypted"], user_id)
                except Exception:
                    msg["content"] = "(decryption failed)"
                del msg["content_encrypted"]
                messages.append(msg)

            return messages

    # ============================================
    # ADMIN CONVERSATIONS (Admin Chat View)
    # ============================================

    async def get_all_conversations(
        self, search: str = None, status: str = None, limit: int = 50
    ) -> List[dict]:
        """List all conversations with user info (admin view)"""
        async with self._conn() as conn:
            where_clauses = ["1=1"]
            params: list = []
            idx = 1

            if status == "archived":
                where_clauses.append("c.is_archived = TRUE")
            else:
                where_clauses.append("c.is_archived = FALSE")

            if search:
                where_clauses.append(
                    f"(COALESCE(p.nome, u.email) ILIKE ${idx})"
                )
                params.append(f"%{search}%")
                idx += 1

            params.append(limit)

            rows = await conn.fetch(f"""
                SELECT c.id, c.user_id, c.last_message_at,
                       c.channel, c.is_archived, c.resumo,
                       COALESCE(p.nome, u.email) AS client_name,
                       u.email AS client_email
                FROM conversations c
                JOIN users u ON c.user_id = u.id
                LEFT JOIN user_profiles p ON p.user_id = u.id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY c.last_message_at DESC NULLS LAST
                LIMIT ${idx}
            """, *params)

            results = []
            for row in rows:
                conv = dict(row)
                conv["id"] = str(conv["id"])
                conv["user_id"] = str(conv["user_id"])
                if conv.get("last_message_at"):
                    conv["last_message_at"] = conv["last_message_at"].isoformat()

                # Get last message preview
                last_msg = await conn.fetchrow("""
                    SELECT role, content_encrypted FROM messages
                    WHERE conversation_id = $1
                    ORDER BY created_at DESC LIMIT 1
                """, row["id"])
                if last_msg:
                    try:
                        full = decrypt_data(last_msg["content_encrypted"], str(row["user_id"]))
                        conv["last_message"] = full[:100]
                    except Exception:
                        conv["last_message"] = "(encrypted)"
                    conv["last_message_role"] = last_msg["role"]
                else:
                    conv["last_message"] = ""
                    conv["last_message_role"] = None
                results.append(conv)

            return results

    async def get_admin_conversation_messages(
        self, conversation_id: str, limit: int = 100
    ) -> List[dict]:
        """Get decrypted messages for admin view"""
        async with self._conn() as conn:
            conv = await conn.fetchrow(
                "SELECT user_id FROM conversations WHERE id = $1",
                _uuid(conversation_id)
            )
            if not conv:
                return []

            user_id = str(conv["user_id"])

            rows = await conn.fetch("""
                SELECT id, role, content_encrypted, created_at FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
            """, _uuid(conversation_id), limit)

            messages = []
            for row in rows:
                try:
                    content = decrypt_data(row["content_encrypted"], user_id)
                except Exception:
                    content = "(decryption failed)"
                messages.append({
                    "id": str(row["id"]),
                    "role": row["role"],
                    "content": content,
                    "created_at": row["created_at"].isoformat()
                })

            return messages
