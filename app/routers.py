import json
from typing import Annotated

from fastapi import Depends, Query, status, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import APIRouter, Request, Path, BackgroundTasks
from sqlalchemy.orm import Session
from vk.exceptions import VkAPIError

from app import vkontakte
from app.models import Act
from app import task, crud
from app.db import get_db
from app import stats
from app import settings
from app import cities
from app import util
from app import fake_data
from app import version


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

SHOW_FAKE_DATA = False


@router.get("/")
async def index(
        request: Request,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    # Если у пользователя нет настроек - редиректим на /settings
    user_settings = settings.settings_get()
    if not user_settings:
        return RedirectResponse(url="/settings")
    
    # Если у пользователя установлены специальные флаги - редиректим на /settings
    # Там мы должны показать ему alert, объясняющий, что случилось
    if user_settings.access_token_failed or user_settings.search_done:
        return RedirectResponse(url="/settings")
    
    contact = crud.contact_get_for_show(db, user_settings)

    # Если контакты кончились начинаем поиск
    if not contact:
        if not task.is_search_running:
            background_tasks.add_task(task.search)
        return templates.TemplateResponse(request=request, name="search.html")

    # Определяем из какого города контакт
    city = "город не указан"
    if contact.city and (city_obj := cities.get_one(contact.city)):
        city = city_obj.name

    age = "возраст не указан"
    if contact.age:
        age = util.add_year_word(contact.age)

    # Проверка на темную лошадку
    # показываем золотой алерт над контактом если у него есть скрытые поля
    hidden_fields = [field for field, value in (
        ("пол", contact.sex),
        ("возраст", contact.age),
        ("город", contact.city),
    ) if value is None]

    # Показываем контакт
    data = {
        "id": contact.id,
        "vk_id": contact.vk_id,
        "photo": contact.photo or "/static/nophoto-police.png",
        "name": contact.name,
        "age": age,
        "city": city,
        "hidden_fields": ", ".join(hidden_fields),
    }

    if SHOW_FAKE_DATA:
        data = fake_data.contact_data

    return templates.TemplateResponse(request=request, name="contact.html", context={"data": data})


@router.get("/action/{contact_id}/{act}")
async def action(
        contact_id: Annotated[int, Path(ge=1)],
        act: Annotated[Act, Path],
        db: Session = Depends(get_db),
):
    crud.contact_set_act(db, contact_id, act)

    return RedirectResponse(url="/")


@router.get("/check-friends/{contact_id}")
def check_friends(
        request: Request,
        contact_id: Annotated[int, Path(ge=1)],
        db: Session = Depends(get_db),
):
    contact = crud.contact_get(db, contact_id)
    if not contact:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    user_settings = settings.settings_get()
    if not user_settings:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User settings missing")

    # Получаем список друзей ВКонтакте
    # Если токен устарел - отмечаем это и редиректим на страницу настроек
    try:
        vk_friends = vkontakte.get_user_friends(user_settings.access_token, contact.vk_id)
    except VkAPIError as e:
        if e.code == vkontakte.VK_ERROR_INVALID_TOKEN:
            user_settings.access_token_failed = True
            settings.settings_set(user_settings)
            return RedirectResponse(url="/settings")
        else:
            raise

    friends_ids = [f.vk_id for f in vk_friends]
    friends = crud.contact_get_send(db, friends_ids)

    data = {
        "contact": contact,
        "friends": friends,
    }

    if SHOW_FAKE_DATA:
        data = fake_data.friends_data

    return templates.TemplateResponse(request=request, name="check_friends.html", context={"data": data})



@router.get("/city-autocomplete" , response_model=list[cities.City])
def autocomplete_cities(q: str = Query(..., min_length=3, max_length=30)):
    return cities.autocomplete(q)


@router.get("/settings")
def settings_form(request: Request):
    user_settings = settings.settings_get()
    user_cities_ids = user_settings.cities if user_settings else ()

    data = user_settings.model_dump() if user_settings else {}
    data["cities_json"] = json.dumps([c.model_dump() for c in cities.get_many(user_cities_ids)], ensure_ascii=False)

    return templates.TemplateResponse(request=request, name="settings.html", context={"data": data})


@router.post("/settings", status_code=status.HTTP_200_OK)
def settings_save(data: settings.Settings) -> None:
    user_settings = settings.settings_get()

    # Сбрасываем failed флаг access_token если его отредактировали
    if user_settings and user_settings.access_token != data.access_token:
        data.access_token_failed = False

    # Сбрасываем флаг search_done (поиск завершен)
    # Если пользователь не поменял ничего влияющего на поиск этот флаг просто снова установится в task
    data.search_done = False

    settings.settings_set(data)


@router.get("/stats")
def statistics(request: Request, db: Session = Depends(get_db)):
    data = stats.stats_get(db)
    data["new_version"] = version.get_new_version()
    data["current_version"] = version.VERSION

    return templates.TemplateResponse(request=request, name="statistics.html", context={"stats": data})