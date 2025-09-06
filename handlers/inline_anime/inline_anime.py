import json
import random
import uuid
from aiogram import Router, F, types, Bot
from tools.cache_tools import get_anime_cache
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import asyncio
from aiogram.enums import ParseMode
from _configs.log_config import logger
from tools.inline_query_tools import clean_description, safe_join, build_anime_caption
from tools.common_utils import delete_message_safe, get_player_url, get_kodik_data_for_site, get_kodik_response
from _configs.config import get_config
from aiogram.exceptions import TelegramBadRequest


cfg = get_config()

ANIME_CACHE_PATH = cfg.cache_config.anime_cache_path
BOT_URL = cfg.bot_config.bot_url
BOT_USERNAME = cfg.bot_config.bot_username
DEV_USERNAME = cfg.dev_config.dev_username
DEV_URL = cfg.dev_config.dev_url
GROUP_ID = cfg.bot_config.group_id
GROUP_URL = cfg.bot_config.group_url


router = Router()


logger.info(f"[inline_anime] - Путь кэша аниме -> {ANIME_CACHE_PATH}")
BASE_URL = "https://ero-no-sekai.up.railway.app/watch/?sid="


# ====== Inline Query Handler ======
@router.inline_query()
async def inline_anime_handler(inline_query: InlineQuery, bot: Bot):
    user_id = inline_query.from_user.id

    try:
        member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        if member.status not in ("member", "administrator", "creator"):
            raise ValueError("Не в группе")
    except TelegramBadRequest:
        await send_join_group_card(inline_query)
        return
    except Exception as e:
        logger.error(f"[inline_anime_handler] Ошибка при проверке участия в группе: {e}")
        await send_join_group_card(inline_query)
        return

    query_text = inline_query.query.lower()

    anime_cache = get_anime_cache()

    logger.info(f"[inline_anime_handler] - Получен inline_query от пользователя {inline_query.from_user.id}: '{query_text}'"
                f"\nНаличие кэша: {True if anime_cache else False}"
                f"\nТип кэш-переменной: {type(anime_cache)}")

    if not query_text:
        animes_list = random.sample(list(anime_cache.values()), k=min(20, len(anime_cache)))
    else:
        logger.violet(f"[inline_anime_handler] - Содержимое anime_cache: {json.dumps(anime_cache, indent=4, ensure_ascii=False)}")

        animes_list = []

        for index, anime in enumerate(anime_cache.values()):
            if not isinstance(anime, dict):
                logger.error(f"[inline_anime_handler] - Элемент под индексом {index} не является словарём: {repr(anime)}")
                continue

            russian_value = anime.get('russian')
            name_value = anime.get('name')

            if russian_value is None:
                logger.warning(f"[inline_anime_handler] - anime[{index}] c id: {anime['id']} → ключ 'russian' отсутствует или None")
            if name_value is None:
                logger.warning(f"[inline_anime_handler] - anime[{index}] c id: {anime['id']} → ключ 'name' отсутствует или None")

            russian_text = russian_value or ''
            name_text = name_value or ''

            try:
                if query_text in russian_text.lower() or query_text in name_text.lower():
                    logger.info(f"[inline_anime_handler] - anime[{index}] → добавлен по совпадению с запросом")
                    animes_list.append(anime)
            except Exception as e:
                logger.error(f"[inline_anime_handler] - anime[{index}] → ошибка при сравнении: {e}")
                logger.debug(f"[inline_anime_handler] - anime[{index}] → russian: {repr(russian_value)}, name: {repr(name_value)}")


    logger.info(f"[inline_anime_handler] - Выбрано {len(animes_list)} аниме для ответа.")

    results = []

    for anime in animes_list:

        if not isinstance(anime, dict):
            logger.error(f"[inline_anime_handler] - Ошибка: anime не является словарём: {repr(anime)}")
            continue  # Пропустить этот элемент

        unique_id = str(uuid.uuid4())
        anime_id = str(anime.get("id"))

        logger.debug(json.dumps(anime, indent=4, ensure_ascii=False))

        genres = anime.get("genres", [])
        studios = anime.get("studios", [])
        description = clean_description(anime.get("description", ""))[:300]
        poster_preview_url = anime.get('mainUrl')

        if inline_query.chat_type == "private":
            # Обработка личных чатов

            message_text = (
                f"🎬 <b>{anime.get('name', 'Без названия')}</b> (<i>{anime.get('russian', '...')}</i>)\n"
                f"⭐️ <b>Оценка:</b> {anime.get('score', '?')}/10\n"
                f"🔖 <b>Жанры:</b> {safe_join(genres)}\n"
                f"🏢 <b>Студия:</b> {safe_join(studios)}\n"
                f"📺 <b>Эпизоды:</b> {anime.get('episodes', '?')}\n\n"
                f"📝 <b>Описание:</b>\n{description}\n\n"
                f"🔗 <a href='{anime.get('url', '')}'>Страница на Shikimori</a>\n"
                f"🔗 <a href='{anime.get('url', '')}/characters'>Персонажи</a>"
            )



            result = get_kodik_response(anime.get('id'))
            markup = None

            if result.status_code == 200:
                result = result.json()
                try:

                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="▶ Смотреть", url=BASE_URL+anime_id)
                        ]
                    ])

                except Exception as e:
                    logger.error(f"[inline_anime_handler] - Ошибка при запросе player_url {e} \nplayer_url={json.dumps(result, indent=4, ensure_ascii=False)}")

            input_message_content = InputTextMessageContent(
                message_text=message_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False
            )

            results.append(
                InlineQueryResultArticle(
                    id=unique_id,
                    title=anime.get('russian') or anime.get('name') or "Без названия",
                    description=clean_description(anime.get("description", ""))[:100] + "...",
                    input_message_content=input_message_content,
                    reply_markup=markup,
                    thumb_url=poster_preview_url,
                    thumb_width=128,
                    thumb_height=200
                )
            )

        else:
            # Обработка запросов внутри групп в которых есть бот
            input_message_content = InputTextMessageContent(
                message_text=anime_id,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            results.append(
                InlineQueryResultArticle(
                    id=unique_id,
                    title=anime.get('russian') or anime.get('name') or "Без названия",
                    description=(clean_description(anime.get("description", ""))[:100] + "..."),
                    input_message_content=input_message_content,
                    thumb_url=poster_preview_url,
                    thumb_width=128,
                    thumb_height=200
                )
            )

    if not results:
        logger.warning(f"[inline_anime_handler] - Не найдено аниме по запросу '{query_text}'")

        unique_id = str(uuid.uuid4())

        input_message_content = InputTextMessageContent(
            message_text=(
                f"К сожалению, что-то пошло не так, и я не смог распознать запрос.\n"
                f"Обратись к {DEV_USERNAME}, возможно, он объяснит причину.\n"
                f"А ещё быстрее — <a href='{BOT_URL}'>обратиться к боту</a> с командой <code>/ssa (название)</code>."
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

        results.append(
            InlineQueryResultArticle(
                id=unique_id,
                title="К сожалению, что-то пошло не так",
                description="Не расстраивайся! Ты всегда можешь получить карусель в чате с ботом, используя команду '/ssa (название)'",
                input_message_content=input_message_content,
                thumb_url='https://ero-no-sekai.up.railway.app/static/pictures/404_preview.jpg',
                thumb_width=128,
                thumb_height=200
            )
        )

    try:
        await inline_query.answer(results=results, cache_time=0)
        logger.info("[inline_anime_handler] - Ответ на inline_query успешно отправлен.")
    except Exception as e:
        logger.exception(f"[inline_anime_handler] - Ошибка при отправке ответа на inline_query: {e}")



# --- Message Handler for Anime ID ---
@router.message(F.text.regexp(r"^\d+$"))
async def anime_selected_handler(message: types.Message, bot: Bot) -> None:
    anime_id = message.text.strip()

    anime_cache = get_anime_cache()

    anime = anime_cache.get(anime_id)

    if not anime:
        await message.reply("😕 Аниме не найдено.")
        return

    caption, markup = build_anime_caption(anime)
    poster_url = anime["poster"]

    try:
        if poster_url:
            if markup:
                reply = await message.reply_photo(
                    photo=poster_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup
                )
                logger.info(f"[anime_selected_handler] - Отправлено фото с описанием аниме ID={anime_id} и клавиатурой")
            else:
                reply = await message.reply_photo(
                    photo=poster_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"[anime_selected_handler] - Отправлено фото с описанием аниме ID={anime_id}")

        else:
            if markup:
                reply = await message.reply(
                    caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup
                )
            else:
                reply = await message.reply(
                    caption,
                    parse_mode=ParseMode.HTML
                )
            logger.info(f"Отправлено текстовое описание аниме ID={anime_id}")

        _ = asyncio.create_task(delete_message_safe(message, delay=1))

    except Exception as e:
        logger.exception(f"[anime_selected_handler] -  Ошибка при отправке сообщения о выбранном аниме ID={anime_id}: {e}")


async def send_join_group_card(inline_query: InlineQuery):
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Прости, но, доступ ограничен",
            description="Функция доступна исключительно участникам нашей группы.",
            input_message_content=InputTextMessageContent(
                message_text="🔒 Для использования этого функционала, вступи в нашу группу:",
                parse_mode="HTML"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔗 Вступить в группу", url=GROUP_URL)]
                ]
            ),
            thumb_url="https://ero-no-sekai.up.railway.app/static/pictures/_access_block.jpg",
            thumb_width=128,
            thumb_height=128
        )
    ]

    await inline_query.answer(results=results, cache_time=0, is_personal=True)
