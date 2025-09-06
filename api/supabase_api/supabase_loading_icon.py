import os.path
import time
from contextlib import suppress
from pathlib import Path

from PIL import Image
from aiofiles import open as aio_open
from aiogram import Router, F
from aiogram.filters import Command, or_f
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiohttp import ClientSession

from _configs.config import get_config, BASE_DIR
from _configs.log_config import logger
from services.supabase.supabase_instance import supabase_client
from tools.common_utils import require_access

router = Router()

cfg = get_config()

# 📐 Настройки изображения аватарки
AVATAR_WIDTH = 200                   # Ширина аватарки
AVATAR_HEIGHT = 350                  # Высота аватарки

@router.message(or_f(Command("spi"), Command("set_profile_icon")))
@require_access(8)
async def set_profile_icon(message: Message, command: F.CommandObject, users_data):
    if not message.photo:
        await message.reply("❌ Пожалуйста, приложи фото к сообщению с командой.")
        return

    args = command.args
    if args:
        parts = args.split()
        if len(parts) != 1:
            await message.reply("⚠️ Неверный формат. Пример: /spi @username")
            return
        username = parts[0].lstrip("@")

        # Получение ID цели по username
        target_user_id = await users_data.get_user_id(username)
        if not target_user_id:
            await message.reply("⚠️ Не удалось найти пользователя.")
            return
        target_username = f"@{username}"
    else:
        target_user_id = message.from_user.id
        target_username = (
            f"@{message.from_user.username}"
            if message.from_user.username else "Вы"
        )

    # 🔁 Обработка фото
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path

    temp_path = Path(cfg.cache_config.temp_file_path)

    await message.bot.download_file(file_path, destination=temp_path)

    try:
        with Image.open(temp_path) as img:
            img = img.convert("RGB")

            img.thumbnail((AVATAR_WIDTH, AVATAR_HEIGHT), Image.Resampling.LANCZOS)

            img.save(temp_path)
    except Exception as e:
        logger.error(f"[set_profile_icon] ⚠️ Ошибка обработки изображения: {e}")
        await message.reply("⚠️ Ошибка обработки изображения.")
        return

    # ⬆ Выгрузка в Supabase
    supabase_url = await supabase_client.upload_avatar(
        user_id=target_user_id,
        file_path=temp_path
    )

    # 🔁 Обновление кэша
    try:

        avatar_cache_path = os.path.join(
            BASE_DIR, "assets", "users_icon_avatars", f"{target_user_id}.jpg"
        )
        public_url = f"{supabase_url}?v={int(time.time())}"

        async with ClientSession() as session:
            async with session.get(public_url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    async with aio_open(avatar_cache_path, "wb") as f:
                        await f.write(image_bytes)
                else:
                    logger.warning(f"[set_profile_icon] ⚠️ Не удалось обновить кэш аватарки: статус {response.status}")
    except Exception as e:
        logger.error(f"[set_profile_icon] ⚠️ Ошибка при обновлении кэша аватарки: {e}")

    await message.reply(
        f"✅ Аватарка пользователя {hbold(target_username)} обновлена.\n"
        f"<a href=\"{supabase_url}\">&#8205;</a>"
    )

    with suppress(Exception):
        temp_path.unlink()