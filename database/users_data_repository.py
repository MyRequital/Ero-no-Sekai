import asyncio
import datetime
import random

import asyncpg
from aiocache import cached, Cache

from _configs.config import get_config
from _configs.log_config import logger
from data.funny_names import adjectives, nouns

cfg = get_config()

LIMIT_WARNINGS = cfg.bot_config.limit_warnings
DB_USER = cfg.database_config.db_user
DB_PASSWORD = cfg.database_config.db_password
DB_HOST = cfg.database_config.db_host
DB_PORT = cfg.database_config.db_port
DB_NAME = cfg.database_config.db_name

class UsersDataRepository:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self, pool):
        self.pool = pool

    @classmethod
    async def create(cls):
        """

        Singleton-фабрика: создаёт экземпляр UsersData один раз, с пулом подключений к БД.

        """
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    logger.info("🔁 UsersData: инициализация пула подключений к базе данных пользователей...")

                    logger.info(
                        f"[[UsersData].create] - 🔁 Попытка создания пула с параметрами:"
                        f"\nuser = {DB_USER}"
                        f"\npassword = {DB_PASSWORD}"
                        f"\nhost = {DB_HOST}"
                        f"\nport = {DB_PORT}"
                        f"\ndbname = {DB_NAME}"
                        f"\ntimeout = 120"
                    )

                    try:
                        pool = await asyncpg.create_pool(
                            user=DB_USER,
                            password=DB_PASSWORD,
                            host=DB_HOST,
                            port=DB_PORT,
                            timeout=120,
                            database=DB_NAME,
                            statement_cache_size=0
                        )
                    except Exception as err:
                        logger.error(f"[[UsersData].create] - ❌ Ошибка при создании пула подключения: {err}")
                        return None

                    cls._instance = cls(pool)
                    logger.info("[[UsersData].create] - ✅ UsersData: пул подключений успешно создан")

        return cls._instance

    # ====== Универсальный сеттер ======
    async def _update_field(self, user_id: int, field_name: str, value):
        allowed_fields = {
            'username', 'first_name', 'last_name', 'display_name_mod', 'icon_file_id',
            'first_login_date', 'access_lvl', 'warnings', 'total_messages', 'messages_today',
            'avg_messages_per_day', 'last_message_date', 'anime_name', 'last_update_anime_name',
            'admin_note', 'marital_status', 'marital_status_from', 'divorce_from', 'last_message_day'
        }

        if field_name not in allowed_fields:
            logger.warning(f"[_UpdateField] - 🔁 Попытка обновить недопустимое поле: {field_name}")
            return

        try:
            logger.violet(f"[_update_field] - 🔁 Обновление поля {field_name} для user_id={user_id}")

            async with self.pool.acquire() as connection:
                query = f'UPDATE chat_users SET {field_name} = $1 WHERE user_id = $2'
                await connection.execute(query, value, user_id)

            logger.violet(f"[_update_field] - ✅ Успешное обновление")
        except Exception as err:
            logger.error(f"[_UpdateField] - ❌ Ошибка при обновлении {field_name} для user_id={user_id}: {err}")

    # ====== Сеттеры ======
    async def set_username(self, user_id, username):
        logger.debug(f"[UserData] ✅ Установлено поле username для user_id={user_id}: {username}")
        await self._update_field(user_id, 'username', username)
        await Cache().delete(f"username:{user_id}")


    async def set_first_name(self, user_id, first_name):
        logger.debug(f"[UserData] ✅ Установлено поле first_name для user_id={user_id}: {first_name}")
        await self._update_field(user_id, 'first_name', first_name)

    async def set_last_name(self, user_id, last_name):
        logger.debug(f"[UserData] ✅ Установлено поле last_name для user_id={user_id}: {last_name}")
        await self._update_field(user_id, 'last_name', last_name)

    async def set_display_name_mod(self, user_id, display_name_mod):
        logger.debug(f"[UserData] ✅ Установлено поле display_name_mod для user_id={user_id}: {display_name_mod}")
        await self._update_field(user_id, 'display_name_mod', display_name_mod)

    async def set_icon_file_id(self, user_id, icon_file_id):
        logger.debug(f"[UserData] ✅ Установлено поле icon_file_id для user_id={user_id}: {icon_file_id}")
        await self._update_field(user_id, 'icon_file_id', icon_file_id)

    async def set_first_login_date(self, user_id, first_login_date):
        logger.debug(f"[UserData] ✅ Установлено поле first_login_date для user_id={user_id}: {first_login_date}")
        await self._update_field(user_id, 'first_login_date', first_login_date)

    async def set_access_lvl(self, user_id, access_lvl):
        logger.debug(f"[UserData] ✅ Установлено поле access_lvl для user_id={user_id}: {access_lvl}")
        await self._update_field(user_id, 'access_lvl', access_lvl)
        await Cache().delete(f"access_lvl:{user_id}")

    async def set_warnings(self, user_id, warnings):
        logger.debug(f"[UserData] ✅ Установлено поле warnings для user_id={user_id}: {warnings}")
        await self._update_field(user_id, 'warnings', warnings)

    async def set_total_messages(self, user_id, total_messages):
        logger.debug(f"[UserData] ✅ Установлено поле total_messages для user_id={user_id}: {total_messages}")
        await self._update_field(user_id, 'total_messages', total_messages)

    async def set_messages_today(self, user_id, messages_today):
        logger.debug(f"[UserData] ✅ Установлено поле messages_today для user_id={user_id}: {messages_today}")
        await self._update_field(user_id, 'messages_today', messages_today)

    async def set_avg_messages_per_day(self, user_id, avg_messages_per_day):
        logger.debug(
            f"[UserData] ✅ Установлено поле avg_messages_per_day для user_id={user_id}: {avg_messages_per_day}")
        await self._update_field(user_id, 'avg_messages_per_day', avg_messages_per_day)

    async def set_last_message_date(self, user_id):
        logger.debug(f"[UserData] ✅ Установлено поле last_message_date для user_id={user_id}")
        await self._update_field(user_id, 'last_message_date', datetime.datetime.now().utcnow())

    async def set_last_update_anime_name(self, user_id, last_update_anime_name):
        logger.debug(
            f"[UserData] ✅ Установлено поле last_update_anime_name для user_id={user_id}: {last_update_anime_name}")
        await self._update_field(user_id, 'last_update_anime_name', last_update_anime_name)

    async def set_admin_note(self, user_id, admin_note):
        logger.debug(f"[UserData] ✅ Установлено поле admin_note для user_id={user_id}: {admin_note}")
        await self._update_field(user_id, 'admin_note', admin_note)

    async def set_marital_status(self, user_id, marital_status):
        logger.debug(f"[UserData] ✅ Установлено поле marital_status для user_id={user_id}: {marital_status}")
        await self._update_field(user_id, 'marital_status', marital_status)

    async def set_marital_status_from(self, user_id, marital_status_from):
        logger.debug(
            f"[UserData] ✅ Установлено поле marital_status_from для user_id={user_id}: {marital_status_from}")
        await self._update_field(user_id, 'marital_status_from', marital_status_from)

    async def set_divorce_from(self, user_id, divorce_from):
        logger.debug(f"[UserData] ✅ Установлено поле divorce_from для user_id={user_id}: {divorce_from}")
        await self._update_field(user_id, 'divorce_from', divorce_from)

    # ====== Особые сеттеры ======
    async def set_anime_name(self, user_id: int):
        last_update = await self._get_field(user_id, 'last_update_anime_name')

        if last_update:
            try:
                last_update_dt = datetime.datetime.fromisoformat(last_update)
                time_diff = datetime.datetime.now() - last_update_dt
                if time_diff.total_seconds() < 60:
                    logger.debug(f"[SetAnimeName] - ⚠️ Аниме-имя user_id={user_id} обновлялось менее минуты назад.")
                    return
            except Exception as err:
                logger.error(f"[SetAnimeName] - ❌ Ошибка разбора даты обновления аниме-имени: {err}")

        anime_name = self.__generate_anime_name()
        now = datetime.datetime.now().isoformat()

        await self._update_field(user_id, 'anime_name', anime_name)
        await self._update_field(user_id, 'last_update_anime_name', now)

        logger.debug(f"[SetAnimeName] - ✅ Аниме-имя обновлено для user_id={user_id}: {anime_name}")
        return anime_name

    # ====== Универсальный геттер ======
    async def _get_field(self, user_id: int, field_name: str):
        try:
            # Строгая проверка допустимых полей
            allowed_fields = {
                'username', 'first_name', 'last_name', 'display_name_mod', 'icon_file_id',
                'first_login_date', 'access_lvl', 'warnings', 'total_messages', 'messages_today',
                'avg_messages_per_day', 'last_message_date', 'anime_name', 'last_update_anime_name',
                'admin_note', 'marital_status', 'marital_status_from', 'divorce_from', 'last_message_day'
            }

            if field_name not in allowed_fields:
                logger.warning(f"[UserData] ❌‼ Попытка доступа к недопустимому полю: {field_name}")
                return None

            async with self.pool.acquire() as connection:
                query = f"SELECT {field_name} FROM chat_users WHERE user_id = $1"
                result = await connection.fetchrow(query, user_id)
                return result[field_name] if result else None

        except Exception as err:
            logger.error(f"[UserData] ❌ Ошибка при получении поля {field_name} для user_id={user_id}: {err}")
            return None

    # ====== Геттеры ======
    async def get_user_base_info(self, user_id: int):
        fields = [
            "username", "first_name", "display_name_mod",
            "first_login_date", "access_lvl", "warnings",
            "total_messages", "avg_messages_per_day",
            "last_message_date", "anime_name", "admin_note",
            "messages_today"
        ]
        field_list = ", ".join(fields)

        try:
            async with self.pool.acquire() as connection:
                query = f"SELECT {field_list} FROM chat_users WHERE user_id = $1"
                result = await connection.fetchrow(query, user_id)
                return dict(result) if result else None
        except Exception as err:
            logger.error(f"[UserData] ❌ Ошибка при получении базовой информации для user_id={user_id}: {err}")
            return None

    async def get_user_id(self, username: str):
        try:
            async with self.pool.acquire() as connection:
                query = 'SELECT user_id FROM chat_users WHERE username = $1'
                result = await connection.fetchrow(query, username)
                return result['user_id'] if result else None
        except Exception as err:
            logger.error(f"[UserData] ❌ Ошибка при получении user_id по username='{username}': {err}")
            return None

    @cached(ttl=60, key_builder=lambda f, self, user_id: f"username:{user_id}")
    async def get_username(self, user_id):
        logger.debug(f"[UserData] ✅ Получение username для user_id={user_id}")
        return await self._get_field(user_id, 'username')

    async def get_first_name(self, user_id):
        logger.debug(f"[UserData] ✅ Получение first_name для user_id={user_id}")
        return await self._get_field(user_id, 'first_name')

    async def get_last_name(self, user_id):
        logger.debug(f"[UserData] ✅ Получение last_name для user_id={user_id}")
        return await self._get_field(user_id, 'last_name')

    async def get_display_name_mod(self, user_id):
        logger.debug(f"[UserData] ✅ Получение display_name_mod для user_id={user_id}")
        return await self._get_field(user_id, 'display_name_mod')

    async def get_icon_file_id(self, user_id):
        logger.debug(f"[UserData] ✅ Получение icon_file_id для user_id={user_id}")
        return await self._get_field(user_id, 'icon_file_id')

    async def get_first_login_date(self, user_id):
        logger.debug(f"[UserData] ✅ Получение first_login_date для user_id={user_id}")
        return await self._get_field(user_id, 'first_login_date')

    @cached(ttl=60, key_builder=lambda f, self, user_id: f"access_lvl:{user_id}")
    async def get_access_lvl(self, user_id):
        logger.debug(f"[UserData] ✅ Получение access_lvl для user_id={user_id}")
        value = await self._get_field(user_id, 'access_lvl')
        return int(value) if value is not None else 0

    async def get_warnings(self, user_id):
        logger.debug(f"[UserData] ✅ Получение warnings для user_id={user_id}")
        return await self._get_field(user_id, 'warnings')

    async def get_total_messages(self, user_id):
        logger.debug(f"[UserData] ✅ Получение total_messages для user_id={user_id}")
        return await self._get_field(user_id, 'total_messages')

    async def get_messages_today(self, user_id):
        logger.debug(f"[UserData] ✅ Получение messages_today для user_id={user_id}")
        return await self._get_field(user_id, 'messages_today')

    async def get_avg_messages_per_day(self, user_id):
        logger.debug(f"[UserData] ✅ Получение avg_messages_per_day для user_id={user_id}")
        return await self._get_field(user_id, 'avg_messages_per_day')

    async def get_last_message_date(self, user_id):
        logger.debug(f"[UserData] ✅ Получение last_message_date для user_id={user_id}")
        return await self._get_field(user_id, 'last_message_date')

    async def get_anime_name(self, user_id):
        logger.debug(f"[UserData] ✅ Получение anime_name для user_id={user_id}")
        return await self._get_field(user_id, 'anime_name')

    async def get_last_update_anime_name(self, user_id):
        logger.debug(f"[UserData] ✅ Получение last_update_anime_name для user_id={user_id}")
        return await self._get_field(user_id, 'last_update_anime_name')

    async def get_admin_note(self, user_id):
        logger.debug(f"[UserData] ✅ Получение admin_note для user_id={user_id}")
        return await self._get_field(user_id, 'admin_note')

    async def get_marital_status(self, user_id):
        logger.debug(f"[UserData] ✅ Получение marital_status для user_id={user_id}")
        return await self._get_field(user_id, 'marital_status')

    async def get_marital_status_from(self, user_id):
        logger.debug(f"[UserData] ✅ Получение marital_status_from для user_id={user_id}")
        return await self._get_field(user_id, 'marital_status_from')

    async def get_divorce_from(self, user_id):
        logger.debug(f"[UserData] ✅ Получение divorce_from для user_id={user_id}")
        return await self._get_field(user_id, 'divorce_from')

    async def get_user_id_by_username(self, username: str):
        logger.debug(f"[UserData] ✅ Получение user_id по username={username}")
        try:
            async with self.pool.acquire() as connection:
                query = "SELECT user_id FROM chat_users WHERE username = $1"
                result = await connection.fetchrow(query, username)
                return int(result['user_id']) if result else None
        except Exception as err:
            logger.error(f"[GetUserID] - ❌ Ошибка при получении user_id по username={username}: {err}")
            return None

    # ====== Добавление базовой информации юзера ======
    async def add_new_user(self, user_id: int, username: str, first_name: str, last_name: str, access_lvl: int = 0):
        try:
            async with self.pool.acquire() as connection:
                # Проверка существования пользователя
                check_query = "SELECT 1 FROM chat_users WHERE user_id = $1"
                exists = await connection.fetchrow(check_query, user_id)
                if exists:
                    logger.debug(f"[AddNewUser] - ⚠️ Пользователь user_id={user_id} уже существует.")
                    return

                # Вставка нового пользователя
                insert_query = """
                    INSERT INTO chat_users (user_id, username, first_name, last_name, access_lvl)
                    VALUES ($1, $2, $3, $4, $5)
                """
                await connection.execute(insert_query, user_id, username, first_name, last_name, access_lvl)

                logger.info(f"[AddNewUser] - ✅ Добавлен новый пользователь: user_id={user_id}")

            return user_id, username, first_name, last_name, access_lvl

        except Exception as err:
            logger.error(f"[AddNewUser] - ❌ Ошибка при добавлении нового пользователя user_id={user_id}: {err}")
            return None

    async def update_user_base_info(self, user_id: int, username: str, first_name: str, last_name: str):
        try:
            async with self.pool.acquire() as connection:
                query = """
                    INSERT INTO chat_users (user_id, username, first_name, last_name, access_lvl)
                    VALUES ($1, $2, $3, $4, 2)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name
                """
                await connection.execute(query, user_id, username, first_name, last_name)

                logger.debug(f"[update_user_base_info] - ✅ Обновлена/создана запись user_id={user_id}")
                return True

        except Exception as err:
            logger.error(f"[update_user_base_info] ❌ Ошибка: {err}")
            return False

    async def increment_message_count(self, user_id: int):
        today_date = datetime.datetime.utcnow().date()

        try:
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(
                    "SELECT last_message_day FROM chat_users WHERE user_id = $1",
                    user_id
                )
                last_day = row['last_message_day'] if row and row['last_message_day'] else None

                if last_day != today_date:
                    await connection.execute("""
                        UPDATE chat_users
                        SET messages_today = 1,
                            total_messages = total_messages + 1,
                            last_message_day = $1
                        WHERE user_id = $2
                    """, today_date, user_id)
                else:
                    await connection.execute("""
                        UPDATE chat_users
                        SET messages_today = messages_today + 1,
                            total_messages = total_messages + 1
                        WHERE user_id = $1
                    """, user_id)

                logger.violet(f"[increment_message_count] - ✅ Успешный коммит (автокоммит в asyncpg)")
                logger.debug(f"[UserData] ✅ Сообщения инкрементированы для user_id={user_id}")

        except Exception as err:
            logger.error(f"[increment_message_count] - ❌ Ошибка при инкременте сообщений для user_id={user_id}: {err}")

    async def add_warning_to_user(self, user_id: int, points: int = 1) -> tuple[int, bool]:
        """
        Добавляет предупреждения пользователю и проверяет, нужно ли банить.

        Возвращает:
            - итоговое количество предупреждений
            - True, если нужно банить (>= LIMIT_WARNINGS)
        """
        current = await self._get_field(user_id, 'warnings') or 0
        new_total = current + points

        await self._update_field(user_id, 'warnings', new_total)

        logger.debug(f"[WARNINGS] user_id={user_id} | было={current} | добавлено={points} | стало={new_total}")
        return new_total, new_total >= LIMIT_WARNINGS

    @staticmethod
    def get_days_in_chat(first_login_date: str) -> int:
        """
        Возвращает количество дней с момента первого входа.
        """
        try:
            first_login = datetime.datetime.fromisoformat(first_login_date)
            return (datetime.datetime.now() - first_login).days or 1
        except Exception as err:
            logger.error(f"[GetDaysInChat] ❌ Ошибка разбора даты: {err}")
            return 1  # Фолбэк, чтобы не упасть

    @staticmethod
    def __generate_anime_name() -> str:
        """
        Генерирует случайное аниме-имя на основе пола.
        """
        try:
            gender = random.choice(["m", "f"])
            adjective = random.choice(adjectives[gender])
            noun = random.choice(nouns[gender])
            return f"{adjective} {noun}"
        except Exception as err:
            logger.error(f"[GenerateAnimeName] ❌ Ошибка генерации имени: {err}")
            return "Сломанный Ёжик"


async def init_users_data_repository():
    """
    Инициализирует создание подключения к базе данных
    :return:
    """
    users_data_instance_repository = await UsersDataRepository.create()
    if users_data_instance_repository is None:
        logger.error("[init_users_data] - ❌ Ошибка: users_data не было создано!")
        return None

    logger.info("✅ Инициализация users_data успешна")
    return users_data_instance_repository

