from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Activity, Card, CardView, User


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
PERIOD_DAYS = {"week": 7, "month": 30, "year": 365}


def _as_naive(value: datetime) -> datetime:
    if getattr(value, "tzinfo", None) is not None:
        return value.replace(tzinfo=None)
    return value


def _as_date(value: datetime) -> datetime:
    naive = _as_naive(value)
    return naive.date() if hasattr(naive, "date") else naive


def period_window(period: str) -> tuple[datetime, datetime, datetime]:
    days = PERIOD_DAYS.get(period, 30)
    until = datetime.now(timezone.utc).replace(tzinfo=None)
    since = until - timedelta(days=days)
    previous_since = since - timedelta(days=days)
    return since, until, previous_since


def views_last_7_days(db: Session, user_id: int) -> list[dict]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=6)
    rows = db.execute(
        select(CardView.created_at)
        .join(Card, CardView.card_id == Card.id)
        .where(Card.author_id == user_id, CardView.created_at >= since)
    ).scalars().all()

    buckets = {(since.date() + timedelta(days=i)): 0 for i in range(7)}
    for created_at in rows:
        day = _as_date(created_at)
        if day in buckets:
            buckets[day] += 1

    series = []
    for day, value in buckets.items():
        series.append({"day": WEEKDAYS[day.weekday()], "value": value, "date": day.isoformat()})
    return series


def recent_activities(db: Session, user_id: int, limit: int = 8) -> list[Activity]:
    stmt = (
        select(Activity)
        .where(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _delta_label(current: int, previous: int) -> str:
    if previous <= 0:
        return "За выбранный период"
    percent = round((current - previous) / previous * 100)
    sign = "+" if percent > 0 else ""
    return f"{sign}{percent}% к прошлому периоду"


def build_stats(db: Session, user: User, period: str = "month") -> dict:
    from app.database.crud.cards import collected_for_author, count_active_for_author
    from app.database.crud.helps import helped_amount, helped_people_count

    since, until, previous_since = period_window(period)
    collected = collected_for_author(db, user.id, since=since, until=until)
    previous = collected_for_author(db, user.id, since=previous_since, until=since)
    helped_people = helped_people_count(db, user.id, since=since, until=until)
    helped_sum = helped_amount(db, user.id, since=since, until=until)
    active_cards = count_active_for_author(db, user.id)
    chart = views_last_7_days(db, user.id)
    total_views = sum(item["value"] for item in chart)
    activities = recent_activities(db, user.id)

    return {
        "collected": collected,
        "collected_delta": _delta_label(collected, previous),
        "helped_people": helped_people,
        "helped_amount": helped_sum,
        "active_cards": active_cards,
        "card_limit": 3,
        "views_total": total_views,
        "chart": chart,
        "period": period,
        "activities": [
            {
                "title": item.title,
                "amount_label": item.amount_label,
                "happened_at": item.happened_at,
                "kind": item.kind,
            }
            for item in activities
        ],
    }
