from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DB_PATH = Path(__file__).resolve().parent.parent / "database.sqlite"
DB_URL = f"sqlite:///{DB_PATH}"


engine = create_engine(
    DB_URL,
    connect_args={
        "timeout": 15,            # Ждать до 15с при блокировке файла
        "check_same_thread": False,  # FastAPI дергает sync-код из разных потоков
    },
    # pool_size=1,  # только один коннект на запись в конкретный момент
    # max_overflow=0,  # Никаких доп. соединений сверху
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()

    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=15000")

    cursor.close()


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db():
    if DB_PATH.exists():
        inspector = inspect(engine)

        # Получаем все имена таблиц из метаданных
        required_tables = set(Base.metadata.tables.keys())
        existing_tables = set(inspector.get_table_names())

        # Проверяем, какие таблицы есть
        if existing_tables:
            # Если есть хоть одна таблица
            missing_tables = required_tables - existing_tables

            if missing_tables:
                # Если есть таблицы, но не все - выбрасываем исключение
                raise ValueError(
                    f"База данных повреждена или неполная. "
                    f"Отсутствуют таблицы: {', '.join(missing_tables)}"
                )
            # Если все таблицы есть - просто возвращаемся
            return

    # Если файла БД нет или таблиц нет - создаем все таблицы
    Base.metadata.create_all(bind=engine)
