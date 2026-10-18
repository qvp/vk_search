from github import Github
from packaging.version import parse, InvalidVersion
import sys

# Ваша текущая версия
VERSION = "0.0.1"

# Настройки репозитория
REPO_PATH = "qvp/vk_search"

def get_latest_github_version(repo_path, token=None):
    """Получает тег последнего релиза с GitHub."""
    try:
        g = Github(token) if token else Github()
        repo = g.get_repo(repo_path)
        latest_release = repo.get_latest_release()
        # Тег часто содержит префикс 'v', например 'v1.2.3'
        # parse() из packaging обычно справляется с таким форматом,
        # но на всякий случай можно убрать 'v' вручную:
        tag = latest_release.tag_name.lstrip('v')
        return tag
    except Exception as e:
        print(f"Не удалось получить версию с GitHub: {e}")
        return None

def get_new_version() -> str | None:
    """
    Сравнивает текущую версию с последней на GitHub.

    Возвращает новую версию если она выше текущей.
    """
    try:
        latest_version_str = get_latest_github_version(REPO_PATH)
        v_current = parse(VERSION)
        v_latest = parse(latest_version_str)
    except InvalidVersion as e:
        print(f"Ошибка формата версии: {e}")
        return None

    if v_latest > v_current:
        return latest_version_str

    return None
