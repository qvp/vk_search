import csv
import io
from datetime import datetime, date, UTC

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact
from app.db import get_db

router = APIRouter()


# Русские заголовки для колонок
CSV_HEADERS = {
    "vk_id": "ВК ID",
    "name": "Имя",
    "age": "Возраст",
    "act": "Действие",
    "act_at": "Дата действия",
    "search_query": "Поисковый запрос",
    "search_friends_at": "Дата поиска друзей",
    "created_at": "Дата создания",
    "photo": "Фото",
    "city": "Город",
    "sex": "Пол",
    "last_visit_days": "Дней с последнего визита",
    "is_relation_open": "Открыты отношения",
    "is_page_open": "Открыта страница",
    "is_messages_open": "Открыты сообщения",
}

# Порядок колонок: сначала vk_id, name, age, потом все остальные
PRIORITY_COLUMNS = ["vk_id", "name", "age", "act", "city", "sex"]
ALL_COLUMNS = list(CSV_HEADERS.keys())
ORDERED_COLUMNS = PRIORITY_COLUMNS + [c for c in ALL_COLUMNS if c not in PRIORITY_COLUMNS]


def _format_value(value) -> str:
    """Приводим значение к строке для CSV."""
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bool):
        return "✅" if value else "❌"
    # Enum с ChoiceType (Act) — берём .value или .name
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def export_contacts_to_csv(db: Session) -> str:
    """Синхронно выгружает все контакты в CSV-строку."""
    contacts: list[Contact] = db.execute(select(Contact)).scalars().all()

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=",", quoting=csv.QUOTE_MINIMAL)

    # Заголовки на русском в нужном порядке
    writer.writerow([CSV_HEADERS[col] for col in ORDERED_COLUMNS])

    for contact in contacts:
        row = [_format_value(getattr(contact, col, None)) for col in ORDERED_COLUMNS]
        writer.writerow(row)

    return buffer.getvalue()


@router.get("/data-export")
def export_contacts_csv(db: Session = Depends(get_db)) -> Response:
    """Эндпоинт для выгрузки всех контактов в CSV."""
    csv_content = export_contacts_to_csv(db)
    filename = f"contacts_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

    # BOM в начале — чтобы Excel корректно открывал UTF-8
    return Response(
        content="\ufeff" + csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
