"""
ClaWin1Click - Seguranca e Criptografia
Sistema de autenticacao e protecao de dados sensiveis
Forked from SegurIA — isolated salt for ClaWin1Click data isolation
"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
from base64 import b64encode

_security_logger = logging.getLogger("clawin.security")

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import jwt

from app.config import SECRET_KEY, ENCRYPTION_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_HOURS, JWT_REFRESH_TOKEN_DAYS


# ============================================
# PASSWORD HASHING
# ============================================

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ============================================
# JWT TOKENS
# ============================================

def create_access_token(user_id: str, email: str, role: str = "lead") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_ACCESS_TOKEN_HOURS),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================
# DATA ENCRYPTION (Fernet - AES 128)
# ============================================

def _get_fernet_key(user_salt: str = "") -> bytes:
    combined = f"{ENCRYPTION_KEY}{user_salt}".encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        # Salt unico para ClaWin1Click — dados NUNCA sao compativeis com SegurIA ou AiSyster
        salt=b"clawin_salt_v1",
        iterations=100000,
    )
    key = b64encode(kdf.derive(combined))
    return key


def encrypt_data(data: str, user_id: str = "") -> bytes:
    if not data:
        return b""
    key = _get_fernet_key(user_id)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode('utf-8'))
    return encrypted


def decrypt_data(encrypted_data: bytes, user_id: str = "") -> str:
    if not encrypted_data:
        return ""
    try:
        key = _get_fernet_key(user_id)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
    except Exception as e:
        _security_logger.error(f"[DECRYPT_ERROR] Failed to decrypt for user {user_id[:8] if user_id else 'N/A'}...: {type(e).__name__}")
        return "[Dados nao puderam ser recuperados]"


# ============================================
# UTILITY FUNCTIONS
# ============================================

def generate_secure_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_for_audit(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================
# RATE LIMITING
# ============================================

import time
import logging

_rate_logger = logging.getLogger("clawin.ratelimit")


class RateLimiter:
    """
    Sliding window rate limiter.
    Primary: Redis sorted sets (shared across processes).
    Fallback: In-memory dict (per-process, used when Redis is unavailable).
    """

    def __init__(self):
        self._requests: dict[str, list[float]] = {}

    def _get_redis(self):
        """Lazy import to avoid circular dependency at module load time."""
        try:
            from app.redis_client import get_redis
            return get_redis()
        except ImportError:
            return None

    async def _redis_is_allowed(self, r, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        pipe = r.pipeline()
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {f"{now}:{secrets.token_hex(4)}": now})
        pipe.expire(redis_key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]
        if current_count >= max_requests:
            return False
        return True

    async def _redis_get_remaining(self, r, key: str, max_requests: int, window_seconds: int) -> int:
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        pipe = r.pipeline()
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zcard(redis_key)
        results = await pipe.execute()

        current_count = results[1]
        return max(0, max_requests - current_count)

    def _memory_is_allowed(self, user_id: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        if user_id not in self._requests:
            self._requests[user_id] = []

        self._requests[user_id] = [
            req_time for req_time in self._requests[user_id]
            if req_time > window_start
        ]

        if len(self._requests[user_id]) >= max_requests:
            return False

        self._requests[user_id].append(now)
        return True

    def _memory_get_remaining(self, user_id: str, max_requests: int, window_seconds: int) -> int:
        now = time.time()
        window_start = now - window_seconds

        if user_id not in self._requests:
            return max_requests

        recent = [
            req_time for req_time in self._requests[user_id]
            if req_time > window_start
        ]
        return max(0, max_requests - len(recent))

    async def is_allowed(self, user_id: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if request is allowed. Tries Redis first, falls back to memory."""
        r = self._get_redis()
        if r:
            try:
                return await self._redis_is_allowed(r, user_id, max_requests, window_seconds)
            except Exception as e:
                _rate_logger.warning("[RATE_LIMIT] Redis error, using fallback: %s", e)
        return self._memory_is_allowed(user_id, max_requests, window_seconds)

    async def get_remaining(self, user_id: str, max_requests: int = 60, window_seconds: int = 60) -> int:
        """Get remaining requests. Tries Redis first, falls back to memory."""
        r = self._get_redis()
        if r:
            try:
                return await self._redis_get_remaining(r, user_id, max_requests, window_seconds)
            except Exception as e:
                _rate_logger.warning("[RATE_LIMIT] Redis error, using fallback: %s", e)
        return self._memory_get_remaining(user_id, max_requests, window_seconds)


rate_limiter = RateLimiter()
