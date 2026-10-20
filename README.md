### ВК поиск
[![Python Version](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fqvp%2Fvk_search%2Fmain%2Fpyproject.toml&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Release](https://img.shields.io/github/v/release/qvp/vk_search?logo=github&label=version)](https://github.com/qvp/vk_search/releases/latest)

Ваш личный сайт знакомств - без ограничений и бесплатно.  
Работает на базе ВКонтакте прямо у вас на компьютере.  

**Преимущества по сравнению с обычным поиском ВКонтакте**:  
🔥Находит скрытые профили (скрыт возраст \ пол \ город)  
🔥Обходит ограничение первой 1000 результатов поиска  
🔥Проверка кому из подруг уже писал  
✅ Фильтр приватных страниц  
✅ Фильтр приватных сообщений  
✅ Фильтр по дате посещения  
✅ Фильтр по семейному положению  
✅ Запоминает просмотренные анкеты  
✅ Показывает статистику  
✅ Экспорт данных в Excel  
✅ Поиск сразу по нескольким городам  

### Установка
1. [Скачать](https://github.com/qvp/vk_search/releases) последнюю версию `vk_search.exe`
2. Запустить

При первом запуске создается файл `database.sqlite`. Этот файл хранит историю просмотров, его не нужно удалять.

### Ручная установка (для опытных)
1. Установить Python https://python.org/downloads
2. Установить UV https://docs.astral.sh/uv/getting-started/installation
3. Запустить `uv run uvicorn app.main:app --reload`
4. Открыть в браузере http://localhost:8000

### Сборка exe
`uv run pyinstaller --clean --noconfirm vk_search.spec`

### Скриншоты
![Главная](screenshots/main.jpg)
![Настройки](screenshots/settings.jpg)
![Статистика](screenshots/stats.jpg)
