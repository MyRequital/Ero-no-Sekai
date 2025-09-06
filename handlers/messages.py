import asyncio
import random
import re
from datetime import datetime, timedelta
from random import random

from aiogram import F
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import or_f
from aiogram.types import BufferedInputFile
from aiogram.types import Message, ChatPermissions

from _configs.config import get_config
from _configs.log_config import logger
from tools.common_utils import get_weather_with_icon, delete_message_safe, check_bad_words

router = Router()
cfg = get_config()

TIMER_REMOVAL = cfg.bot_config.timer_removal
GROUP_ID = cfg.bot_config.group_id
BAN_DAYS = cfg.bot_config.ban_days
LIMIT_WARNINGS = cfg.bot_config.limit_warnings



@router.message(F.text.regexp(r"и+\s*горь кто я", flags=re.IGNORECASE))
async def handle_who_am_i(message: Message, users_data):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))
    await users_data.set_anime_name(message.from_user.id)
    funny_name = await users_data.get_anime_name(message.from_user.id)
    if message:
        message_bot = await message.reply(f"Сегодня ты: {funny_name}")
        if message_bot:
            _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))
    else:
        _ = await message.bot.send_message(chat_id=GROUP_ID,
                                           text=("Уважаемые пользователи. "
                                           "\nПожалуйста, не удаляйте ваши запросы ко мне - это приводит к ошибкам."
                                           "\nЯ в любом случае, ловлю ваш запрос - и обработаю его как только это будет возможно."))

@router.message(F.text.lower() == "chatid")
async def send_chat_id(message: Message):
    await message.reply(f"Chat ID этого чата: {message.chat.id}")

@router.message(F.text.regexp(r'.*да\sи+горь\?', flags=re.IGNORECASE))
async def send_igor_yes(message: Message):
    await message.reply("Конечно! Это истина!")

@router.message(F.text.regexp(
    r'^(.*?и+горь|бот)\s+(прости|извини?|сор(ян|ри)|пардон|виноват|прош[уу] прощения?)',
    flags=re.IGNORECASE)
) # с удалением
async def send_srry(message: Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))

    status = random.choices(["ПРИНЯТО ✅", "ОТКЛОНЕНО ❌"], weights=[0.7, 0.3])[0]
    guilt_level = random.randint(0, 50) if "ПРИНЯТО" in status else random.randint(51, 100)
    demon_phrase = random.choice([
        "👿 Демоны снизят ваш рейтинг грешности",
        "☕ Сатана поставил чайник",
        "📜 Легион тьмы записал вас в очередь",
        "❄️ Адские печи остывают в вашу честь"
    ])

    response = (
        f"<b>⚖️ Вердикт системы извинений</b>\n\n"
        f"▫️ Статус: {status}\n"
        f"▫️ Уровень вины: {guilt_level}% "
        f"{'😇 Невинный' if guilt_level < 30 else '😈 Греховный' if guilt_level > 70 else '😐 Нейтральный'}\n"
    )

    if "ПРИНЯТО" in status:
        response += (
            f"\n⭐ {random.choice(['Освобожден от кармы', 'Ангелы аплодируют', 'Грехи обнулены'])}\n"
            f"\n{demon_phrase}\n"
            f"🎉 <i>Можете продолжать!</i>"
        )
    else:
        response += (
            f"\n⚠️ {random.choice(['Слишком милое извинение', 'Недостаточно слез', 'Демоны требуют жертву'])}\n"
            f"🔥 Рекомендация: {random.choice(['Принести мема-жертву', 'Аниме-марафон 24ч', 'Покаяться в /game'])}\n"
            f"\n{demon_phrase} 👹"
        )

    sorry = await message.reply(response, parse_mode="HTML")

    if sorry:
        _ = asyncio.create_task(delete_message_safe(sorry, TIMER_REMOVAL))


@router.message(F.text.regexp(r'.*и+горь\s+поиграем', flags=re.IGNORECASE)) # с удалением
async def send_play(message: Message):
    _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))
    message = await message.reply(
                                    'Во что будем играть?'
                                    '\n/to_play - города'
                                    '\n/to_play(на замену) - города(на замену)'
                                    '\n\n/out_game - быстрый выход'
                                )
    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))

@router.message(or_f(
    F.text.regexp(r'(игорь|бот)\s+(какова|какой)\s+(вероятность|шанс)\s+(того\s+)?что\s+(.+)', flags=re.IGNORECASE),
    F.text.regexp(r'(игорь|бот)\s+шанс\s+(того\s+)?что\s+(.+)', flags=re.IGNORECASE),
    F.text.regexp(r'(игорь|бот)\s+насколько\s+вероятно\s+что\s+(.+)', flags=re.IGNORECASE)
))
async def send_chance(message: Message):
    _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))

    for pattern in [
        r'(?:игорь|бот)\s+(?:какова|какой)\s+(?:вероятность|шанс)\s+(?:того\s+)?что\s+(.+)',
        r'(?:игорь|бот)\s+шанс\s+(?:того\s+)?что\s+(.+)',
        r'(?:игорь|бот)\s+насколько\s+вероятно\s+что\s+(.+)'
    ]:
        match = re.search(pattern, message.text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()
            break
    else:
        return

    replacements = {
        r'\bменя\b': 'тебя',
        r'\bмоего\b': 'твоего',
        r'\bмое\b': 'твое',
        r'\bмой\b': 'твой',
        r'\bмоя\b': 'твоя',
        r'\bмои\b': 'твои',
        r'\bя\b': 'ты'
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    text = text.rstrip('?')

    responses = [
        f'Шанс того, что {text} - {random.randint(0, 100)}%',
        f'Вероятность: {random.randint(0, 100)}%, что {text}',
        f'Мои расчеты показывают {random.randint(0, 100)}% на то, что {text}',
        f'{random.randint(0, 100)} из 100, что {text}'
    ]

    message = await message.reply(random.choice(responses))
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))


@router.message(F.text.regexp(r"^и+горь.*\?$", flags=re.IGNORECASE))
async def true(message: Message):
    await message.reply(f"{random.choice(['Да', 'Нет'])}")


@router.message(F.text.regexp(r'и+горь погода\s+(.+)', flags=re.IGNORECASE))
async def weather_handler(message: Message):
    _ = asyncio.create_task(delete_message_safe(message, 10))
    text = message.text.lower()
    match = re.search(r'и+горь погода\s+(.+)', text)
    city = match.group(1).strip()

    spoils = [
        f"Снимаю трусики с облаков в {city.capitalize()}...\n"
        f"погодка сейчас будет~",

        f"Поглаживаю термометр в {city.capitalize()}...\n"
        f"ммм, почти готово~",

        f"Ищу твой {city.capitalize()} на карте...\n"
        f"пальчиком...\n"
        f"медленно..."

    ]

    spoil = await message.answer(random.choice(spoils), show_alert=True)
    if spoil:
        _ = asyncio.create_task(delete_message_safe(spoil, 3))


    if match:
        weather_text, icon_file = get_weather_with_icon(city)

        if weather_text and icon_file:
            file = BufferedInputFile(icon_file.read(), filename="weather.png")

            reply = await message.answer_photo(
                photo=file,
                caption=weather_text,
                parse_mode="HTML"
            )
            if reply:
                _ = asyncio.create_task(delete_message_safe(reply, TIMER_REMOVAL))
        else:
            error_message = (
                f"⚠️ <b>Ошибка:</b> Не удалось получить данные о погоде для города <i>{city}</i>.\n\n"
                f"<b>Проверьте правильность написания:</b>\n"
                f"• <i>Убедитесь, что название города введено корректно.</i>\n"
                f"• <i>Попробуйте использовать полное название города.</i>\n"
                f"• <i>Если ошибка повторяется, возможно, проблема с доступом к серверу.</i>\n\n"
                f"Если проблема не исчезает, пожалуйста, попробуйте снова через некоторое время."
            )
            reply = await message.answer(error_message, parse_mode="HTML")
            if reply:
                _ = asyncio.create_task(delete_message_safe(reply, TIMER_REMOVAL))


@router.message(F.text)
async def filter_bad_words(message: Message, bot, users_data):
    if not message.text or message.text.startswith('🎬') or message.text.startswith('🔥'):
        return

    user_id = message.from_user.id
    await users_data.increment_message_count(user_id)

    try:
        logger.debug(
            f"Получено сообщение в filter_bad_words: {message.text}"
            f"\nАйди топика: {message.message_thread_id or 'Проблема с айди'}"
            f"\nНазвание топика: "
            f"{getattr(message.reply_to_message.forum_topic_created, 'name', 'Проблема названия топика') if message.reply_to_message and message.reply_to_message.forum_topic_created else 'Проблема названия топика'}"
        )

        # === Проверка/добавление пользователя ===
        user_exists = await users_data.get_user_id(message.from_user.username)

        if user_exists is None:
            await users_data.add_new_user(
                user_id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )

        try:
            await users_data.increment_message_count(user_id)
        except Exception as err:
            logger.warning(f"[FilterBadWords] - Ошибка при подсчете сообщений.\n{err}")

        # === Уровень доступа ===
        access_lvl = await users_data.get_access_lvl(user_id)


        if access_lvl >= 7:
            logger.debug(f"🔓 Пользователь @{message.from_user.username} с доступом {access_lvl} — не наказуем.")
            return

        # === Проверка на плохие слова ===
        result, original_word, trigger_word = check_bad_words(message.text)

        if result:
            logger.info(f"🚨 Обнаружено плохое слово у @{message.from_user.username}: '{original_word}' → '{trigger_word}'")

            total_warnings, should_ban = await users_data.add_warning_to_user(user_id)

            if should_ban:
                until_date = datetime.now() + timedelta(days=BAN_DAYS)
                try:
                    await bot.restrict_chat_member(
                        chat_id=message.chat.id,
                        user_id=user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=until_date
                    )
                    reply = await message.reply(
                        f'⛔ <b>@{message.from_user.username}</b> получил(-а) <b>бан на {BAN_DAYS} дня</b>!\n'
                        f'(Предупреждения: <b>{total_warnings}/{LIMIT_WARNINGS}</b>)'
                        f'\nМат: <code>{original_word}</code> → <b>{trigger_word}</b>'
                    )
                    _ = asyncio.create_task(delete_message_safe(reply, TIMER_REMOVAL))
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.warning(f"[FilterBadWords] - Не удалось ограничить пользователя {user_id}: {e}")
            else:
                reply = await message.reply(
                    f'⚠ <b>@{message.from_user.username}</b> получил(-а) <b>предупреждение</b>.\n'
                    f'Всего предупреждений: <b>{total_warnings}/{LIMIT_WARNINGS}</b>'
                    f'\nМат: <code>{original_word}</code> → <b>{trigger_word}</b>'
                )
                _ = asyncio.create_task(delete_message_safe(reply, TIMER_REMOVAL))

    except Exception as e:
        logger.error(f"[FilterBadWords] - {e}")
        try:
            reply = await message.reply('❌ Ошибка при добавлении предупреждения')
            _ = asyncio.create_task(delete_message_safe(reply, TIMER_REMOVAL))
        except Exception as reply_error:
            logger.error(f"[Error - FilterBadWords] - Ошибка при отправке сообщения об ошибке: {reply_error}")



logger.info('[Messages] - Зарегистрирован успешно')

