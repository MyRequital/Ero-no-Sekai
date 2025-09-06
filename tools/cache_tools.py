import asyncio
from typing import List, Tuple

from database.anime_cache_repository import AnimeCacheRepository
import json
import os
from _configs.config import get_config
from _configs.log_config import logger


cfg = get_config()
ANIME_CACHE_PATH = cfg.cache_config.anime_cache_path

_cache_data = None
_last_mtime = 0


async def cache_anime_list(
    anime_entries: List[Tuple[int, dict]],
    repository: AnimeCacheRepository
) -> None:
    """
    Асинхронно сохраняет список аниме-данных в Supabase через AnimeCacheRepository.

    :param anime_entries: Список кортежей (anime_id, anime_entry)
    :param repository: Экземпляр AnimeCacheRepository
    """
    for anime_id, anime_entry in anime_entries:
        try:
            await repository.add_anime_cache(anime_id, anime_entry)
            logger.debug(f"[cache_anime_list] ✅ Сохранено в БД: {anime_id}")
        except Exception as e:
            logger.warning(f"[cache_anime_list] ❌ Ошибка сохранения ID {anime_id} в БД\n{e}")


def cache_anime_list_in_background(
    anime_entries: List[Tuple[int, dict]],
    repository: AnimeCacheRepository
) -> None:
    """
    Запускает фоновую задачу по сохранению кэша аниме в Supabase.

    :param anime_entries: Список кортежей (anime_id, anime_entry)
    :param repository: Экземпляр AnimeCacheRepository
    """
    try:
        asyncio.create_task(cache_anime_list(anime_entries, repository))
        logger.info(f"[cache_anime_list_in_background] 🚀 Запущена фоновая задача на кэширование {len(anime_entries)} аниме")
    except Exception as e:
        logger.error(f"[cache_anime_list_in_background] ❌ Ошибка запуска фоновой задачи\n{e}")


def get_anime_cache():
    global _cache_data, _last_mtime

    try:

        mtime = os.path.getmtime(ANIME_CACHE_PATH)
        logger.debug(f"[get_anime_cache] -> Проверка времени изменения файла, текущее время изменения файла {mtime}")
        if _cache_data is None or mtime > _last_mtime:
            with open(ANIME_CACHE_PATH, "r", encoding="utf-8") as f:
                _cache_data = json.load(f)
                _last_mtime = mtime
                logger.info(f"[get_anime_cache] -> Обновление файла. Замечено изменение времени обновления файла {_last_mtime}")
        logger.info(f"[get_anime_cache] - Кэш успешно обновлен после нового запроса")
    except Exception as e:
        logger.error(f"[get_anime_cache] - Не удалось загрузить кеш: {e}")
        _cache_data = {}

    logger.debug(f"[get_anime_cache] - Выдача кэша")
    return _cache_data