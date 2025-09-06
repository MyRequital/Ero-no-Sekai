""" _configs/config.py — конфигурация для Telegram-бота и внешних API с логированием."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
from pydantic import field_validator
from typing import List, Any


from _configs.log_config import logger
from pathlib import Path
import json


load_dotenv()
logger.debug(".env файл загружен")

BASE_DIR = Path(__file__).resolve().parent.parent

logger.info(f"Базовая директория {BASE_DIR}")

# 📄 Путь к config.json
CONFIG_PATH = BASE_DIR / "_configs" / "config.json"

class CommonSettings(BaseSettings):
    class Config:
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    logger.info(f"[CommonSettings(BaseSettings)] - Создан")


# ====== Telegram Config ======
class TelegramConfig(CommonSettings):
    token: str = Field(..., alias="TELEGRAM_API_TOKEN")                          # Телеграм API токен
    logger.info(f"[TelegramConfig] - Зарегистрирован")

    model_config = SettingsConfigDict(extra="ignore")


# ====== Конфиги бота ======
class BotConfig(CommonSettings):
    timer_removal: int = 120             # Таймер для удаления сообщения бота
    ban_days: int = 1                    # Дни бана за маты
    access_cache_ttl: int = 600          # Время хранения кэша прав доступа (в секундах)

    # ====== Warnings ======
    limit_warnings: int = 10  # Ограничение предупреждений для бана

    group_id: int = Field(..., alias="GROUP_ID")                                 # ID рабочей группы
    group_url: str = Field(..., alias="GROUP_URL")


    dev_id_list: List[str] = Field(..., alias="DEV_ID_LIST")                                    # Список отладчиков (Отсылка логов в лс)
    actual_staff_nick_list: str = Field(..., alias="ACTUAL_STAFF_NICK_LIST")                    # Список администрации и модерации чата (команда /staff)

    bot_name: str = Field(..., alias="BOT_NAME")
    bot_url: str = Field(..., alias="BOT_URL")
    bot_username: str = Field(..., alias="BOT_USERNAME")

    site_url: str = r"https://ero-no-sekai.up.railway.app/"


    logger.info(f"[BotConfig] - Зарегистрирован")

    model_config = SettingsConfigDict(extra="ignore")

# ====== Пути кэш файлов ======
class CacheConfig(CommonSettings):
    # ====== Путь к аниме кэшу по id ======
    anime_cache_path: str = os.path.join(BASE_DIR, "_cache", "anime_cache", "anime_cache.json")
    logger.debug(f"[CacheConfig] - Путь аниме кэша по id при инициализации -> {anime_cache_path}")

    # ====== Путь к аниме кэшу по названию ======
    anime_cache_by_name_path: str = os.path.join(BASE_DIR, "_cache", "anime_cache", "anime_cache_by_name.json")
    logger.debug(f"[CacheConfig] - Путь аниме кэша по названию при инициализации -> {anime_cache_by_name_path}")

    # ====== Путь к temp ======
    temp_file_path: str = os.path.join(BASE_DIR, "_cache", "temp")
    logger.debug(f"[CacheConfig] - Путь к temp -> {temp_file_path}")

    model_config = SettingsConfigDict(extra="ignore")


# ====== Weather API ======
class WeatherApiConfig(CommonSettings):
    weather_token: str = Field(..., alias="WEATHER_TOKEN")
    logger.info(f"[WeatherApiConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== Shikimori API ======
class ShikimoriApiConfig(CommonSettings):
    rest_url: str = "https://shikimori.one/api/characters/{id}"
    gql_url: str = "https://shikimori.one/api/graphql"

    user_agent: str = Field(..., alias="SHIKIMORI_HEADERS_USER_AGENT")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    logger.info(f"[ShikimoriApiConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== Kinopoisk API ======
class KinopoiskAPIConfig(CommonSettings):
    kp_url: str = "https://api.kinopoisk.dev/v1.4/movie"
    kp_token: str = Field(..., alias="KINOPOISK_API_TOKEN")

    @property
    def kp_headers(self) -> dict[str, str]:
        return {
            'accept': 'application/json',
            'X-API-KEY': self.kp_token
        }

    logger.info(f"[KinopoiskAPIConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")



# ====== Retry logic ======
class RetryLogicConfig(CommonSettings):
    max_retries_for_characters: int = 3         # Максимальное количество дозапросов к character
    retry_delay_for_characters: float = 1.0     # Задержка между дозапросами
    logger.info(f"[RetryLogicConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== Database ======
class DatabaseConfig(CommonSettings):
    db_path: str = "../database/bot_data.db"         # Путь к БД
    auto_commit_interval_minutes: int = 15           # Таймер для авто-обновления БД

    db_user: str = Field(..., alias="DB_USER")
    db_password: str = Field(..., alias="DB_PASSWORD")
    db_host: str = Field(..., alias="DB_HOST")
    db_port: str = Field(..., alias="DB_PORT")
    db_name: str = Field(..., alias="DB_NAME")

    cache_db_user: str = Field(..., alias="CACHE_DB_USER")
    cache_db_password: str = Field(..., alias="CACHE_DB_PASSWORD")
    cache_db_host: str = Field(..., alias="CACHE_DB_HOST")
    cache_db_port: str = Field(..., alias="CACHE_DB_PORT")
    cache_db_name: str = Field(..., alias="CACHE_DB_NAME")

    ssl_cert_path: str = str(BASE_DIR / ".dev" / "supabase-ca.crt")  # Просто путь

    def read_ssl_certificate(self) -> bytes:
        """
        Читает содержимое SSL-сертификата в бинарном виде.
        :return: bytes
        """
        try:
            with open(self.ssl_cert_path, "rb") as cert_file:
                content = cert_file.read()
                logger.violet(f"SSL сертификат успешно прочитан ({self.ssl_cert_path})")
                return content
        except FileNotFoundError:
            logger.error(f"❌ Файл SSL сертификата не найден: {self.ssl_cert_path}")
            return b""
        except Exception as e:
            logger.error(f"❌ Ошибка при чтении SSL сертификата: {e}")
            return b""

    logger.info(f"[DatabaseConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== SUPABASE ======
class SupabaseConfig(CommonSettings):
    storage_service_role_key: str = Field(..., alias="STORAGE_SERVICE_ROLE_KEY")
    storage_url: str = Field(..., alias="STORAGE_URL")

    logger.info(f"[SupabaseConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== UserProfileConfig ======
class UserProfileConfig(CommonSettings):
    image_width: int = 1200          # Размер изображения чат-профиля
    image_height: int = 850
    image_padding: int = 40         # Отступы по краям
    text_spacing: int = 18          # Отступы меж строк

    avatar_width: int = 350         # Ширина аватарки
    avatar_height: int = 350        # Высота аватарки
    avatar_padding_right: int = 20  # Отступ аватарки справа
    avatar_padding_top: int = 20    # Отступ аватарки сверху
    avatar_border_width: int = 2    # Ширина обводки аватарки

    font_regular_size: int = Field(default=30, ge=10, le=100)       # Размер шрифта текста профиля
    font_title_size: int = Field(default=26, ge=10, le=100)
    font_note_size: int = Field(default=28, ge=10, le=100)

    logger.info(f"[UserProfileConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")


# ====== DeveloperConfig ======
class DeveloperConfig(CommonSettings):
    dev_username: str = Field(..., alias="DEV_USERNAME")
    dev_url: str = Field(..., alias="DEV_URL")

    logger.info(f"[DeveloperConfig] - Зарегистрирован")
    model_config = SettingsConfigDict(extra="ignore")

# ====== WebApp Config ======
class WebAppConfig(CommonSettings):
    kodik_token: str = Field(..., alias="KODIK_TOKEN")                          # Kodik API токен
    logger.info(f"[WebAppConfig] - Зарегистрирован")

    model_config = SettingsConfigDict(extra="ignore")


class AppConfig(BaseModel):
    tg_config: TelegramConfig
    bot_config: BotConfig
    weather_config: WeatherApiConfig
    shikimori_config: ShikimoriApiConfig
    retry_logic_config: RetryLogicConfig
    database_config: DatabaseConfig
    supabase_config: SupabaseConfig
    user_profile_config: UserProfileConfig
    dev_config: DeveloperConfig
    web_app_config: WebAppConfig
    cache_config: CacheConfig
    kp_config: KinopoiskAPIConfig

    logger.info(f"[AppConfig] - Зарегистрирован")


# ====== Загрузка из JSON ======
def load_config_from_json(path: Path) -> AppConfig:
    if not path.exists():
        logger.warning("[load_config_from_json] config.json не найден. Загрузка значений из .env и создание нового...")

        cfg = AppConfig(
            tg_config=TelegramConfig(),
            bot_config=BotConfig(),
            weather_config=WeatherApiConfig(),
            shikimori_config=ShikimoriApiConfig(),
            retry_logic_config=RetryLogicConfig(),
            database_config=DatabaseConfig(),
            supabase_config=SupabaseConfig(),
            user_profile_config=UserProfileConfig(),
            dev_config=DeveloperConfig(),
            web_app_config=WebAppConfig(),
            cache_config=CacheConfig(),
            kp_config=KinopoiskAPIConfig(),
        )

        save_config_to_json(cfg, path)
        logger.info("[load_config_from_json] config.json успешно создан из .env")
        return cfg

    try:
        with path.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)

        config = AppConfig.model_validate(raw_data)
        logger.info("[load_config_from_json] Конфигурация успешно загружена из config.json")
        return config

    except (ValidationError, json.JSONDecodeError) as e:
        logger.error(f"[load_config_from_json] Ошибка при загрузке config.json: {e}")
        logger.warning("[load_config_from_json] Перегрузка из .env и пересохранение config.json")

        cfg = AppConfig(
            tg_config=TelegramConfig(),
            bot_config=BotConfig(),
            weather_config=WeatherApiConfig(),
            shikimori_config=ShikimoriApiConfig(),
            retry_logic_config=RetryLogicConfig(),
            database_config=DatabaseConfig(),
            supabase_config=SupabaseConfig(),
            user_profile_config=UserProfileConfig(),
            web_app_config=WebAppConfig(),
            cache_config=CacheConfig(),
            kp_config=KinopoiskAPIConfig(),
        )

        save_config_to_json(cfg, path)
        return cfg


def save_config_to_json(cfg: AppConfig, path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(cfg.model_dump(), f, indent=4, ensure_ascii=False)
        logger.info(f"[save_config_to_json] Конфиг успешно сохранён -> {path}")
    except Exception as e:
        logger.error(f"[save_config_to_json] Ошибка записи config.json: {e}")


# 🔁 Текущее состояние конфига
_bot_cfg: AppConfig = load_config_from_json(CONFIG_PATH)

def get_config() -> AppConfig:
    """

    :rtype: object
    """
    return _bot_cfg

def set_config(new_config: AppConfig) -> None:
    global _bot_cfg
    _bot_cfg = new_config


logger.info("Конфигурация успешно загружена ✅")
