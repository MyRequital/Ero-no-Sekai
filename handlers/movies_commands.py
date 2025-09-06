from api.anilist_api import anilist_requests
from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from tools.common_utils import async_translate
from api.shikimori_api import shikimori_requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from _configs.log_config import logger


router = Router()


@router.message(or_f(Command("asra"), Command("anilist_send_random_anime")))
async def send_random_movie(message: types.Message):
    result = anilist_requests.send_random_anime()

    translated_description = await async_translate(
        result.get('description'),
        scr='en',
        dest_lang='ru'
    )

    caption = (
        f"🎬 <b>{result.get('title')}</b>\n"
        f"⭐ <b>Рейтинг</b>: <b>{result.get('score')}</b>\n"
        f"📌 <b>Жанры</b>: <b>{result.get('genres')}</b>\n"
        f"📝 <b>Описание</b>:<i>\n{translated_description}</i>"
    )

    if "photo_url" in result:
        await message.reply_photo(
            result["photo_url"],
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await message.reply(result["text"])


@router.message(or_f(Command("asa"), Command("anilist_send_anime")))
async def send_anime_with_anilist(message: types.Message, command: F.CommandObject):
    title_name = await async_translate(message.text.split(" ", 1)[1].strip(),
                                       scr='ru',
                                       dest_lang='en'
                                       )

    result = anilist_requests.send_anime_by_name(title_name)

    translated_description = await async_translate(
        result.get('description'),
        scr='en',
        dest_lang='ru'
    )

    caption = (
        f"🎬 <b>{result.get('title')}</b>\n"
        f"⭐ <b>Рейтинг</b>: <b>{result.get('score')}</b>\n"
        f"📌 <b>Жанры</b>: <b>{result.get('genres')}</b>\n"
        f"📝 <b>Описание</b>:<i>\n{translated_description}</i>"
    )

    if "photo_url" in result:
        await message.reply_photo(
            result["photo_url"],
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await message.reply(result["text"])



# @router.message(or_f(Command("ssa"), Command("shikimori_send_anime")))
# async def send_anime_with_shikimori(message: types.Message, command: F.CommandObject):
#     try:
#         title_name = message.text.split(" ", 1)[1].strip()
#     except IndexError:
#         await message.reply("🔍 Укажите название аниме после команды, например: `/ssa Наруто`", parse_mode="Markdown")
#         return
#
#     ani_data = await shikimori_requests.get_data_anime_by_name(title_name)
#
#     if "error" in ani_data:
#         await message.reply(f"❌ Ошибка API: {ani_data['error']}")
#         return
#
#     anime = ani_data.get("data", {}).get("animes", [None])[0]
#     if not anime:
#         await message.reply("😕 Аниме не найдено. Проверьте название.")
#         return
#
#     poster_url = anime.get("poster", {}).get("originalUrl") if anime.get("poster") else None
#
#     # Более надежная обработка описания
#     description = anime.get("description")
#     if not description:
#         description = "Описание отсутствует."
#     elif len(description) > 500:
#         description = description[:500] + "..."
#
#     genres = [g.get("russian", "") for g in anime.get("genres", [])]
#     studios = [s.get("name", "") for s in anime.get("studios", [])]
#
#     caption = (
#         f"🎬 <b>{anime.get('name', 'Без названия')}</b> (<i>{anime.get('russian', '...')}</i>)\n"
#         f"⭐ <b>Оценка:</b> {anime.get('score', '?')}/10\n"
#         f"🔖 <b>Жанры:</b> {', '.join(genres) or 'Не указаны'}\n"
#         f"🏢 <b>Студия:</b> {', '.join(studios) or 'Неизвестна'}\n"
#         f"📺 <b>Эпизоды:</b> {anime.get('episodes', '?')}\n\n"
#         f"📝 <b>Описание:</b>\n{description}\n\n"
#         f"🔗 <a href='{anime.get('url', '')}'>Страница на Shikimori</a>"
#     )
#
#     if poster_url:
#         await message.reply_photo(
#             photo=poster_url,
#             caption=caption,
#             parse_mode="HTML"
#         )
#     else:
#         await message.reply(caption, parse_mode="HTML")


@router.message(or_f(Command("ssrc"), Command("shikimori_send_random_character")))
async def send_random_character_data(message: types.Message):
    char_data = shikimori_requests.send_data_random_person()

    if not char_data:
        await message.reply("Не удалось получить данные о персонаже.")
        return

    poster_url = char_data.get("poster", {}).get("originalUrl") if char_data.get("poster") else None

    description = char_data.get("description")
    if not description:
        description = "Описание отсутствует."
    else:
        description = str(description)
        if len(description) > 500:
            description = description[:500] + "..."

    name = char_data.get('name', 'Без имени')
    russian_name = f" ({char_data['russian']})" if char_data.get('russian') else ""

    caption = (
        f"<b>{name}</b>{russian_name}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"🔗 <a href='{char_data.get('url', '')}'>Страница на Shikimori</a>"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Повторить", callback_data="random_character_repeat")]
    ])

    if poster_url:
        await message.answer_photo(
            photo=poster_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=markup
        )
    else:
        await message.answer(
            text=caption,
            parse_mode="HTML",
            reply_markup=markup
        )


# Обработчик для кнопки "Повторить"
@router.callback_query(F.data == "random_character_repeat")
async def repeat_random_character(callback: types.CallbackQuery):
    try:
        await callback.message.delete()

        char_data = shikimori_requests.send_data_random_person()

        if not char_data:
            await callback.message.answer("Не удалось получить данные о персонаже.")
            return

        poster_url = char_data.get("poster", {}).get("originalUrl") if char_data.get("poster") else None

        description = char_data.get("description")
        if not description:
            description = "Описание отсутствует."
        else:
            description = str(description)
            if len(description) > 500:
                description = description[:500] + "..."

        name = char_data.get('name', 'Без имени')
        russian_name = f" ({char_data['russian']})" if char_data.get('russian') else ""

        caption = (
            f"<b>{name}</b>{russian_name}\n\n"
            f"📝 <b>Описание:</b>\n{description}\n\n"
            f"🔗 <a href='{char_data.get('url', '')}'>Страница на Shikimori</a>"
        )

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторить", callback_data="random_character_repeat")]
        ])

        if poster_url:
            await callback.message.answer_photo(
                photo=poster_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=markup
            )
        else:
            await callback.message.answer(
                text=caption,
                parse_mode="HTML",
                reply_markup=markup
            )

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    finally:
        await callback.answer()


logger.info("[MoviesCommand] - Зарегистрирован успешно")