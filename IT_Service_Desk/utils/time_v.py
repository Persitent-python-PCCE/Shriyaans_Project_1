from datetime import datetime, timedelta, timezone


LOCAL_TIMEZONE = timezone(timedelta(hours=5, minutes=30), name="IST")


def to_local_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(LOCAL_TIMEZONE)
