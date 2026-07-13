"""Calendar-day boundaries for digest selection."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class InvalidTimezoneError(ValueError):
    pass


def utc_day_bounds(day: date, timezone_name: str) -> tuple[datetime, datetime]:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise InvalidTimezoneError("invalid digest timezone") from None
    local_start = datetime.combine(day, time.min, timezone)
    local_end = datetime.combine(day + timedelta(days=1), time.min, timezone)
    return local_start.astimezone(UTC), local_end.astimezone(UTC)


def previous_local_day(now: datetime, timezone_name: str) -> date:
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        raise InvalidTimezoneError("invalid digest timezone") from None
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    return now.astimezone(timezone).date() - timedelta(days=1)
