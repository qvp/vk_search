"""Единая точка вычисления путей к ресурсам и данным.

Работает одинаково и в режиме разработки, и в собранном PyInstaller
приложении (--onefile и --onedir).
"""

import sys
from pathlib import Path


def _resource_dir() -> Path:
    """Каталог с ресурсами только для чтения (static, templates).

    В собранном приложении ресурсы лежат в ``sys._MEIPASS`` (распакованный
    временный каталог для --onefile или ``_internal`` для --onedir).
    В режиме разработки — рядом с пакетом ``app``.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parent


def _data_dir() -> Path:
    """Каталог для изменяемых файлов (database.sqlite, settings.json).

    В собранном приложении — рядом с exe, чтобы данные сохранялись между
    запусками (для --onefile ``sys._MEIPASS`` — временный каталог).
    В режиме разработки — корень проекта.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


RESOURCE_DIR = _resource_dir()
DATA_DIR = _data_dir()

STATIC_DIR = RESOURCE_DIR / "static"
TEMPLATES_DIR = RESOURCE_DIR / "templates"

DB_PATH = DATA_DIR / "database.sqlite"
SETTINGS_PATH = DATA_DIR / "settings.json"
