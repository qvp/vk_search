from datetime import datetime, timedelta, UTC

contact_data = {
    "id": 1,
    "vk_id": 1,
    "photo": "/static/fake_data/selma.png",
    "name": "Ольга Гаврилина",
    "age": 23,
    "city": "Челябинск",
    "hidden_fields": "пол",
}

friend1 = {
    "id": 2,
    "vk_id": 2,
    "photo": "/static/fake_data/sarah.png",
    "name": "Татьяна Карпова",
    "age": 25,
    "city": "Томск",
    "act_at": datetime.now(UTC) - timedelta(days=8, hours=2, minutes=14),
}

friend2 = {
    "id": 3,
    "vk_id": 3,
    "photo": "/static/fake_data/riz.jpg",
    "name": "Жанна Акулич",
    "age": 25,
    "city": "Томск",
    "act_at": datetime.now(UTC) - timedelta(days=3, hours=6, minutes=9),
}

friends_data = {
    "contact": contact_data,
    "friends": [friend1, friend2],
}
