import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from uvicorn.config import Config
from uvicorn.server import Server

from _configs import config_commands
from _configs.config import get_config, set_config
from _configs.config_io import load_config_from_file
from _configs.log_config import logger
from api.supabase_api import supabase_loading_icon, supabase_uploading_icon
from database import repositories
from database.anime_cache_repository import init_anime_cache_repository
from database.users_data_middleware import UsersDataMiddleware
from database.anime_cache_repository import AnimeCacheRepository
from database.users_data_repository import init_users_data_repository
from handlers import messages, chat_member, movies_commands, user_data_handlers
from handlers.carousels import carousel_handlers
from handlers.carousels import character_carousel_handlers
from handlers.commands import commands, admin_commands
from handlers.games import city_games_handlers
from handlers.inline_anime import inline_anime
from web_app.app import create_app

cfg = get_config()

TELEGRAM_API_TOKEN = cfg.tg_config.token

# ===============================================

async def start_web_server():
    """Асинхронный запуск FastAPI-сервера на фоне"""
    app = await create_app()

    config = Config(
        app=app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info",
        loop="asyncio",
        lifespan="off"
    )

    server = Server(config)
    await server.serve()

storage = MemoryStorage()

default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_API_TOKEN, default=default_properties)
dp = Dispatcher(storage=storage)


# Подключение роутов
dp.include_router(inline_anime.router)                          # Роут инлайн-аниме запросов
dp.include_router(chat_member.router)                           # Роут обработки вступления в группу
dp.include_router(commands.router)                              # Роут обычных команд
dp.include_router(city_games_handlers.router)                   # Роут обработки игры в города (не актуален)
dp.include_router(movies_commands.router)                       # Роут Anilist-запросов -- Работает (не актуален)
dp.include_router(carousel_handlers.router)                     # Роут обработки аниме-каруселей
dp.include_router(character_carousel_handlers.router)           # Роут обработки чарактер-карусеоей
dp.include_router(user_data_handlers.router)                    # Роут обработки команд профиля
dp.include_router(admin_commands.router)                        # Роут обработки команд модерации и администрирования
dp.include_router(supabase_loading_icon.router)
dp.include_router(supabase_uploading_icon.router)
dp.include_router(config_commands.router)
dp.include_router(messages.router)                              # Конечный Роут. Обработка текстовых команд. Обработка
                                                                # остаточных сообщений.


async def set_bot_commands():
    """Регистрация команд бота с иконками"""
    commands_set = [
        BotCommand(command="start", description="🔞 Начало работы с Ero no Sekai: Shinigami"),
        BotCommand(command="help", description="‼️ Помощь"),
        BotCommand(command="free_rules", description="📜 Правила бесплатной группы"),
        BotCommand(command="buy_rules", description="💎 Правила платной группы"),
        BotCommand(command="price_list", description="⚖️ Преимущества платного доступа"),
        BotCommand(command="policy", description="🔒 Политика конфиденциальности")
    ]
    await bot.set_my_commands(commands_set)

    logger.info(f"[set_bot_command] - Инициализация быстрых команд для бота")


async def on_startup():
    """Действия при запуске бота"""
    log_level = logger.getEffectiveLevel()
    log_levels = {
        5: 'JSON-DEBUG',
        10: 'DEBUG',
        20: 'INFO',
        30: 'WARNING',
        40: 'ERROR',
        50: 'CRITICAL'
    }
    log_level_str = log_levels.get(log_level, 'UNKNOWN')

    # === Инициализация users_data_repository ===
    try:
        logger.info("[Startup] - 🔁 Инициализация users_data_repository...")
        users_data_repository = await init_users_data_repository()
        if users_data_repository is None:
            raise RuntimeError("UsersDataRepository is None")
        repositories.set_users_data_repository(users_data_repository)
        logger.info("[Startup] - ✅ Регистрация users_data_repository")
    except Exception as err:
        logger.critical(f"[Startup] - ❌ Ошибка при инициализации users_data_repository: {err}")
        raise

    # === Подключение middleware ===
    try:
        logger.info("[Startup] - 🔁 Подключение UsersDataMiddleware...")
        dp.update.middleware(UsersDataMiddleware(users_data_repository))
        logger.info("[Startup] - ✅ UsersDataMiddleware подключён")
    except Exception as err:
        logger.critical(f"[Startup] - ❌ Ошибка при установке middleware: {err}")
        raise

    # === Инициализация anime_cache_repository ===
    try:
        logger.info("[Startup] - 🔁 Инициализация anime_cache_repository...")
        # проблема
        anime_cache_repository = await init_anime_cache_repository()
        if anime_cache_repository is None:
            raise RuntimeError("AnimeCacheRepository is None")
        repositories.set_anime_cache_repository(anime_cache_repository)
        await anime_cache_repository.export_cache_to_file()
        logger.info("[Startup][anime_cache_repository][export_cache_to_file] - ✅ Инициализация кэш файла")
        logger.info("[Startup] - ✅ Регистрация anime_cache_repository")
    except Exception as err:
        logger.critical(f"[Startup] - ❌ Ошибка при инициализации anime_cache_repository: {err}")
        raise


    # === Загрузка конфигурации ===
    try:
        logger.info("[Startup] - 🔁 Загрузка конфигурации...")
        set_config(load_config_from_file())
        logger.info("[Startup] - ✅ Конфигурация загружена")
    except Exception as err:
        logger.critical(f"[Startup] - ❌ Ошибка при загрузке конфигурации: {err}")
        raise

    # === Установка команд бота ===
    try:
        logger.info("[Startup] - 🔁 Установка команд бота...")
        await set_bot_commands()
        logger.info("[Startup] - ✅ Команды бота установлены")
    except Exception as err:
        logger.critical(f"[Startup] - ❌ Ошибка при установке команд бота: {err}")
        raise

    logger.info(f"[Startup] - ✅ Бот запущен. Уровень логирования: {log_level_str}")



async def main():
    await on_startup()

    web_task = asyncio.create_task(start_web_server())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    done, pending = await asyncio.wait(
        [web_task, bot_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()

    await bot.session.close()
    logger.info("[Main] - Все задачи завершены корректно.")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:

        logger.critical(f"[Main] - Критическая ошибка asyncio.run: {e}", exc_info=True)


# web: gunicorn web_app.run:app --bind 0.0.0.0:$PORT
# worker: python main.py
