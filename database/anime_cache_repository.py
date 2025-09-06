import asyncio
from typing import Optional

import asyncpg
import json
from pathlib import Path


from _configs.config import get_config
from _configs.log_config import logger


cfg = get_config()

CACHE_DB_USER = cfg.database_config.cache_db_user
CACHE_DB_PASSWORD = cfg.database_config.cache_db_password
CACHE_DB_HOST = cfg.database_config.cache_db_host
CACHE_DB_PORT = cfg.database_config.cache_db_port
CACHE_DB_NAME = cfg.database_config.cache_db_name

CACHE_JSON_PATH = Path(cfg.cache_config.anime_cache_path)


class AnimeCacheRepository:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, pool):
        self.pool = pool

    @classmethod
    async def create(cls):
        """

        Singleton-фабрика: создаёт экземпляр AnimeCacheRepository один раз, с пулом подключений к БД.

        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    logger.info("🔁 [AnimeCacheRepository]: инициализация пула подключений к базе данных аниме кэша...")

                    logger.info(
                        f"[[AnimeCacheRepository].create] - 🔁 Попытка создания пула с параметрами:"
                        f"\nuser = {CACHE_DB_USER}"
                        f"\npassword = {CACHE_DB_PASSWORD}"
                        f"\nhost = {CACHE_DB_HOST}"
                        f"\nport = {CACHE_DB_PORT}"
                        f"\ndbname = {CACHE_DB_NAME}"
                        f"\ntimeout = 120"
                    )

                    try:
                        pool = await asyncpg.create_pool(
                            user=CACHE_DB_USER,
                            password=CACHE_DB_PASSWORD,
                            host=CACHE_DB_HOST,
                            port=CACHE_DB_PORT,
                            timeout=120,
                            database=CACHE_DB_NAME,
                            statement_cache_size=0
                        )
                    except Exception as err:
                        logger.error(f"[[AnimeCacheRepository].create] - ❌ Ошибка при создании пула подключения: {err}")
                        return None

                    cls._instance = cls(pool)
                    logger.info("[[AnimeCacheRepository].create] - ✅ AnimeCacheRepository: пул подключений успешно создан")

        return cls._instance


    # ====== Геттер для anime_data ======
    async def get_anime_data(self, anime_id: int) -> Optional[dict]:
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("SELECT data FROM anime_cache WHERE anime_id = $1", anime_id)
                return result["anime_data"] if result else None
        except Exception as err:
            logger.error(f"[AnimeCacheRepository][get_anime_data] ❌ Ошибка при получении anime_data: {err}")
            return None


    # ====== Сеттер для anime_data ======
    async def set_data(self, anime_id: int, data: dict) -> bool:
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO anime_cache (anime_id, data)
                    VALUES ($1, $2)
                    ON CONFLICT (anime_id)
                    DO UPDATE SET data = EXCLUDED.data
                    """,
                    anime_id, json.dumps(data)
                )
            logger.violet(f"[AnimeCacheRepository][set_data] ✅ Данные обновлены для anime_id={anime_id}")
            return True
        except Exception as err:
            logger.error(f"[AnimeCacheRepository][set_data] ❌ Ошибка при обновлении data: {err}")
            return False


    # # ====== Загрузка всего кэша из БД и сохранение в файл ======
    # async def export_cache_to_file(self) -> None:
    #     try:
    #         async with self.pool.acquire() as conn:
    #             records = await conn.fetch("SELECT anime_id, data FROM anime_cache")
    #
    #         cache_dict = {record["anime_id"]: record["data"] for record in records}
    #         CACHE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    #
    #         with CACHE_JSON_PATH.open("w", encoding="utf-8") as f:
    #             json.dump(cache_dict, f, ensure_ascii=False, indent=2)
    #
    #         logger.info(
    #             f"[AnimeCacheRepository][export_cache_to_file] ✅ Экспортировано {len(records)} записей в JSON файл."
    #         )
    #     except Exception as e:
    #         logger.error(f"[AnimeCacheRepository][export_cache_to_file] ❌ Ошибка при экспорте кэша в файл: {e}")

    # ====== Загрузка всего кэша из БД и сохранение в файл ======
    async def export_cache_to_file(self) -> None:
        try:
            async with self.pool.acquire() as conn:
                records = await conn.fetch("SELECT anime_id, data FROM anime_cache")

            # Используем comprehension dictionary с применением json.loads
            cache_dict = {}
            for record in records:
                try:
                    cache_dict[record["anime_id"]] = json.loads(record["data"])
                except json.JSONDecodeError as e:
                    logger.error(
                        f"[AnimeCacheRepository][export_cache_to_file] ❌ Ошибка при декодировании JSON для anime_id {record['anime_id']}: {e}"
                    )
                    continue  # Пропустить проблемную запись

            CACHE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

            with CACHE_JSON_PATH.open("w", encoding="utf-8") as f:
                json.dump(cache_dict, f, ensure_ascii=False, indent=2)

            logger.info(
                f"[AnimeCacheRepository][export_cache_to_file] ✅ Экспортировано {len(records)} записей (после обработки ошибок) в JSON файл."
            )
        except Exception as e:
            logger.error(f"[AnimeCacheRepository][export_cache_to_file] ❌ Ошибка при экспорте кэша в файл: {e}")



    # ====== Добавление в БД и в файл ======
    async def add_anime_cache(self, anime_id: int, data: dict) -> bool:
        """
        Добавляет запись в БД и обновляет локальный JSON-файл кэша
        """
        success = await self.set_data(int(anime_id), data)
        logger.info(f"[AnimeCacheRepository][add_anime_cache] ✅ Попытка обновления кэша для ->"
                    f"\nanime_id: {anime_id}({type(anime_id)})"
                    f"\ndata: {data}"
                    f"\nsuccess: {success}")
        if success:
            try:
                CACHE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

                json_data = {}
                if CACHE_JSON_PATH.exists():
                    with CACHE_JSON_PATH.open("r", encoding="utf-8") as f:
                        json_data = json.load(f)

                json_data[anime_id] = data

                with CACHE_JSON_PATH.open("w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                logger.info(f"[AnimeCacheRepository][add_anime_cache] ✅ Кэш обновлён для anime_id={anime_id}")
            except Exception as e:
                logger.error(f"[AnimeCacheRepository][add_anime_cache] ❌ Ошибка при обновлении кэша в JSON: {e}")

        return success


async def init_anime_cache_repository():
    """
    Инициализирует создание подключения к базе данных кэша
    :return:
    """
    anime_cache_instance_repository = await AnimeCacheRepository.create()
    if anime_cache_instance_repository is None:
        logger.error("[init_anime_cache_repository] - ❌ Ошибка: AnimeCacheRepository не было создано!")
        return None

    logger.info("✅ Инициализация AnimeCacheRepository успешна")
    return anime_cache_instance_repository
