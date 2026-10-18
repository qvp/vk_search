import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel, Field, model_validator
from pydantic import ValidationError

from app.paths import SETTINGS_PATH


FILE_PATH: Path = SETTINGS_PATH


class Settings(BaseModel):
    access_token: str
    cities: list[int] = Field(min_length=1, max_length=20)
    age_from: int = Field(ge=18, le=99)
    age_to: int = Field(ge=18, le=99)
    hide_married: bool = Field(default=True)
    hide_private_page: bool = Field(default=True)
    hide_private_messages: bool = Field(default=True)
    hide_longtime_visited: bool = Field(default=True)

    # Специальные флаги для управления приложением
    access_token_failed: bool = Field(default=False)
    search_done: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def preprocess_access_token(cls, values):
        """Предварительная обработка access_token до валидации модели"""
        if isinstance(values, dict):
            token = values.get('access_token')
            if token and isinstance(token, str):  # noqa: SIM102
                # Если это URL с фрагментом
                if token.startswith('https://oauth.vk.ru/blank.html#'):
                    # Извлекаем параметры из фрагмента
                    fragment = token.split('#', 1)[1]
                    params = parse_qs(fragment)
                    if 'access_token' in params:
                        values['access_token'] = params['access_token'][0]
                # Если это просто строка - оставляем как есть
        return values

    @model_validator(mode="after")
    def validate_age_range(self) -> "Settings":
        if self.age_from > self.age_to:
            raise ValueError(
                f"age_from ({self.age_from}) не может быть больше age_to ({self.age_to})"
            )
        return self


def settings_get() -> Settings | None:
    path = Path(FILE_PATH)

    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Settings(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Ошибка при чтении настроек из {FILE_PATH}: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка при чтении {FILE_PATH}: {e}")
        return None


def settings_set(settings: Settings) -> bool:
    try:
        path = Path(FILE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Преобразуем модель в словарь и сохраняем с форматированием
        data = settings.model_dump(mode="json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return True
    except Exception as e:
        print(f"Ошибка при сохранении настроек в {FILE_PATH}: {e}")
        return False
