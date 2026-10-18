import enum
from datetime import datetime, UTC

from sqlalchemy_utils import ChoiceType
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, BigInteger, Integer, DateTime, Boolean

from app.db import Base


class Act(enum.StrEnum):
    HIDE = "hide"
    SEND = "send"


class Contact(Base):
    # Добавлять индексы вредно так как используется ORDER BY random()
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    act: Mapped[Act | None] = mapped_column(ChoiceType(Act, impl=String(20)))
    act_at: Mapped[datetime | None] = mapped_column(DateTime)
    search_query: Mapped[str | None] = mapped_column(String(1024))
    search_friends_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Эти поля должны совпадать с vkontakte.User
    vk_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    photo: Mapped[str | None] = mapped_column(String(1024))
    city: Mapped[int | None] = mapped_column(Integer)
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[int | None] = mapped_column(Integer)
    last_visit_days: Mapped[int | None] = mapped_column(Integer)
    is_relation_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_page_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_messages_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
