import os
import time
from pathlib import Path

import aiohttp
from aiofiles import open as aio_open
from aiofiles.os import path as aio_path
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from _configs.config import BASE_DIR
from _configs.log_config import logger
from services.supabase.supabase_instance import supabase_client

CACHE_AVATARS = os.path.join(BASE_DIR, 'assets', 'users_icon_avatars')


router = Router()

@router.message(Command("test_icon"))
async def test_icon_handler(message: Message, users_data):
    target_user_id = message.from_user.id
    target_username = None

    if message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                target_username = message.text[entity.offset: entity.offset + entity.length]
                break

    if target_username:
        resolved_id = await users_data.get_user_id_by_username(target_username)
        if resolved_id:
            target_user_id = resolved_id
        else:
            await message.reply("❌ Не удалось найти пользователя.")
            return

    try:
        base_url = supabase_client.client.storage \
            .from_("shinigami-users-avatars") \
            .get_public_url(f"avatars/{target_user_id}.jpg")

        # Суффикс для обхода кэша
        avatar_url = f"{base_url}?v={int(time.time())}"

        await message.answer_photo(
            photo=avatar_url,
            caption=f"Аватарка пользователя {target_username or 'текущего'}"
        )
        return

    except Exception as e:
        fallback_path = os.path.join(BASE_DIR, "assets", "users_icon_avatars", "default.jpg")

        if not os.path.exists(fallback_path):
            await message.reply("Аватарка не найдена, и заглушка отсутствует.")
            return

        await message.answer_photo(
            photo=FSInputFile(fallback_path),
            caption=f"Заглушка для пользователя {target_username or 'текущего'}"
        )


async def get_users_avatar(user_id: int | str) -> str:
    avatar_filename = f"{user_id}.jpg"
    avatar_path = os.path.join(CACHE_AVATARS, avatar_filename)

    # ✅ Проверка на кэш
    if await aio_path.exists(avatar_path):
        return avatar_path

    try:
        # 🛰️ Получение URL из Supabase
        base_url = supabase_client.client.storage \
            .from_("shinigami-users-avatars") \
            .get_public_url(f"avatars/{user_id}.jpg")

        avatar_url = f"{base_url}?v={int(time.time())}"

        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status == 200 and content_type.startswith("image/"):
                    image_bytes = await response.read()

                    Path(CACHE_AVATARS).mkdir(parents=True, exist_ok=True)
                    async with aio_open(avatar_path, "wb") as f:
                        await f.write(image_bytes)

                    return avatar_path
                else:
                    raise ValueError(f"❌ Файл недоступен или не изображение. Статус: {response.status}, Тип: {content_type}")

    except Exception as e:
        logger.warning(f"[get_users_avatar] - ❌ Ошибка загрузки аватарки для {user_id}, используется заглушка. Ошибка: {e}")

        fallback_path = os.path.join(CACHE_AVATARS, "default.jpg")

        # ✅ Кэшируем заглушку при первом обращении
        if not await aio_path.exists(fallback_path):
            default_source_path = os.path.join(BASE_DIR, "assets", "users_icon_avatars", "default.jpg")
            try:
                async with aio_open(default_source_path, "rb") as src:
                    default_bytes = await src.read()
                async with aio_open(fallback_path, "wb") as dst:
                    await dst.write(default_bytes)
            except Exception as file_error:
                logger.error(f"[get_users_avatar] - ❌ Ошибка при кэшировании fallback аватара: {file_error}")
                return default_source_path  # В крайнем случае — путь к исходнику

        return fallback_path