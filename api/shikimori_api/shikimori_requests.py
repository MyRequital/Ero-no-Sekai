# Стандартные библиотеки
import asyncio
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

import aiohttp
import requests

from _configs.config import get_config
from _configs.log_config import logger
from data.shikimori_genres_id_to_name import GENRES_ID_TO_NAME
from database.repositories import get_anime_cache_repository
from tools.cache_tools import cache_anime_list_in_background
from tools.common_utils import get_kodik_response


cfg = get_config()

HEADERS = cfg.shikimori_config.headers
REST_URL = cfg.shikimori_config.rest_url
GQL_URL = cfg.shikimori_config.gql_url
MAX_RETRIES_FOR_CHARACTERS = cfg.retry_logic_config.max_retries_for_characters
RETRY_DELAY_FOR_CHARACTERS = cfg.retry_logic_config.retry_delay_for_characters

SITE_URL = cfg.bot_config.site_url

ANIME_CACHE = cfg.cache_config.anime_cache_path
ANIME_CACHE_BY_NAME = cfg.cache_config.anime_cache_by_name_path


# ====== Запрос по названию ======
async def get_data_anime_by_name(title_name: str, limit: int = 10):
    cached_by_name = load_cache(ANIME_CACHE_BY_NAME)
    logger.violet(f"[get_data_anime_by_name] - json лог для {title_name} / {title_name.lower()}"
                  f"\n{json.dumps(cached_by_name, indent=4, ensure_ascii=False)}")

    if title_name.lower() in cached_by_name:
        cached_list = transform_anime_data(cached_by_name[title_name.lower()])
        logger.info(f"[get_data_anime_by_name] - Данные для '{title_name}' найдены в кэше по названию. Выдан кэш.")
        logger.violet(f"[get_data_anime_by_name] - лог кэша по названию {title_name.lower()}"
                      f"\n{json.dumps(cached_by_name[title_name.lower()], indent=4, ensure_ascii=False)}")
        return cached_list, True

    anime_cache_repository = await get_anime_cache_repository()

    variables = {'search': title_name, 'limit': limit}
    query = """
    query GetAnime($search: String, $limit: Int) {
        animes(search: $search, limit: $limit, kind: "!special,!ova,!ona,!music,!pv,!cm,!tv_special") {
            id
            name
            russian
            kind
            rating
            score
            episodes
            episodesAired
            url
            season
            poster {
                originalUrl
                mainUrl
            }
            genres { russian }
            studios { name }
            description
        }
    }
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://shikimori.one/api/graphql',
            json={'query': query, 'variables': variables},
            headers=HEADERS
        ) as response:
            if response.status == 200:
                cache_data = await response.json()

                existing_cache = load_cache(ANIME_CACHE)
                cached_by_name[title_name.lower()] = {}

                anime_entries = []

                for anime in cache_data['data']['animes']:
                    anime_id = anime['id']
                    anime_entry = create_anime_cache_entry(anime)

                    existing_cache[anime_id] = anime_entry
                    cached_by_name[title_name.lower()][anime_id] = anime_entry
                    anime_entries.append((anime_id, anime_entry))

                if anime_cache_repository:
                    cache_anime_list_in_background(anime_entries, anime_cache_repository)

                try:
                    save_cache(cached_by_name, ANIME_CACHE_BY_NAME)
                except Exception as e:
                    logger.warning(f"[get_data_anime_by_name] - Сохранение кэша для каруселей не прошло.\n{e}")
                else:
                    logger.info(f"[get_data_anime_by_name] - Кэш сохранён: {len(cached_by_name)} элементов")

                return cache_data, False

            else:
                text = await response.text(encoding='utf-8')
                logger.error(f"[get_data_anime_by_name] - Ошибка API: {response.status}, \n\n{text}")
                return {"error": f"Error: {response.status}"}, False

# ===================================

# ====== Запрос по жанру ======
async def get_data_anime_by_genre(
        genre_id: int,
        min_score: int = 7,
        limit: int = 10,
        max_page: int = 10,
        tries: int = 2,
        request_rate_limit: float = 0.2,
        max_requests: int = 10
):
    query = """
    query GetAnime($genre: String, $score: Int, $limit: Int, $page: Int) {
      animes(genre: $genre, score: $score, limit: $limit, page: $page, kind: "!special,!ova,!ona,!music,!pv,!cm,!tv_special") {
        id
        name
        russian
        kind
        rating
        episodes
        score
        url
        poster {
          originalUrl
          mainUrl
        }
        genres {
          id
          russian
        }
        studios {
          name
        }
        description
      }
    }
    """
    genre_name = GENRES_ID_TO_NAME.get(genre_id, str(genre_id))
    logger.info(f"[GetDataWithGenre] - Запрос жанра id={genre_id} ({genre_name}), оценка >= {min_score}, лимит={limit}, попыток={tries}")

    collected = []
    seen_ids = set()

    async with aiohttp.ClientSession() as session:
        request_count = 0

        while len(collected) < limit and request_count < max_requests:

            if request_count == 1:
                page = 1
                logger.debug("[GetDataWithGenre] - После 1х попытки фолбэк на первую страницу")
            else:
                page = random.randint(1, max_page)

            variables = {
                "genre": str(genre_id),
                "score": min_score,
                "limit": 50,
                "page": page
            }

            logger.debug(f"[GetDataWithGenre] - Запрос #{request_count + 1} | page={page} | variables={variables}")

            try:
                async with session.post(
                        "https://shikimori.one/api/graphql",
                        json={"query": query, "variables": variables},
                        headers=HEADERS
                ) as response:
                    if response.status != 200:
                        logger.error(f"[GetDataWithGenre] - Ошибка при запросе: {response.status}")
                        request_count += 1
                        continue

                    try:
                        json_data = await response.json()
                        logger.debug(f"API Response: {json_data}")
                    except Exception as e:
                        logger.error(f"[GetDataWithGenre] - Ошибка при парсинге JSON: {e}")
                        request_count += 1
                        continue

                    animes = json_data.get("data", {}).get("animes", [])
                    logger.debug(f"[GetDataWithGenre] - Получено аниме: {len(animes)} шт. на странице {page}")

                    for anime in animes:
                        anime_id = anime.get("id")
                        if not anime_id or anime_id in seen_ids:
                            continue

                        seen_ids.add(anime_id)
                        collected.append(anime)
                        logger.debug(f"[GetDataWithGenre] - Добавлено: {anime.get('russian', anime.get('name'))} | score={anime.get('score')}")

                    request_count += 1
                    await asyncio.sleep(request_rate_limit)

            except Exception as e:
                logger.warning(f"[GetDataWithGenre] - Ошибка при запросе: {e}")
                request_count += 1
                continue

        if len(collected) < limit:
            logger.warning(f"[GetDataWithGenre] - Не удалось набрать {limit} аниме, возвращаем {len(collected)} шт.")

    if collected:
        if len(collected) > limit:
            collected = random.sample(collected, limit)
        else:
            collected = sorted(collected, key=lambda x: float(x.get("score", 0)), reverse=True)

    return collected[:limit] if collected else None

# ===================================

# ====== Работа с персонажами ======
def get_top_anime_by_year_and_rating(year=2024, min_score=7, attempts=3):
    page_ranges = [10, 5]
    limit = 10

    query = """
    query GetAnime($year: Int, $limit: Int, $page: Int) {
        animes(year: $year, limit: $limit, page: $page) {
            id
            name
            russian
            kind
            rating
            score
            episodes
            episodesAired
            url
            season
            airedOn {
                year
                    }
            poster {
                originalUrl
                mainUrl
            }
            genres { 
                russian  
            }
            studios { 
                name 
            }
            description
        }
    }
    """

    for range_limit in page_ranges:
        page = random.randint(1, range_limit)

        variables = {
            'year': year,
            'limit': limit,
            'page': page
        }

        response = requests.post(
            'https://shikimori.one/api/graphql',
            json={
                'query': query,
                'variables': variables
            },
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json().get("data", {}).get("animes", [])
            logger.debug(f"[GetTopAnime] Успешный запрос (page={page}) с параметрами {json.dumps(variables, ensure_ascii=False)}")

            if not data:
                logger.warning(f"[GetTopAnime] Нет аниме на странице {page}")
                continue

            filtered = [anime for anime in data if anime.get("score", 0) >= min_score]
            logger.debug(f"[GetTopAnime] После фильтрации: {len(filtered)} аниме")

            if not filtered:
                logger.warning(f"[GetTopAnime] На странице {page} нет аниме с рейтингом >= {min_score}")
                continue

            sorted_anime = sorted(filtered, key=lambda x: float(x.get("rating", 0)), reverse=True)
            logger.debug(f"[GetTopAnime] После сортировки: {len(sorted_anime)} аниме")

            return sorted_anime[:limit]

        else:
            logger.warning(f"[GetTopAnime] Ошибка запроса (page={page}): {response.status_code}")

    return {"error": "Не удалось получить данные после 3 попыток"}

# ===================================

# ====== Работа с персонажами ======
def send_data_random_person(max_attempts=5):
    for attempt in range(max_attempts):
        character_id = random.randint(1, 99999)

        query = """
        query {
            characters(ids: %d, page: 1, limit: 1) {
                id
                malId
                name
                russian
                japanese
                synonyms
                url
                createdAt
                updatedAt
                isAnime
                isManga
                isRanobe
                
                poster { 
                    id 
                    originalUrl 
                    mainUrl 
                }
                description
                descriptionHtml
                descriptionSource
            }
        }""" % character_id

        try:
            response = requests.post(
                'https://shikimori.one/api/graphql',
                json={'query': query},
                headers=HEADERS,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                characters = data.get('data', {}).get('characters', [])
                if characters and characters[0].get('id'):
                    return characters[0]

            sleep(1)

        except Exception as e:
            logger.warning(f"[RandomPerson] - Попытка {attempt + 1} Провалы: {str(e)}")
            sleep(2)

    return None


def fetch_origin(char_id):
    """
    Запрашивает полную инфу по персонажу через REST и возвращает его источник: anime → manga → ranobe.
    """
    try:
        r = requests.get(REST_URL.format(id=char_id), headers=HEADERS)
        logger.debug(f"[fetch_origin] – GET /characters/{char_id} → код {r.status_code}")

        if r.status_code != 200:
            logger.warning(f"[fetch_origin] – Персонаж {char_id}: статус {r.status_code}, возвращаю None")
            return None

        data = r.json()
        logger.debug(f"[fetch_origin] – Ключи ответа для персонажа {char_id}: {list(data.keys())}")

        sources = [
            ('animes', 'anime'),
            ('mangas', 'manga'),
            ('ranobe', 'ranobe'),
        ]

        for key, origin_type in sources:
            lst = data.get(key, [])
            if lst:
                first = lst[0]
                origin = {
                    'type': origin_type,
                    'id': first.get('id'),
                    'name': first.get('russian') or first.get('name'),
                    'url': f"https://shikimori.one{first.get('url')}",
                }
                logger.debug(
                    f"[fetch_origin] – Источник для «{data.get('name', '???')}» (id={char_id}): "
                    f"{origin_type} → {origin['name']} ({origin['url']})"
                )
                return origin

        logger.debug(f"[fetch_origin] – Для персонажа {data.get('name', '???')} (id={char_id}) источник не найден")
        return None

    except Exception as e:
        logger.exception(f"[fetch_origin] – Ошибка при получении origin для персонажа {char_id}: {e}")
        return None


def send_data_character(character_name, limit=10):
    """
    Делает один GQL-запрос по имени персонажа и добавляет источник (origin) через REST-запрос.
    Обрабатывает всех персонажей без фильтрации, origin подгружается параллельно.
    """
    query = """
    query ($search: String, $limit: Int) {
        characters(search: $search, limit: $limit) {
            id
            malId
            name
            russian
            japanese
            synonyms
            url
            createdAt
            updatedAt
            isAnime
            isManga
            isRanobe
            poster { id originalUrl mainUrl }
            description
            descriptionSource
        }
    }
    """

    variables = {'search': character_name, 'limit': limit}

    try:
        resp = requests.post(GQL_URL, json={'query': query, 'variables': variables}, headers=HEADERS)
        logger.debug(f"[send_data_character] - Статус ответа GQL: {resp.status_code}")

        if resp.status_code != 200:
            logger.warning(f"[send_data_character] - Ошибка GQL-запроса: код {resp.status_code}")
            return {'data': {'characters': []}}

        data = resp.json()
        characters = data.get('data', {}).get('characters', [])

    except Exception as e:
        logger.exception(f"[send_data_character] - Ошибка при запросе персонажей: {e}")
        return {'data': {'characters': []}}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_char = {executor.submit(fetch_origin, ch['id']): ch for ch in characters}
        for future in as_completed(future_to_char):
            ch = future_to_char[future]
            try:
                origin = future.result()
            except Exception as e:
                logger.error(f"[send_data_character] - Ошибка при получении origin: {e}. ch={ch!r}")
                origin = None
            ch['origin'] = origin

            try:
                name = ch.get('name', '???')
                char_id = ch.get('id', '???')
                if origin:
                    logger.debug(
                        f"[send_data_character] - {name} (id={char_id}) → {origin['type']} "
                        f"«{origin['name']}» ({origin['url']})"
                    )
                else:
                    logger.debug(f"[send_data_character] - {name} (id={char_id}) → origin = None")
            except Exception as e:
                logger.error(f"[send_data_character] - Ошибка при логировании origin: {e}. ch={ch!r}")

    return {'data': {'characters': characters}}

# ===================================


# ====== Дополнительно ======
def load_cache(file_path: str) -> dict:
    """Загружает кэш из указанного файла, если он существует и содержит корректный JSON, или создаёт новый файл."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"[load_cache] Невалидный JSON в файле {file_path}, создаётся новый кэш.")
                return {}
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        logger.info(f"[load_cache] Файл {file_path} не существует, создаётся новый кэш.")
        return {}

def save_cache(cache_data: dict, cache_file_path: str) -> None:
    """Сохраняет кэш в файл."""
    with open(cache_file_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=4, ensure_ascii=False)

def create_anime_cache_entry(anime: dict) -> dict:
    """Создает массив-словарь для кэша на основе данных об аниме.
    {
        \n'id': anime['id'],
        \n'name': anime['name'],
        \n'russian': anime.get('russian', 'Нет русской адаптации'),
        \n'score': anime['score'],
        \n'url': anime['url'],
        \n'mainUrl': anime['poster']['mainUrl'],
        \n'rating': anime['rating'],
        \n'episodes': anime['episodes'],
        \n'kind': anime['kind'],
        \n'poster': anime['poster']['originalUrl'],
        \n'genres': [genre['russian'] for genre in anime['genres']],
        \n'studios': [studio['name'] for studio in anime['studios']],
        \n'description': anime.get('description', 'Описание отсутствует')
    }

    """

    poster = anime.get('poster') or {}                                                          # Ссылка постера
    main_url = poster.get('mainUrl') or SITE_URL + "static/pictures/_access_block.jpg"          # Запасная ссылка постера
    original_url = poster.get('originalUrl') or SITE_URL + "static/pictures/_access_block.jpg"  # Оригинал ссылки постера

    capture = {
        'id': anime['id'],
        'name': anime['name'],
        'russian': anime.get('russian', 'Нет русской адаптации'),
        'score': anime['score'],
        'url': anime['url'],
        'mainUrl': main_url,
        'rating': anime['rating'],
        'episodes': anime['episodes'],
        'kind': anime['kind'],
        'poster': original_url,
        'genres': [genre['russian'] for genre in anime['genres']],
        'studios': [studio['name'] for studio in anime['studios']],
        'description': anime.get('description', 'Описание отсутствует')
    }

    anime_id = capture.get('id')
    try:
        kodik_iframe = get_kodik_response(anime_id).json()['results'][0].get('link')

        if kodik_iframe:
            capture['kodik_iframe'] = kodik_iframe

        return capture

    except Exception as e:
        logger.warning(f"[create_anime_cache_entry] - Ошибка -> {e}"
                       f"\nCapture -> {capture}")
        return capture


def transform_anime_data(source_dict):
    result = []
    for _, anime in source_dict.items():

            result.append(anime)

    return result

logger.info("[ShikimoriApi] - Зарегистрирован успешно")