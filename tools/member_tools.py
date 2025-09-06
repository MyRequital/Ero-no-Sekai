from datetime import datetime
import inspect
import os
from _configs.log_config import logger

from _configs.config import get_config

cfg = get_config()

DEV_ID_LIST = cfg.bot_config.dev_id_list
logger.debug(f"[member_tools] - Список айди разработчиков {DEV_ID_LIST}")


async def send_dev_log(bot, message: str):

    frame = inspect.stack()[1]
    filename = os.path.basename(frame.filename)
    lineno = frame.lineno
    func_name = frame.function

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_text = (
        f"{now} - {message}"
    )

    for dev_id in DEV_ID_LIST:
        try:
            await bot.send_message(dev_id, log_text)
        except Exception as e:
            logger.error(f"Не удалось отправить лог {dev_id}: {e}")
