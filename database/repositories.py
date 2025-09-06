from typing import Optional
from database.users_data_repository import UsersDataRepository
from database.anime_cache_repository import AnimeCacheRepository


users_data_repository: Optional[UsersDataRepository] = None

def get_users_data_repository() -> Optional[UsersDataRepository]:
    """
    Получение объекта работы с базой данных пользователей
    :return: объект UsersDataRepository
    """
    global users_data_repository
    return users_data_repository

def set_users_data_repository(data: UsersDataRepository) -> None:
    """
    Регистрация объекта базы данных пользователей
    :param data: класс UsersDataRepository
    :return: None
    """
    global users_data_repository
    users_data_repository = data


anime_cache_repository: Optional[AnimeCacheRepository] = None

def set_anime_cache_repository(data: AnimeCacheRepository) -> None:
    """
    Регистрация объекта базы данных аниме кэша
    :param data: класс AnimeCacheRepository
    :return: None
    """
    global anime_cache_repository
    anime_cache_repository = data

async def get_anime_cache_repository() -> Optional[AnimeCacheRepository]:
    """
    Получение объекта работы с базой данных аниме кэша.
    При отсутствии — создаёт и регистрирует объект.
    :return: объект AnimeCacheRepository
    """
    global anime_cache_repository
    if anime_cache_repository is None:
        anime_cache_instance = await AnimeCacheRepository.create()
        if anime_cache_instance is None:
            return None
        set_anime_cache_repository(anime_cache_instance)

    return anime_cache_repository