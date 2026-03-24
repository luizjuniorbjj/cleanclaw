"""Type conversion helpers for asyncpg bindings."""
from datetime import date, time, datetime
from typing import Optional, Union


def to_date(val: Optional[Union[str, date]]) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val))


def to_time(val: Optional[Union[str, time]]) -> Optional[time]:
    if val is None:
        return None
    if isinstance(val, time):
        return val
    parts = str(val).split(":")
    return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
