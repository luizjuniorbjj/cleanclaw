"""
DatabaseBase — connection pool, generic methods, helpers.
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, date
from uuid import UUID

import asyncpg

logger = logging.getLogger("clawin.database")


class UUIDEncoder(json.JSONEncoder):
    """JSON Encoder that supports UUID serialization"""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def _uuid(value) -> UUID:
    """Convert string to UUID if needed"""
    return UUID(value) if isinstance(value, str) else value


class DatabaseBase:
    """
    Single-platform database abstraction layer.
    No agency_id — all queries scoped by user_id only.
    """

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @asynccontextmanager
    async def _conn(self):
        """Acquire connection from pool"""
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    # ============================================
    # GENERIC DATABASE METHODS
    # ============================================

    async def fetch(self, query: str, *args):
        """Execute query and return all rows"""
        async with self._conn() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Execute query and return single row"""
        async with self._conn() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        """Execute query without returning rows"""
        async with self._conn() as conn:
            return await conn.execute(query, *args)
