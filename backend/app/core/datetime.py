from datetime import date, datetime, time, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))


def now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_client_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=BEIJING_TZ)
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def beijing_date(value: datetime | None = None) -> date:
    if value is None:
        return datetime.now(BEIJING_TZ).date()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BEIJING_TZ).date()


def format_beijing_time(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BEIJING_TZ).strftime("%H:%M")


def day_bounds_utc(target_date: date) -> tuple[datetime, datetime]:
    start = datetime.combine(target_date, time.min, tzinfo=BEIJING_TZ)
    end = datetime.combine(target_date + timedelta(days=1), time.min, tzinfo=BEIJING_TZ)
    return (
        start.astimezone(timezone.utc).replace(tzinfo=None),
        end.astimezone(timezone.utc).replace(tzinfo=None),
    )

