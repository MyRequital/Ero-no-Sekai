from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from api.shikimori_api.shikimori_requests import send_data_character
from _configs.log_config import logger
from handlers.carousels.carousel_handlers import remove_character_tags
from tools.common_utils import delete_message_safe
import re
import asyncio

router = Router()


@router.message(Command("ssc"))
async def character_carousel_entry(message: types.Message, state: FSMContext, users_data, **kwargs):
    try:
        logger.debug("[CharacterCarouselEntry] – вход в хендлер, text=%r, from_id=%s",
                     message.text, message.from_user.id)

        args = message.text.split(" ", 1)
        logger.debug("[CharacterCarouselEntry] – split args -> %r (types: %s)",
                     args, [type(a).__name__ for a in args])

        if len(args) < 2:
            logger.debug("[CharacterCarouselEntry] – нет аргумента после /ssc, отвечаю подсказкой")
            await message.reply(
                "👤 Укажи имя персонажа после команды, например:\n<code>/ssc Rem</code>",
                parse_mode="HTML"
            )
            return

        name = args[1].strip()
        logger.debug("[CharacterCarouselEntry] – получено имя %r (тип %s)", name, type(name).__name__)

        mes = await message.answer(f"🔍 Ищу персонажей по имени: {name}...")
        logger.debug("[CharacterCarouselEntry] – отправлено 'ищу...', msg_id=%s", getattr(mes, "message_id", None))
        if mes:
            _ = await asyncio.create_task(delete_message_safe(mes, 5))

        try:
            logger.debug("[CharacterCarouselEntry] – вызываю send_data_character(%r)", name)
            character_data = send_data_character(name)
            logger.debug("[CharacterCarouselEntry] – send_data_character вернул: %r (тип %s)",
                         character_data, type(character_data).__name__)
        except Exception as e:
            logger.error("[CharacterCarouselEntry] – Ошибка в send_data_character: %r (тип %s)",
                         e, type(e).__name__)
            raise

        characters = character_data.get("data", {}).get("characters", [])
        logger.debug("[CharacterCarouselEntry] – сырые characters: len=%d, %r",
                     len(characters), characters)
        characters = [char for char in characters if char is not None]
        logger.debug("[CharacterCarouselEntry] – отфильтрованные characters: len=%d", len(characters))

        if not characters:
            logger.debug("[CharacterCarouselEntry] – список пуст, отвечаю 'не найдены'")
            await message.reply("😕 Персонажи не найдены.")
            return

        data = await state.get_data()
        logger.debug("[CharacterCarouselEntry] – FSM до удаления: %r", data)
        last_msg_id = data.get("char_carousel_last_message_id")
        logger.debug("[CharacterCarouselEntry] – last_msg_id = %r", last_msg_id)
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
                logger.debug("[CharacterCarouselEntry] – удалено сообщение %s", last_msg_id)
            except Exception as e:
                logger.warning("[CharacterCarouselEntry] – не удалось удалить старое сообщение %s: %s",
                               last_msg_id, e)

        new_carousel = {
            "characters": characters,
            "total": len(characters),
            "current_index": 0,
            "owner_id": message.from_user.id
        }
        await state.update_data(char_carousel=new_carousel, char_carousel_last_message_id=None)
        data_after = await state.get_data()
        logger.debug("[CharacterCarouselEntry] – FSM после update: %r", data_after)

        await send_character_carousel_item(message, state)
        logger.debug("[CharacterCarouselEntry] – успешно отправил первый элемент карусели")

    except Exception as e:
        logger.exception(f"[CharacterCarouselEntry] – фатальная ошибка в обработчике /ssc: {e}")
        await message.reply("⚠️ Ошибка при поиске персонажей. Попробуй позже.")


async def send_character_carousel_item(message: types.Message | types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    carousel = data.get("char_carousel", {})
    characters = carousel.get("characters", [])
    index = carousel.get("current_index", 0)
    total = carousel.get("total", 0)

    if not characters or index >= total:
        await message.answer("😵 Не удалось отобразить персонажа.")
        return

    char = characters[index]
    if not isinstance(char, dict):
        await message.answer("⚠️ Ошибка: некорректный персонаж. Пропускаю...")
        return

    name = char.get("russian") or char.get("name", "Неизвестно")
    description = (char.get("description") or "Описание отсутствует").strip()

    logger.debug("[send_character_carousel_item] Описание до обработки:\n%s", description)

    description = remove_character_tags(description).replace("<br>", "\n")
    description = convert_spoilers(description)
    logger.debug("[send_character_carousel_item] После convert_spoilers:\n%s", description)

    description = escape_md2_preserving_spoilers(description)
    logger.debug("[send_character_carousel_item] После escape_md2_preserving_spoilers:\n%s", description)

    description = safe_truncate_md2(description, 600)
    if description.endswith("..."):
        description = description[:-3] + "\\.\\.\\."

    url = char.get("url", "")
    image_url = char.get("poster", {}).get("originalUrl", "")

    origin = char.get("origin")
    if origin:
        type_map = {
            'anime': 'Аниме',
            'manga': 'Манга',
            'ranobe': 'Ранобэ'
        }
        kind = type_map.get(origin.get("type"), origin.get("type"))
        kind = escape_md2(kind)
        origin_name = escape_md2(origin.get("name", ""))
        origin_url = origin.get("url", "")
        origin_line = f"🎬 *Источник:* {kind} [{origin_name}]({origin_url})"
    else:
        origin_line = "🎬 *Источник:* не найден"

    name = escape_md2(name)

    caption = (
        f"👤 *{name}*\n\n"
        f"📝 *Описание:*\n{description}\n\n"
        f"{origin_line}\n\n"
        f"🔗 [Профиль на Shikimori]({url})"
    )

    logger.debug(f"[Caption Length] {len(caption)} / 1024")
    logger.debug("[send_character_carousel_item] Финальный caption перед отправкой:\n%s", caption)

    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️", callback_data="char_carousel:prev"),
        InlineKeyboardButton(text=f"{index + 1}/{total}", callback_data="char_carousel:noop"),
        InlineKeyboardButton(text="➡️", callback_data="char_carousel:next")
    ]])

    if isinstance(message, types.CallbackQuery):
        try:
            await message.message.edit_media(
                media=InputMediaPhoto(media=image_url, caption=caption, parse_mode="MarkdownV2"),
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"[CarouselItem] - Ошибка: {e}")
            await message.answer(f"⚠️ Ошибка обновления: {e}")
    else:
        msg = await message.answer_photo(
            photo=image_url,
            caption=caption,
            parse_mode="MarkdownV2",
            reply_markup=markup
        )
        await state.update_data(char_carousel_last_message_id=msg.message_id)


@router.callback_query(F.data.startswith("char_carousel:"))
async def handle_character_carousel(callback: types.CallbackQuery, state: FSMContext):
    try:
        _, direction = callback.data.split(":")
        data = await state.get_data()
        carousel = data.get("char_carousel", {})
        owner_id = carousel.get("owner_id")

        if owner_id != callback.from_user.id:
            await callback.answer("Это чужая карусель. Создай свою командой /ssc ✨", show_alert=True)
            return

        total = carousel.get("total", 0)
        index = carousel.get("current_index", 0)
        characters = carousel.get("characters", [])

        if not characters:
            await callback.answer("🥲 Карусель пуста. Попробуй ещё раз.")
            return

        if direction == "prev":
            index = (index - 1) % total
        elif direction == "next":
            index = (index + 1) % total
        else:
            await callback.answer()
            return

        await state.update_data(
            char_carousel={
                "characters": characters,
                "total": total,
                "current_index": index,
                "owner_id": owner_id
            }
        )

        await send_character_carousel_item(callback, state)

    except Exception as e:
        logger.error(f"[CharacterCarouselHandler] - {e}")
        await callback.answer(f"⚠️ Ошибка: {str(e)}"
                              f"\nP.S. Если это ошибка MESSAGE_TOO_LONG, не беспокойтесь и просто забейте :)", show_alert=True)
    finally:
        await callback.answer()


# ====== Дополнительно ======
def escape_md2(text: str) -> str:
    """
    Экранирует спецсимволы для MarkdownV2,
    оставляя '|' нетронутым (чтобы ||спойлер|| работал),
    но экранируя точку.
    """
    escaped = re.sub(r'([_*\[\]()~`>#+=\-{}.!\\])', r'\\\1', text)
    logger.debug("[escape_md2] Экранированный текст:\n%s", escaped)
    return escaped

def escape_md2_preserving_spoilers(text: str) -> str:
    parts = re.split(r'(\|\|.*?\|\|)', text, flags=re.DOTALL)
    escaped_parts = []

    for part in parts:
        if part.startswith("||") and part.endswith("||"):
            inner = part[2:-2]
            escaped_inner = escape_md2(inner)
            escaped_parts.append(f"||{escaped_inner}||")
        else:
            escaped_parts.append(escape_md2(part))

    return ''.join(escaped_parts)


def convert_spoilers(text: str) -> str:
    """
    Заменяет [spoiler=заголовок]текст[/spoiler] на ||текст|| без экранирования,
    чтобы экранирование происходило один раз — после.
    """
    return re.sub(r'\[spoiler(=.+?)?\](.*?)\[/spoiler\]', lambda m: f"||{m.group(2).strip()}||", text, flags=re.DOTALL)


def safe_truncate_md2(text: str, limit: int = 1000) -> str:
    """
    Безопасно обрезает текст с экранированными символами для MarkdownV2,
    чтобы не разрезать спойлеры или экранирование.
    """
    result = ""
    length = 0
    in_spoiler = False
    i = 0

    while i < len(text) and length < limit:
        char = text[i]
        if text[i:i+2] == "||":
            in_spoiler = not in_spoiler
            result += "||"
            i += 2
            continue
        if char == "\\" and i + 1 < len(text):
            result += text[i:i+2]
            i += 2
            length += 1
        else:
            result += char
            i += 1
            length += 1

    if in_spoiler:
        result += "||"
    if i < len(text):
        result += "..."

    return result

