import json
import os.path
from pathlib import Path
from _configs.config import AppConfig, BotConfig
from _configs.log_config import logger
from _configs.config import get_config, BASE_DIR

CONFIG_PATH = Path(os.path.join(BASE_DIR, "_configs", "config.json"))


def load_config_from_file() -> AppConfig:
    if not CONFIG_PATH.exists():
        logger.warning(f"[config_io] ⚠️ Файл конфигурации не найден. Создаю шаблон по пути: {CONFIG_PATH}")
        try:
            default_config = AppConfig()
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(
                json.dumps(default_config.model_dump(), indent=4, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"[config_io] ❌ Не удалось создать config.json: {e}")
            raise RuntimeError("Невозможно продолжить без файла конфигурации")

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return AppConfig(**data)
    except Exception as e:
        logger.error(f"[config_io] ❌ Ошибка чтения config.json: {e}")
        raise RuntimeError(f"Ошибка загрузки конфигурации: {e}")


def save_config_to_file(cfg: AppConfig) -> None:
    try:
        json_data = json.dumps(cfg.model_dump(), indent=4, ensure_ascii=False)
        CONFIG_PATH.write_text(json_data, encoding="utf-8")
    except Exception as e:
        logger.error(f"[config_io] Ошибка записи JSON: {e}")