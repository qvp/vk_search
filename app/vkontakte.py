from datetime import datetime, UTC

from vk import API
from pydantic import BaseModel

from app import settings


class User(BaseModel):
    vk_id: int
    name: str
    photo: str | None
    city: int | None
    age: int | None
    sex: int | None
    last_visit_days: int | None
    is_relation_open: bool
    is_page_open: bool
    is_messages_open: bool


VK_SEX_FEMALE = 1
VK_ERROR_INVALID_TOKEN = 5
VK_ERROR_PROFILE_IS_PRIVATE = 30
VK_FIELDS = "screen_name,last_seen,crop_photo,can_write_private_message,city,sex,relation,bdate"


def search_by_day(access_token: str, city: int, year: int, month: int, day: int) -> list[User]:
    """
    Поиск контактов напрямую через users.search API
    """
    search_params = {
        "city": city,
        "birth_year": year,
        "birth_month": month,
        "birth_day": day,
        "fields": VK_FIELDS,
        "count": 1000,
        "sex": VK_SEX_FEMALE,
    }

    api = API(access_token=access_token, v="5.101")
    response = api.users.search(**search_params)

    result = []
    for vk_user in response["items"]:
        result.append(_parse_user(vk_user))

    return result


def search_in_friends(user_settings: settings.Settings, vk_user_id: int) -> list[User]:
    """
    Поиск по друзьям контакта

    Здесь фильтруем по полу, городу и возрасту допуская, что эти значения могут быть None
    """
    result = []
    vk_users = get_user_friends(user_settings.access_token, vk_user_id)
    for vk_user in vk_users:

        # Пол женский или не указан
        if vk_user.sex not in (VK_SEX_FEMALE, None):
            continue

        # Возраст в нужном диапазоне или не указан
        if vk_user.age is not None and not (user_settings.age_from <= vk_user.age <= user_settings.age_to):
            continue

        # Город в нужном списке или не указан
        if vk_user.city not in user_settings.cities + [None]:
            continue

        result.append(vk_user)

    return result


def get_user_friends(access_token: str, vk_user_id: int) -> list[User]:
    """
    Получить друзей пользователя
    """
    params = {
        "user_id": vk_user_id,
        "fields": VK_FIELDS,
        "count": 1000,
    }

    api = API(access_token=access_token, v="5.101")
    response = api.friends.get(**params)

    vk_users = []
    for item in response["items"]:
        vk_user = _parse_user(item)
        vk_users.append(vk_user)

    return vk_users


def _parse_user(vk_raw_user: dict) -> User:
    user = User(
        vk_id=str(vk_raw_user["id"]),
        city=vk_raw_user.get("city", {}).get("id"),
        name=vk_raw_user.get("first_name", "") + " " + vk_raw_user.get("last_name", ""),
        age=_parse_age_from_bdate(vk_raw_user.get("bdate")),
        sex=vk_raw_user.get("sex"),
        photo=None,
        last_visit_days=_calculate_last_visit_days(vk_raw_user.get("last_seen", {}).get("time")),
        is_relation_open=_is_relation_open(vk_raw_user.get("relation")),
        is_page_open=not bool(vk_raw_user.get("is_closed", 0)),  # по умолчанию открыта
        is_messages_open=bool(vk_raw_user.get("can_write_private_message", 0)),
    )

    # Выбираем самую большую из аватарок
    if "crop_photo" in vk_raw_user:
        sizes = {p["width"] * p["height"]: p["url"] for p in vk_raw_user["crop_photo"]["photo"]["sizes"]}
        max_key = max(sizes.keys())
        if max_key:
            user.photo = sizes[max_key]

    return user


def _parse_age_from_bdate(vk_birth_date: str | None) -> int | None:
    if vk_birth_date is None:
        return None

    try:
        # Дата может приходить в формате %d.%m
        bdate = datetime.strptime(vk_birth_date, "%d.%m.%Y").replace(tzinfo=UTC)
    except ValueError:
        return None

    today = datetime.now(UTC)
    age = today.year - bdate.year

    # Если день рождения ещё не наступил в этом году
    if (today.month, today.day) < (bdate.month, bdate.day):
        age -= 1

    return age


def _calculate_last_visit_days(last_seen_time: int | None) -> int | None:
    last_visit_days = None
    if last_seen_time:
        last_seen_delta = datetime.now(UTC) - datetime.fromtimestamp(last_seen_time, tz=UTC)
        last_visit_days = last_seen_delta.days

    return last_visit_days


def _is_relation_open(vk_relation: int | None) -> bool:
    open_statuses = (
        None,
        1,  # не замужем,
        6,  # в активном поиске
    )

    return vk_relation in open_statuses
