from data.cities import city_list
import dotenv
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
import asyncio
from googletrans import Translator
from datetime import datetime
import requests
import json
from io import BytesIO
from _configs.log_config import logger
from data.bad_words import BAD_WORDS, CHAR_SUBSTITUTIONS, PSEUDO_SPACES
from functools import wraps
from aiogram import types
from database.repositories import get_users_data_repository
from _configs.config import get_config
import re
from itertools import product
from typing import Set, Tuple, Optional


cfg = get_config()


translator = Translator()
dotenv.load_dotenv()

WEATHER_TOKEN = cfg.weather_config.weather_token


def require_access(min_access_lvl):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, command: F.CommandObject, users_data, **kwargs):
            initiator_user_id = message.from_user.id
            initiator_access_lvl = await users_data.get_access_lvl(initiator_user_id)

            if initiator_access_lvl < min_access_lvl:
                await message.reply(f"❗ Для выполнения данной команды нужен {min_access_lvl}-й уровень доступа."
                                    f"\n\n<i>*О повышении уровня доступа, можно узнать у администрации чата.</i>")
                return

            return await func(message, command, users_data, **kwargs)

        return wrapper

    return decorator


def alternate_require_access(min_access_lvl: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, command: F.CommandObject, **kwargs):
            users_data = get_users_data_repository()

            initiator_user_id = message.from_user.id
            initiator_access_lvl = await users_data.get_access_lvl(initiator_user_id)

            if initiator_access_lvl < min_access_lvl:
                await message.reply(
                    f"❗️ Для выполнения данной команды нужен {min_access_lvl}-й уровень доступа."
                    f"\n\n<i>О повышении уровня доступа можно узнать у администрации чата.</i>"
                )
                return

            return await func(message, command, users_data=users_data, **kwargs)

        return wrapper

    return decorator


def get_last_valid_letter(city: str) -> str:
    """Получает последнюю букву города, пропуская Ь, Ы, Ъ."""
    logger.debug(f"[City] - {city}")
    city = city.lower().strip()
    for letter in reversed(city):
        if letter not in "ьъы":
            return letter
    return city[-1]


def is_valid_city(city: str) -> bool:
    print(city, 'в ис валид сити')
    """Проверяет, есть ли город в базе (с учетом регистра и пробелов)"""
    city = " ".join(city.lower().strip().split())
    return any(city == c.lower() for cities in city_list.values() for c in cities)


def get_next_city(last_letter: str, used_cities: set) -> str | None:
    """Выбирает новый город на нужную букву, исключая уже использованные"""
    last_letter = last_letter.lower()
    used_cities = {c.lower() for c in used_cities}

    logger.debug(f"[LastLetter] - {last_letter}")

    possible_cities = [
        city for city in (city_list.get(last_letter, []) or [])
        if city.lower() not in used_cities
    ]

    return possible_cities[0] if possible_cities else None


def get_weather_with_icon(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_TOKEN}&units=metric&lang=ru"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        def format_unix_time(ts):
            return datetime.fromtimestamp(ts).strftime("%H:%M")

        main = data["main"]
        wind = data["wind"]
        sys = data["sys"]
        weather = data["weather"][0]
        clouds = data["clouds"]

        icon_code = weather.get("icon", "")
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@4x.png"
        icon_image = requests.get(icon_url).content

        message = (
            f"🏙 <b>Город:</b> {data.get('name')}\n"
            f"🌤 <b>Погода:</b> {weather.get('description').capitalize()}\n"
            f"🌡 <b>Температура:</b> {main.get('temp')}°C (ощущается как {main.get('feels_like')}°C)\n"
            f"📈 <b>Мин/Макс:</b> {main.get('temp_min')}°C / {main.get('temp_max')}°C\n"
            f"💧 <b>Влажность:</b> {main.get('humidity')}% {'- Ой как влажно, промокла даже я...' if main.get('humidity') == 70 else ''}\n"
            f"🔻 <b>Давление:</b> {main.get('pressure')} гПа\n"
            f"☁️ <b>Облачность:</b> {clouds.get('all')}%\n"
            f"💨 <b>Ветер:</b> {wind.get('speed')} м/с\n"
            f"🌅 <b>Восход:</b> {format_unix_time(sys.get('sunrise'))}\n"
            f"🌇 <b>Закат:</b> {format_unix_time(sys.get('sunset'))}"
        )

        return message, BytesIO(icon_image)

    except requests.exceptions.RequestException as e:
        logger.error(f'[WeatherError] - {e}')
        return None, None


async def delete_message_safe(message: types.Message, delay: int = 0):
    """Безопасное удаление сообщения с задержкой и обработкой ошибок."""
    try:
        if delay > 0:
            await asyncio.sleep(delay)

        await message.delete()
        logger.debug(f"[DeleteMessage] - Сообщение {message.message_id} успешно удалено")
    except TelegramBadRequest as e:
        if "message to delete not found" in str(e):
            logger.warning(f"[DeleteMessage] - Сообщение {message.message_id} уже удалено")
        else:
            logger.error(f"[DeleteMessage] - Ошибка при удалении сообщения {message.message_id}: {e}")
    except Exception as e:
        logger.error(f"[DeleteMessage] - Неизвестная ошибка при удалении сообщения: {e}")


def generate_variants(word: str, substitutions: dict) -> Set[str]:
    variants = [[] for _ in range(len(word))]
    for i, char in enumerate(word):
        variants[i] = substitutions.get(char, [char])
    return {''.join(v) for v in product(*variants)}


def normalize_word(word: str) -> str:
    """Удаляет всё, кроме букв и цифр. Очищает скрытые пробелы и символы."""
    cleaned = re.sub(PSEUDO_SPACES, '', word)
    cleaned = re.sub(r'[^a-zA-Zа-яА-Я0-9]+', '', cleaned)
    return cleaned.lower()


def get_all_variants(words: Set[str], substitutions: dict) -> dict:
    """Возвращает мапу: вариант -> оригинальное плохое слово"""
    variant_map = {}
    for word in words:
        for variant in generate_variants(word, substitutions):
            variant_map[variant] = word
    return variant_map


BAD_WORD_VARIANT_MAP = get_all_variants(BAD_WORDS, CHAR_SUBSTITUTIONS)


def check_bad_words(text: str):
    text = re.sub(PSEUDO_SPACES, ' ', text)
    words = re.findall(r'\b\w+\b', text.lower())

    for original_word in words:
        cleaned = normalize_word(original_word)
        logger.debug(f"[Мат-фильтр] Проверка слова: '{original_word}' → '{cleaned}'")

        if cleaned in BAD_WORD_VARIANT_MAP:
            trigger_word = BAD_WORD_VARIANT_MAP[cleaned]
            return True, original_word, trigger_word
    return False, None, None


async def async_translate(text: str, scr="ru", dest_lang: str = 'en') -> str:
    '''
    Асинхронный перевод текста на нужный язык.

    :param text: Текст для перевода
    :param scr: Начальный язык
    :param dest_lang: Целевой язык (по умолчанию 'en')
    :return: Переведённый текст
    '''

    result = await translator.translate(text, src=scr, dest=dest_lang)

    logger.debug("[Translate]"
                 f"\n{text}"
                 f"\n{result}")

    return result.text

def get_player_url(kodik_link: str) -> str:
    """
    Функция сбора ссылки.
    Производит сбор итоговой url-строки для плеера и возвращает ее для перехода по ней.

    :param kodik_link: iFrame ссылка
    :return: URL-ссылка на сайт с плеером
    """
    return f'https://ero-no-sekai.up.railway.app/watch/?url=https:{kodik_link}'


def get_kodik_response(shikimori_id: Optional[str | int]) -> requests.Response:
    """
    Функция запроса к KodikAPI, которая возвращает Response объект для дальнейших манипуляций.
    *Обратите внимание, url-строка включает в себя KodikAPI Token получаемый из Config(cfg) объекта.

    :param shikimori_id: ID аниме по Shikimori.one
    :return: Response объект
    """
    url = f"https://kodikapi.com/search?token={cfg.web_app_config.kodik_token}&shikimori_id={shikimori_id}"
    response = requests.get(url)

    try:
        data = response.json()
        results = data.get("results", [])
        if response.status_code == 200 and not results:
            logger.warning(
                f"[get_kodik_data] - Вернул 0 элементов по запросу shikimori_id={shikimori_id} "
                f"(url={url})\nПолученный массив: {json.dumps(data, indent=4, ensure_ascii=False)}"
            )
    except Exception as e:
        logger.error(
            f"[get_kodik_data] - Ошибка при парсинге JSON: {e}\nОтвет: {response.text}"
            f"Status Code: {response.status_code}"
        )

    return response


def get_kodik_data_for_site(shikimori_id: Optional[str | int] = None,
                            kinopoisk_id: Optional[str | int] = None
                            ):
    """
    Функция запроса к KodikAPI, которая возвращает Response объект для дальнейших манипуляций.
    *Обратите внимание, url-строка включает в себя KodikAPI Token получаемый из Config(cfg) объекта.

    :param shikimori_id: ID аниме по Shikimori.one
    :param kinopoisk_id: ID фильма\сериала из Кинопоиска
    :return: data
    """
    if shikimori_id:
        url = f"https://kodikapi.com/search?token={cfg.web_app_config.kodik_token}&shikimori_id={shikimori_id}"
    elif kinopoisk_id:
        url = f"https://kodikapi.com/search?token={cfg.web_app_config.kodik_token}&kinopoisk_id={kinopoisk_id}"


    response = requests.get(url)

    try:
        data = response.json()
        results = data.get("results", [])
        if response.status_code == 200 and not results:
            logger.warning(
                f"[get_kodik_data] - Вернул 0 элементов по запросу shikimori_id={shikimori_id} "
                f"(url={url})\nПолученный массив: {json.dumps(data, indent=4, ensure_ascii=False)}"
            )
    except Exception as e:
        logger.error(
            f"[get_kodik_data] - Ошибка при парсинге JSON: {e}\nОтвет: {response.text}"
            f"Status Code: {response.status_code}"
        )
        return None

    return data['results'][0]


logger.info("[Utils] - Зарегистрирован успешно")
