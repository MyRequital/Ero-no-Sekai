from aiogram.fsm.context import FSMContext
from aiogram import Router, types, F
from aiogram.filters import Command, or_f

from api.shikimori_api import shikimori_requests
from _configs.log_config import logger
from data.shikimori_genres import GENRES
from data.shikimori_genres_id_to_name import GENRES_ID_TO_NAME
from tools.common_utils import delete_message_safe, get_player_url, get_kodik_response
import re
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

import uuid
import json
from _configs.config import get_config, BASE_DIR


router = Router()
cfg = get_config()

dev_url = cfg.dev_config.dev_url

BASE_URL = "https://ero-no-sekai.up.railway.app/watch/?sid="


@router.message(or_f(Command("ssa"), Command("shikimori_send_anime")))
async def search_anime_carousel(message: types.Message, command: F.CommandObject, state: FSMContext, users_data, **kwargs):
    try:
        title_name = message.text.split(" ", 1)[1].strip()
    except IndexError:
        await message.reply("🔍 Укажите название аниме после команды, например: /ssa Наруто", parse_mode="Markdown")
        return

    mes = await message.answer(
        f"Создаю подборку аниме по названию «<b>{title_name.capitalize()}</b>»"
        f"\n\nНадеюсь ты найдешь то, что искал :)"
    )

    if mes:
        await delete_message_safe(mes, 5)

    ani_data, is_cache = await shikimori_requests.get_data_anime_by_name(title_name, limit=10)

    if "error" in ani_data:
        await message.reply(f"❌ Ошибка API: {ani_data['error']}"
                            f"\nНе обращай внимания, ошибка не связана с твоим запросом :)"
                            f"\n Обратись к <a href='{dev_url}'>администратору</a>")
        return

    carousel_id = str(uuid.uuid4())
    data = await state.get_data()
    carousels = data.get("carousels", {})

    if not is_cache:
        animes = ani_data.get("data", {}).get("animes", [])
        logger.violet(f"[ssa] - json лог"
                      f"\n{json.dumps(animes, indent=4, ensure_ascii=False)}")
        if not animes:
            await message.reply("😕 Аниме не найдено. Проверьте название.")
            return

        carousels[carousel_id] = {
            "animes": animes,
            "title": title_name,
            "total": len(animes),
            "current_index": 0,
            "owner_id": message.from_user.id
        }
        await state.update_data(carousels=carousels)
        await send_anime_carousel_item(message, state, carousel_id)

    else:
        logger.violet(f"[ssa] - json лог"
                      f"\n{json.dumps(ani_data, indent=4, ensure_ascii=False)}")
        if not ani_data:
            await message.reply("😕 Аниме не найдено. Проверьте название.")
            return

        carousels[carousel_id] = {
            "animes": ani_data,
            "title": title_name,
            "total": len(ani_data),
            "current_index": 0,
            "owner_id": message.from_user.id
        }
        await state.update_data(carousels=carousels)
        await send_anime_cache_carousel_item(message, state, carousel_id)


@router.message(Command("ssag"))
async def search_anime_by_genre_carousel(message: types.Message, state: FSMContext, users_data, **kwargs):
    try:
        args = message.text.split(" ", 2)[1:]
        if not args:
            await message.reply(
                "📌 Укажи жанр и опционально минимальный рейтинг, например:\n<code>/ssag романтика 7</code>",
                parse_mode="HTML")
            return

        genre_name = args[0].lower()
        min_score = int(args[1]) if len(args) > 1 and args[1].isdigit() else 7
        logger.info(f"[GenreCarousel] - Рейтинг {min_score}")

        genre_id = GENRES.get(genre_name)
        if genre_id is None:
            await message.reply("😕 Такой жанр не найден. Попробуй снова.")
            return

        mes = await message.answer(
            f"Создаю подборку аниме по жанру «<b>{GENRES_ID_TO_NAME.get(genre_id).capitalize()}</b>», с рейтингом выше <b>{min_score}</b>."
            f"\n\n<i>*Имейте ввиду, попытка собрать аниме с рейтингом <b>выше 8</b> может занять <b>время</b> — как ваше, так и моё."
            f"А, шанс получить положительный результат крайне мал.</i>"
        )

        if mes:
            await delete_message_safe(mes, 5)

        animes = await shikimori_requests.get_data_anime_by_genre(
            genre_id=genre_id,
            min_score=min_score,
            limit=10,
            tries=3
        )

        if not animes:
            logger.error(f"[GenreCarousel] - Не удалось сгенерировать карусель по жанру {genre_name}(id={genre_id})")
            await message.reply("😢 Не удалось найти аниме по этому жанру.")
            return

        carousel_id = str(uuid.uuid4())
        data = await state.get_data()
        carousels = data.get("carousels", {})

        carousels[carousel_id] = {
            "animes": animes,
            "title": genre_name,
            "total": len(animes),
            "current_index": 0,
            "owner_id": message.from_user.id
        }
        await state.update_data(carousels=carousels)
        await send_anime_carousel_item(message, state, carousel_id)

    except Exception as e:
        logger.error(f"[SSAG Handler Error] - {e}")
        await message.reply("⚠️ Ошибка при выполнении запроса. Попробуй позже.")


@router.message(Command("sstop10"))
async def top10_anime_by_year(message: types.Message, state: FSMContext, users_data, **kwargs):
    try:
        args = message.text.split(" ", 2)[1:]
        year = int(args[0]) if len(args) >= 1 and args[0].isdigit() else 2024
        min_score = int(args[1]) if len(args) >= 2 and args[1].isdigit() else 7

        logger.info(f"[Top10Carousel] - Год: {year}, Мин. рейтинг: {min_score}")

        mes = await message.answer(f"🔍 Ищу топ-10 аниме за {year} с рейтингом выше {min_score}...")
        if mes:
            await delete_message_safe(mes, 10)

        animes = shikimori_requests.get_top_anime_by_year_and_rating(
            year=year,
            min_score=min_score,
            attempts=3
        )

        logger.debug(f"[Top10Carousel] Полученные аниме: {animes}")

        # Проверяем, что получили список аниме
        if not animes or not isinstance(animes, list):
            logger.warning(f"[Top10Carousel] Не удалось получить аниме за {year} с рейтингом >= {min_score}")
            await message.reply("😢 Не удалось найти аниме по этим параметрам.")
            return

        filtered = [anime for anime in animes if anime.get("score", 0) >= min_score]
        logger.debug(f"[Top10Carousel] После фильтрации (по рейтингу {min_score}): {filtered}")

        if not filtered:
            logger.warning(f"[Top10Carousel] Нет аниме с рейтингом >= {min_score}")
            await message.reply("😢 Не удалось найти аниме с нужным рейтингом.")
            return

        anime_list = filtered[:10]

        data = await state.get_data()
        last_msg_id = data.get("anime_carousel_last_message_id")
        if last_msg_id:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
            except Exception:
                pass

        await state.update_data(
            anime_carousel={
                "animes": anime_list,
                "title": f"ТОП 10 ({year}+)",
                "total": len(anime_list),
                "current_index": 0,
                "owner_id": message.from_user.id
            },
            anime_carousel_last_message_id=None
        )

        await send_anime_carousel_item(message, state)

    except Exception as e:
        logger.error(f"[Top10Carousel] - {e}")
        await message.reply("⚠️ Ошибка при выполнении запроса. Попробуй позже.")



async def send_anime_carousel_item(message: types.Message | types.CallbackQuery, state: FSMContext, carousel_id: str):
    data = await state.get_data()
    carousels = data.get("carousels", {})
    anime_carousel = carousels.get(carousel_id, {})

    animes = anime_carousel.get("animes", [])
    title_name = anime_carousel.get("title", "")
    total = anime_carousel.get("total", 0)
    current_index = anime_carousel.get("current_index", 0)

    if not animes or current_index >= len(animes):
        await (message.reply("😕 Ошибка отображения аниме.") if isinstance(message, types.Message)
               else message.answer("😕 Ошибка отображения аниме."))
        return

    anime = animes[current_index]

    poster_url = anime.get("poster").get("mainUrl") if anime.get("poster").get("mainUrl") else anime.get("poster").get("originalUrl")
    logger.info(f"[SEND ITEM] -> poster_url = {poster_url}")


    # Обработка описания
    description = anime.get("description") or "Описание отсутствует."
    description = remove_character_tags(description)
    if len(description) > 300:
        description = description[:300] + "..."

    anime_id = anime.get('id')
    genres = [g.get("russian", "") for g in anime.get("genres", [])]
    studios = [s.get("name", "") for s in anime.get("studios", [])]

    result = get_kodik_response(anime_id)

    player_url = None
    if result.status_code == 200:
        result_json = result.json()
        results = result_json.get('results', [])
        if results:
            player_url = get_player_url(results[0].get('link'))

    # Кнопки
    buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"anime_carousel:{carousel_id}:prev"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="anime_carousel:noop"),
            InlineKeyboardButton(text="➡️", callback_data=f"anime_carousel:{carousel_id}:next")
        ]
    ]
    if player_url:
        buttons.append([InlineKeyboardButton(text="▶️ Смотреть", url=BASE_URL + anime_id)])

    buttons.append([InlineKeyboardButton(text="❌ Удалить", callback_data=f"anime_carousel:{carousel_id}:delete")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    caption = (
        f"🎬 <b>{anime.get('name', 'Без названия')}</b> (<i>{anime.get('russian', '...')}</i>)\n"
        f"⭐️ <b>Оценка:</b> {anime.get('score', '?')}/10\n"
        f"🔖 <b>Жанры:</b> {', '.join(genres) or 'Не указаны'}\n"
        f"🏢 <b>Студия:</b> {', '.join(studios) or 'Неизвестна'}\n"
        f"📺 <b>Эпизоды:</b> {anime.get('episodes', '?')}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"🔗 <a href='{anime.get('url', '')}'>Страница на Shikimori</a>\n"
        f"🔗 <a href='{anime.get('url', '')}/characters'>Персонажи</a>"
    )

    if isinstance(message, types.CallbackQuery):
        try:
            await message.message.edit_media(
                media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
                reply_markup=markup
            )
        except Exception as e:
            await message.answer(f"Ошибка при обновлении сообщения: {str(e)}")
    else:
        await message.reply_photo(
            photo=poster_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup
        )


async def send_anime_cache_carousel_item(message: types.Message | types.CallbackQuery, state: FSMContext, carousel_id: str):
    data = await state.get_data()
    carousels = data.get("carousels", {})
    anime_carousel = carousels.get(carousel_id, {})

    animes = anime_carousel.get("animes", [])
    title_name = anime_carousel.get("title", "")
    total = anime_carousel.get("total", 0)
    current_index = anime_carousel.get("current_index", 0)

    if not animes or current_index >= len(animes):
        await (message.reply("😕 Ошибка отображения аниме.") if isinstance(message, types.Message)
               else message.answer("😕 Ошибка отображения аниме."))
        return

    anime = animes[current_index]


    poster_url = anime.get("poster")
    logger.info(f"[SEND CACHE ITEM] -> poster_url = {poster_url}")

    description = anime.get("description") or "Описание отсутствует."
    description = remove_character_tags(description)
    if len(description) > 300:
        description = description[:300] + "..."

    anime_id = anime.get('id')
    genres = anime.get("genres", [])
    studios = anime.get("studios", [])

    result = get_kodik_response(anime_id)

    player_url = None
    if result.status_code == 200:
        result_json = result.json()
        results = result_json.get('results', [])
        if results:
            player_url = get_player_url(results[0].get('link'))

    buttons = [
        [
            InlineKeyboardButton(text="⬅️", callback_data=f"anime_carousel:{carousel_id}:prev"),
            InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="anime_carousel:noop"),
            InlineKeyboardButton(text="➡️", callback_data=f"anime_carousel:{carousel_id}:next")
        ]
    ]

    if player_url:
        buttons.append([InlineKeyboardButton(text="▶️ Смотреть", url=BASE_URL + anime_id)])

    buttons.append([InlineKeyboardButton(text="❌ Удалить", callback_data=f"anime_carousel:{carousel_id}:delete")])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    caption = (
        f"🎬 <b>{anime.get('name', 'Без названия')}</b> (<i>{anime.get('russian', '...')}</i>)\n"
        f"⭐️ <b>Оценка:</b> {anime.get('score', '?')}/10\n"
        f"🔖 <b>Жанры:</b> {', '.join(genres) or 'Не указаны'}\n"
        f"🏢 <b>Студия:</b> {', '.join(studios) or 'Неизвестна'}\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"🔗 <a href='{anime.get('url', '')}'>Страница на Shikimori</a>\n"
        f"🔗 <a href='{anime.get('url', '')}/characters'>Персонажи</a>"
    )

    if isinstance(message, types.CallbackQuery):
        try:
            await message.message.edit_media(
                media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
                reply_markup=markup
            )
        except Exception as e:
            await message.answer(f"Ошибка при обновлении сообщения: {str(e)}")
    else:
        await message.reply_photo(
            photo=poster_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup
        )


@router.callback_query(F.data.startswith("anime_carousel:"))
async def handle_anime_carousel(callback: types.CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer()
            return

        _, carousel_id, action = parts
        data = await state.get_data()
        carousels = data.get("carousels", {})
        anime_carousel = carousels.get(carousel_id)

        if not anime_carousel:
            await callback.answer("Прости, но карусель устарела. \nВызови новую :) \n*Это могло произойти после перезагрузки сервера", show_alert=True)
            return

        if anime_carousel.get("owner_id") != callback.from_user.id:
            await callback.answer("Эта карусель принадлежит другому пользователю.", show_alert=True)
            return

        if action == "delete":
            try:
                await callback.message.delete()
            except Exception:
                pass
            carousels.pop(carousel_id, None)
            await state.update_data(carousels=carousels)
            return

        current_index = anime_carousel.get("current_index", 0)
        total = anime_carousel.get("total", 0)

        if action == "prev":
            new_index = (current_index - 1) % total
        elif action == "next":
            new_index = (current_index + 1) % total
        else:
            await callback.answer()
            return

        anime_carousel["current_index"] = new_index
        carousels[carousel_id] = anime_carousel
        await state.update_data(carousels=carousels)

        # определяем, кэш это или нет
        is_cache = isinstance(anime_carousel["animes"][0], dict) and isinstance(anime_carousel["animes"][0].get('poster'), str)

        if is_cache:
            await send_anime_cache_carousel_item(callback, state, carousel_id)
        else:
            await send_anime_carousel_item(callback, state, carousel_id)

    except Exception as e:
        logger.error(f"[HandlerAnimeCarousel] - {e}")
        await callback.answer(f"Ошибка: {str(e)}\nНажмите еще раз", show_alert=True)
    finally:
        await callback.answer()



def remove_character_tags(text: str) -> str:
    return re.sub(r'\[character[^\]]*\](.*?)\[/character\]', r'\1', text, flags=re.DOTALL)


