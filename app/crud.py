from datetime import datetime, UTC

from sqlalchemy import func, select, update, or_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.settings import Settings
from app.models import Contact, Act


def contact_get_unique_search_queries(db: Session) -> list[str]:
    stmt = select(Contact.search_query).where(Contact.search_query.is_not(None)).distinct()
    result = db.execute(stmt)

    return list(result.scalars().all())


def contact_batch_insert(db: Session, data: list[dict]) -> None:
    stmt = insert(Contact).values(data)

    # Пропускаем при конфликте по unique constraint
    stmt = stmt.on_conflict_do_nothing(
        index_elements=['vk_id']
    )
    db.execute(stmt)
    db.commit()


def contact_get(db: Session, contact_id: int) -> Contact | None:
    return db.get(Contact, contact_id)


def contact_get_for_show(db: Session, user_settings: Settings) -> Contact | None:
    """
    Возвращает рандомный контакт для показа на главной из тех что пользователь еще не скрыл

    У контакта может быть не указан город, возраст или пол, но его все равно нужно показывать
    """
    # Фильтруем только тех кого пользователь еще не отметил
    stmt = select(Contact).where(Contact.act.is_(None))

    # Фильтруем по городам актуальным в данный момент
    stmt = stmt.where(or_(
        Contact.city.in_(user_settings.cities),
        Contact.city.is_(None),
    ))
    
    # Фильтруем по возрасту актуальному в данный момент
    stmt = stmt.where(or_(
        Contact.age.between(user_settings.age_from, user_settings.age_to),
        Contact.age.is_(None),
    ))

    # Скрываем тех кто давно не посещал свою страницу вконтакте
    if user_settings.hide_longtime_visited:
        stmt = stmt.where(Contact.last_visit_days <= 30)

    # Скрываем тех у кого семейное положение "занято"
    if user_settings.hide_married:
        stmt = stmt.where(Contact.is_relation_open == True)

    # Скрываем тех у кого закрыта страница
    if user_settings.hide_private_page:
        stmt = stmt.where(Contact.is_page_open == True)

    # Скрываем тех у кого закрыты личные сообщения
    if user_settings.hide_private_messages:
        stmt = stmt.where(Contact.is_messages_open == True)
    
    stmt = stmt.where(Contact.vk_id.is_not(None)).order_by(func.random()).limit(1)
    result = db.execute(stmt)

    return result.scalar_one_or_none()


def contact_get_for_search_friends(db: Session, user_settings: Settings) -> Contact | None:
    """
    Возвращает рандомный контакт из тех по которым еще не вели поиск среди друзей

    Главное чтобы совпадал город поиска.
    Смотреть друзей можно только если страница открытая.
    """
    stmt = select(Contact).where(
        Contact.city.in_(user_settings.cities),
        Contact.search_friends_at.is_(None),
        Contact.is_page_open == True,
    ).limit(1)
    result = db.execute(stmt)

    return result.scalar_one_or_none()


def contact_set_act(db: Session, contact_id: int, act: Act) -> None:
    act_at = datetime.now(UTC)
    stmt = (
        update(Contact)
        .where(Contact.id == contact_id)
        .values(act=act, act_at=act_at)
    )
    db.execute(stmt)
    db.commit()


def contact_mark_search_friends(db: Session, contact_id: int) -> None:
    search_friends_at = datetime.now(UTC)
    stmt = (
        update(Contact)
        .where(Contact.id == contact_id)
        .values(search_friends_at=search_friends_at)
    )
    db.execute(stmt)
    db.commit()
    

def contact_get_send(db: Session, friends_ids: list[int]) -> list[Contact]:
    stmt = select(Contact).where(
        Contact.act == Act.SEND,
        Contact.vk_id.in_(friends_ids),
    )
    result = db.execute(stmt)

    return result.scalars().all()
