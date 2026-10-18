import time
import random
from datetime import date, timedelta

import vk.exceptions
from sqlalchemy.orm import Session

from app import crud
from app import vkontakte
from app.db import SessionLocal
from app import settings


# Флаг - запущена задача или нет
is_search_running = False


def search():
    global is_search_running

    try:
        is_search_running = True
        with SessionLocal() as db:
            _search_task(db)

    finally:
        is_search_running = False


def _search_task(db: Session) -> None:
    # Если нет настроек завершаем поиск
    # пользователя переадресует на страницу настроек
    user_settings = settings.settings_get()
    if not user_settings:
        return

    # Прекращаем поиск если токен протух
    # (пользователю показывается сообщение "обновите токен")
    if user_settings.access_token_failed:
        return

    # Находим случайные параметры для поиска
    processed_search_queries = crud.contact_get_unique_search_queries(db)
    free_search_queries = _generate_fee_search_queries(processed_search_queries, user_settings.cities, user_settings.age_from, user_settings.age_to)

    # Находим случайный контакт для поиска по друзьям
    contact_for_search_friends = crud.contact_get_for_search_friends(db, user_settings)

    # Если нет возможности искать новые контакты завершаем поиск
    # помечаем в настройках флаг и переадресовываем на настройки
    if not free_search_queries and contact_for_search_friends is None:
        user_settings.search_done = True
        settings.settings_set(user_settings)
        return

    try:
        # Поиск через users.search
        if free_search_queries:
            random_sq_index = random.randrange(len(free_search_queries))
            search_query: str = free_search_queries.pop(random_sq_index)
            city, year, month, day = _parse_search_query(search_query)
            vk_users_day = vkontakte.search_by_day(user_settings.access_token, city, year, month, day)

            if vk_users_day:
                items_for_save = [{**u.model_dump(), "search_query": search_query} for u in vk_users_day]
            else:
                # Если список пуст добавляем один пустой контакт, чтобы сохранить search_query
                items_for_save = [{
                    "vk_id": None,
                    "name": "{empty contact}",
                    "search_query": search_query,
                    "is_relation_open": False,
                    "is_page_open": False,
                    "is_messages_open": False,
                }]

            # сохраняем результаты добавляя текущий поисковой запрос
            crud.contact_batch_insert(db, items_for_save)

            # Ждем секунду чтобы ВК не ругался на спам
            time.sleep(1)

        # Поиск через друзей
        if contact_for_search_friends:
            try:
                vk_users_friends = vkontakte.search_in_friends(user_settings, contact_for_search_friends.vk_id)
                if vk_users_friends:
                    crud.contact_batch_insert(db, [u.model_dump() for u in vk_users_friends])
            except vk.exceptions.VkAPIError as e:
                if e.code != vkontakte.VK_ERROR_PROFILE_IS_PRIVATE:
                    raise
            finally:
                crud.contact_mark_search_friends(db, contact_for_search_friends.id)

    # Если токен устарел помечаем это в настройках
    except vk.exceptions.VkAPIError as e:
        if e.code == vkontakte.VK_ERROR_INVALID_TOKEN:
            user_settings.access_token_failed = True
            settings.settings_set(user_settings)
        else:
            raise

    finally:
        # Ждем секунду на случай если несколько поисков будет запущено подряд
        time.sleep(1)


def _generate_fee_search_queries(processed_map: set[str], cities: list[int], age_from: int, age_to: int) -> list[str]:
    """
    Создает карту еще не обработанных значений.
    """
    one_day = timedelta(days=1)
    current_date = date.today()

    min_birth_date = current_date.replace(year=current_date.year - age_to - 1) + one_day
    max_birth_date = current_date.replace(year=current_date.year - age_from)

    result = []
    current = min_birth_date

    while current <= max_birth_date:
        for city in cities:
            map_item = _stringify_search_query(city, current)

            if map_item not in processed_map:
                result.append(map_item)

        current += one_day

    return result


def _stringify_search_query(city: int, item_date: date) -> str:
    """
    Return string "city-year-month-day"
    """
    return f"{city}_{item_date.strftime("%Y_%m_%d")}"


def _parse_search_query(map_item: str) -> tuple[int, int, int, int]:
    """
    Parse string "city-year-month-day"
    """
    items = map_item.split("_")
    return int(items[0]), int(items[1]), int(items[2]), int(items[3])


if __name__ == "__main__":
    search()
