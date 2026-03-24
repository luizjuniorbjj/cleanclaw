"""
app.core.db — Composed Database class from domain-specific mixins.

The Database class inherits from all mixins + DatabaseBase,
providing the same API as the original monolithic class.
"""

from app.core.db._base import DatabaseBase, UUIDEncoder, _uuid
from app.core.db._users import UsersMixin
from app.core.db._conversations import ConversationsMixin
from app.core.db._memories import MemoriesMixin
from app.core.db._subscriptions import SubscriptionsMixin
from app.core.db._affiliates import AffiliatesMixin
from app.core.db._platform import PlatformMixin


class Database(
    UsersMixin,
    ConversationsMixin,
    MemoriesMixin,
    SubscriptionsMixin,
    AffiliatesMixin,
    PlatformMixin,
    DatabaseBase,
):
    """Composed Database class — all methods available via mixins."""
    pass


__all__ = ["Database", "UUIDEncoder", "_uuid"]
