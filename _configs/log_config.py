import logging
import inspect

# ====== Logger ======
LOGGER_LVL = 10

# Уровни логирования:
# 5  - JSON-DEBUG  (отладочная информация включая JSON логи)
# 10 - DEBUG       (подробная отладочная информация)
# 20 - INFO        (общая информация)
# 30 - WARNING     (предупреждения)
# 40 - ERROR       (ошибки)
# 50 - CRITICAL    (критические ошибки)

VIOLET = 5
logging.addLevelName(VIOLET, "VIOLET")

COLORS = {
    'DEBUG':    ('\033[94m', '\033[96m'),
    'INFO':     ('\033[32m', '\033[92m'),
    'WARNING':  ('\033[93m', '\033[93m'),
    'ERROR':    ('\033[91m', '\033[91m'),
    'CRITICAL': ('\033[91m', '\033[91m'),
    'VIOLET':   ('\033[35m', '\033[35m'),
}
RESET = '\033[0m'


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        level_color, msg_color = COLORS.get(record.levelname.strip(RESET), ('', ''))

        record.levelname = f"{level_color}{record.levelname}{RESET}"
        record.msg = f"{msg_color}{record.msg}{RESET}"
        record.name = f"\033[95m{record.name}{RESET}"

        return super().format(record)


console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(levelname)s - %(asctime)s - [%(name)s:%(lineno)d] - %(message)s'
))

root_logger = logging.getLogger()
root_logger.setLevel(LOGGER_LVL)
root_logger.addHandler(console_handler)

logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)


class ProxyLogger:
    def __getattr__(self, attr):
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        logger_name = module.__name__ if module else '__main__'
        real_logger = logging.getLogger(logger_name)
        return getattr(real_logger, attr)

def violet(self, msg, *args, **kwargs):
    if self.isEnabledFor(VIOLET):
        self._log(VIOLET, msg, args, **kwargs)

logging.Logger.violet = violet

logger = ProxyLogger()

__all__ = ['logger']