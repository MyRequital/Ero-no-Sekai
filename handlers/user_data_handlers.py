import os.path

from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from _configs.log_config import logger
from aiogram.types import BufferedInputFile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import random
from api.supabase_api.supabase_uploading_icon import get_users_avatar
from typing import Optional, Tuple
from _configs.config import get_config, AppConfig

cfg = get_config()
LIMIT_WARNINGS = cfg.bot_config.limit_warnings


router = Router()

@router.message(Command("me"))
async def send_me_profile(message: types.Message, users_data):
    user_id = int(message.from_user.id)
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    updated = await users_data.update_user_base_info(user_id, username, first_name, last_name)

    if not updated:
        await message.reply("❌ Не удалось обновить или создать профиль пользователя.")
        return

    person_data = await users_data.get_user_base_info(user_id)
    if not person_data:
        await message.reply("❌ Пользователь не найден.")
        return

    try:
        avatar_path = await get_users_avatar(user_id)

        image = generate_user_profile_image(person_data, LIMIT_WARNINGS, avatar_path)
        await message.answer_photo(BufferedInputFile(image, filename="profile.png"))

    except Exception as e:
        logger.exception(f"[send_me_profile] ⚠️ Ошибка генерации изображения: {e}")
        info = await combine_user_info(user_id, users_data)
        await message.reply(info)

@router.message(or_f(Command("whois"), Command("profile")))
async def send_user_profile(message: types.Message, command: F.CommandObject, users_data):
    if not command.args:
        await message.reply("❌ Укажите пользователя: /whois @username")
        return

    username = command.args.strip().lstrip("@")
    user_id = await users_data.get_user_id(username)

    if not user_id:
        await message.reply("❌ Пользователь не найден.")
        return

    person_data = await users_data.get_user_base_info(user_id)
    if not person_data:
        await message.reply("❌ Пользователь не найден.")
        return

    try:
        avatar_path = await get_users_avatar(user_id)

        image = generate_user_profile_image(person_data, LIMIT_WARNINGS, avatar_path)
        await message.answer_photo(BufferedInputFile(image, filename="profile.png"))
    except Exception as e:
        logger.warning(f"⚠️ Ошибка генерации изображения профиля для {user_id}: {e}")
        info = await combine_user_info(user_id, users_data)
        await message.reply(info)


# ====== Фолбэк-комбинатор текстового профиля ======
async def combine_user_info(user_id, users_data):
    person_data = await users_data.get_user_base_info(user_id)
    if not person_data:
        return "❌ Пользователь не найден."

    try:
        login_date = person_data['first_login_date']
        logger.debug(f"[combine_user_info] - Получение даты первого логина: {login_date}")
        days_in_group = (datetime.now() - login_date).days
        logger.debug(f"[combine_user_info] - Вычисление количества дней в группе: {days_in_group}")
    except Exception as err:
        logger.warning(f"[combine_user_info] - Ошибка: {err}. "
                       f"\nУстановлено количество дней в группе по-умолчанию, 0")
        days_in_group = 0

    if days_in_group > 0:
        messages_per_day = person_data['total_messages'] / days_in_group
    else:
        messages_per_day = person_data['total_messages']

    if days_in_group > 0:
        messages_per_day = person_data['total_messages'] / days_in_group
    else:
        messages_per_day = person_data['total_messages']

    base_info = (
        f"<b>👤 Имя:</b> <u>{person_data['first_name']}</u> (@{person_data['username']})"
        f"\n<b>📆 В группе с:</b> <code>{person_data['first_login_date']}</code> <i>({days_in_group} дн.)</i>"
        f"\n<b>🏷 Ник:</b> <i>{person_data['display_name_mod']}</i>"
        f"\n<b>🌸 Аниме-имя:</b> <i>{person_data['anime_name']}</i>"
        f"\n<b>🛡 Уровень доступа:</b> <code>{person_data['access_lvl']}</code>"
        f"\n<b>⚠️ Предупреждения:</b> <code>{person_data['warnings']}/{LIMIT_WARNINGS}</code>"
        f"\n<b>📈 Активность:</b> <code>{person_data['messages_today']} | {person_data['total_messages']} | {messages_per_day:.2f}</code> <i>(сегодня | всего | в день)</i>"
    )

    if person_data.get("admin_note"):
        base_info += (
            f"\n{'─' * 30}"
            f"\n<b>🗒 Запись админа:</b>\n<code>{person_data['admin_note']}</code>"
        )

    return base_info


AVATAR_BORDER_COLOR = "#000000"  # Цвет рамки (чёрный по умолчанию)

# 🅰️ Пути к шрифтам
FONTS_DIR = os.path.join("assets", "fonts")
FONT_NAMES = [
    "Adventure Indiana.ttf",
    "MolliWrites.ttf",
    "sfdistantgalaxycyrillic.ttf",
    "Harry Potter.ttf",
    "morpheus2_regularrus.otf", # Тест
    "anirm___.ttf"           # Тест

]

def generate_user_profile_image(person_data: dict, limit_warnings: int, avatar_path: Optional[str]) -> bytes:
    cfg = get_config()

    # 📐 Размеры
    image_width = cfg.user_profile_config.image_width
    image_height = cfg.user_profile_config.image_height
    image_padding = cfg.user_profile_config.image_padding
    text_spacing = cfg.user_profile_config.text_spacing

    avatar_width = cfg.user_profile_config.avatar_width
    avatar_height = cfg.user_profile_config.avatar_height
    avatar_padding_right = cfg.user_profile_config.avatar_padding_right
    avatar_padding_top = cfg.user_profile_config.avatar_padding_top
    avatar_border_width = cfg.user_profile_config.avatar_border_width

    # Размеры шрифтов
    font_regular_size = cfg.user_profile_config.font_regular_size
    font_title_size = cfg.user_profile_config.font_title_size
    font_note_size = cfg.user_profile_config.font_note_size

    # 🎲 Случайный шрифт
    font_name = random.choice(FONT_NAMES)
    font_path = os.path.join(FONTS_DIR, font_name)


    font_regular = get_font(font_path, font_regular_size)
    font_title = get_font(font_path, font_title_size)
    font_note = get_font(font_path, font_note_size)

    user_info, admin_note = build_user_info_dict(person_data, limit_warnings)

    img = Image.new("RGB", (image_width, image_height), "white")
    draw = ImageDraw.Draw(img)

    # 🎨 Фон
    top_color = random_light_color()
    bottom_color = random_light_color()
    draw_vertical_gradient(draw, image_width, image_height, top_color, bottom_color)

    # 🛡 Рамка
    access_lvl = int(user_info["Уровень доступа"])
    frame_color = next(
        (c for r, c in {
            range(0, 4): "#a0a0a0",
            range(4, 7): "#4682b4",
            range(7, 8): "#9370db",
            range(8, 9): "#daa520",
            range(9, 10): "#dcdcdc",
            range(10, 11): "#ff4c4c"
        }.items() if access_lvl in r),
        "#000000"
    )
    draw.rectangle([0, 0, image_width - 1, image_height - 1], outline=frame_color, width=8)

    # 👤 Аватарка
    avatar_x = image_width - avatar_width - avatar_padding_right
    avatar_y = avatar_padding_top

    if avatar_path and os.path.exists(avatar_path):
        try:
            avatar_img = Image.open(avatar_path).convert("RGBA")
            avatar_img = avatar_img.resize((avatar_width, avatar_height), Image.Resampling.LANCZOS)
            bordered_avatar = Image.new("RGBA", (avatar_width + 2 * avatar_border_width, avatar_height + 2 * avatar_border_width), AVATAR_BORDER_COLOR)
            bordered_avatar.paste(avatar_img, (avatar_border_width, avatar_border_width), avatar_img)
            img.paste(bordered_avatar, (avatar_x - avatar_border_width, avatar_y - avatar_border_width), bordered_avatar)
        except Exception as e:
            logger.warning(f"[generate_user_profile_image] - ⚠️ Не удалось вставить аватарку: {e}")

    # 📝 Текстовая часть слева от аватарки
    draw_dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    text_block_right_edge = avatar_x - image_padding
    text_block_width = text_block_right_edge - image_padding

    y = image_padding
    for label, value in user_info.items():
        text_line = f"{label}: {value}"
        wrapped_lines = wrap_text(text_line, font_regular, text_block_width, draw_dummy)
        for line in wrapped_lines:
            draw.text((image_padding, y), line, font=font_regular, fill="#111111")
            _, _, _, h = draw.textbbox((0, 0), line, font=font_regular)
            y += h + text_spacing

    # ✏️ Блок "Запись админа" (всегда внизу, на всю ширину)
    admin_block_y = max(y, avatar_y + avatar_height + image_padding)
    draw.text((image_padding, admin_block_y), "Запись админа:", font=font_title, fill="#800000")
    _, _, _, h_title = draw.textbbox((0, 0), "Запись админа:", font=font_title)
    y = admin_block_y + h_title + 10

    if admin_note:
        wrapped_note_lines = wrap_text(admin_note, font_note, image_width - 2 * image_padding, draw_dummy)
        for line in wrapped_note_lines:
            draw.text((image_padding, y), line, font=font_note, fill="#333333")
            _, _, _, h_line = draw.textbbox((0, 0), line, font=font_note)
            y += h_line + 4

    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.read()


# ====== Дополнительно ======
def get_font(path, size):
    return ImageFont.truetype(path, size)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current_line = [], ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def random_light_color() -> tuple:
    """Генерация случайного светлого цвета (RGB)"""
    return tuple(random.randint(180, 255) for _ in range(3))

def draw_vertical_gradient(draw: ImageDraw.Draw, width: int, height: int, top_color: tuple, bottom_color: tuple):
    """Рисует вертикальный градиент"""
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def build_user_info_dict(person_data: dict, limit_warnings: int) -> Tuple[dict, str]:
    try:
        login_date = person_data['first_login_date']
        days_in_group = (datetime.now() - login_date).days
    except Exception as err:
        logger.warning(f"[build_user_info_dict] - ⚠️ Ошибка: {err}. Установлено количество дней по умолчанию")
        days_in_group = 0

    messages_per_day = (
        person_data['total_messages'] / days_in_group
        if isinstance(days_in_group, int) and days_in_group > 0
        else person_data['total_messages']
    )

    admin_note = person_data.get("admin_note", "").strip()

    user_info = {
        "Имя": f"{person_data['first_name']} (@{person_data['username']})",
        "В группе с": f"{person_data['first_login_date']} ({days_in_group} дн.)",
        "Ник": person_data['display_name_mod'],
        "Аниме-имя": person_data['anime_name'],
        "Уровень доступа": str(person_data['access_lvl']),
        "Предупреждения": f"{person_data['warnings']}/{limit_warnings}",
        "Сообщений сегодня": str(person_data['messages_today']),
        "Всего сообщений": str(person_data['total_messages']),
        "Среднее в день": f"{messages_per_day:.2f}"
    }

    return user_info, admin_note
