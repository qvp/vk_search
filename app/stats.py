from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Act, Contact


_MONTHS_RU_SHORT = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]


def _format_day_label(d: date) -> str:
    return f"{d.day} {_MONTHS_RU_SHORT[d.month - 1]}"


def _as_date(value) -> date:
    """func.date() в SQLite отдаёт строку, в Postgres — date/datetime. Приводим к date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def stats_get_totals(db: Session) -> tuple[int, int]:
    """
    Возвращает (viewed, written) за всё время.
    viewed = act == hide (посмотрел и скрыл, не стал писать).
    written = act == send (написал).
    """
    rows = db.execute(
        select(Contact.act, func.count())
        .where(Contact.act.is_not(None))
        .group_by(Contact.act)
    ).all()

    counts = {act: count for act, count in rows}
    viewed = counts.get(Act.HIDE, 0)
    written = counts.get(Act.SEND, 0)
    return viewed, written


def stats_get_totals_since(db: Session, since: datetime) -> tuple[int, int]:
    """То же самое, но только для act_at >= since."""
    rows = db.execute(
        select(Contact.act, func.count())
        .where(Contact.act.is_not(None), Contact.act_at >= since)
        .group_by(Contact.act)
    ).all()

    counts = {act: count for act, count in rows}
    viewed = counts.get(Act.HIDE, 0)
    written = counts.get(Act.SEND, 0)
    return viewed, written


def stats_get_daily(db: Session, days: int = 30) -> list[dict]:
    """
    Разбивка по дням за последние `days` дней (включая сегодня), от старого к новому.
    Каждый элемент: {"date": "2026-08-06", "label": "6 авг", "viewed": int, "written": int}.
    Дни без единой записи в БД всё равно попадают в список с нулями — пропусков не остаётся,
    именно это и рисуется на странице как пустой столбик.
    """
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    day_col = func.date(Contact.act_at).label("day")

    rows = db.execute(
        select(day_col, Contact.act, func.count())
        .where(Contact.act.is_not(None), Contact.act_at >= start_dt)
        .group_by(day_col, Contact.act)
    ).all()

    by_day: dict[date, dict[str, int]] = {}
    for day_value, act, count in rows:
        d = _as_date(day_value)
        entry = by_day.setdefault(d, {"viewed": 0, "written": 0})
        if act == Act.HIDE:
            entry["viewed"] += count
        elif act == Act.SEND:
            entry["written"] += count

    result: list[dict] = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        entry = by_day.get(d, {"viewed": 0, "written": 0})
        result.append({
            "date": d.isoformat(),
            "label": _format_day_label(d),
            "viewed": entry["viewed"],
            "written": entry["written"],
        })

    return result


def stats_get(db: Session) -> dict:
    """Собирает весь контекст сразу для templates.TemplateResponse(name='stats.html', ...)."""
    viewed_total, written_total = stats_get_totals(db)

    since_30d = datetime.now(timezone.utc) - timedelta(days=30)
    viewed_30d, written_30d = stats_get_totals_since(db, since_30d)

    return {
        "viewed_total": viewed_total,
        "written_total": written_total,
        "viewed_30d": viewed_30d,
        "written_30d": written_30d,
        "daily": stats_get_daily(db, days=30),
    }
