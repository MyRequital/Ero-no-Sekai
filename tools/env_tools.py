import os
from _configs.log_config import logger
from typing import Callable, Any



def str_to_bool(value: str) -> bool:
    return value.lower() in ("true", "1", "yes", "on")


def get_env_var(
    key: str,
    required: bool = True,
    cast: Callable[[str], Any] = str,
    default=None
):
    """Получает переменную окружения с логированием, приведением типа и валидацией."""
    raw_value = os.getenv(key, default)

    logger.debug(f"🔍 Запрос переменной окружения: '{key}' (тип: {cast.__name__})")

    if raw_value is None:
        if required:
            logger.critical(f"❌ Обязательная переменная '{key}' не найдена и не имеет значения по умолчанию.")
            raise ValueError(f"Обязательная переменная окружения '{key}' не найдена.")
        else:
            logger.warning(f"⚠ Переменная '{key}' не найдена, используется default={default}")
            return default

    if default is not None and not isinstance(default, cast):
        logger.warning(
            f"⚠ Значение по умолчанию для '{key}' имеет тип {type(default).__name__}, "
            f"ожидался {cast.__name__}"
        )

    try:
        if cast is bool:
            value = str_to_bool(str(raw_value))
        else:
            value = cast(raw_value)

        if raw_value == default:
            logger.info(f"🟡 '{key}' = {value} (использовано значение по умолчанию)")
        else:
            logger.info(f"✅ '{key}' = {value} (получено из .env/окружения)")

        return value

    except (TypeError, ValueError) as e:
        logger.error(f"❌ Ошибка приведения переменной '{key}' к типу {cast.__name__}: {e}")
        raise ValueError(f"Переменная '{key}' не может быть приведена к типу {cast.__name__}")


def cast_to_int_list(raw: str) -> list[int]:
    return [int(i.strip()) for i in raw.split(",") if i.strip().isdigit()]



