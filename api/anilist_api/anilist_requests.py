import requests
import random
import re
from _configs.log_config import logger



def send_random_anime(max_attempts=3):
    query = """
    query GetRandomAnime($id: Int) {
        Media(id: $id) {
            id
            title {
                romaji
                english
                native
            }
            genres
            description(asHtml: false)
            averageScore
            episodes
            coverImage {
                large
            }
        }
    }
    """
    url = 'https://graphql.anilist.co'

    for attempt in range(max_attempts):
        variables = {'id': random.randint(1, 250000)}
        response = requests.post(url, json={'query': query, 'variables': variables})

        if response.status_code != 200:
            continue

        data = response.json()
        if "errors" in data:
            continue

        media = data.get("data", {}).get("Media")
        if not media:
            continue

        title_data = media.get("title", {})
        title = (
                title_data.get("romaji")
                or title_data.get("english")
                or title_data.get("native")
                or "Без названия"
        )

        description = media.get("description")
        if description:
            description = description.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            description = re.sub(r'<[^>]+>', '', description)
            description = description[:500] + ("..." if len(description) > 500 else "")
        else:
            description = "Нет описания."

        score = media.get("averageScore", "?")
        genres = ", ".join(media.get("genres", [])) or "Жанры не указаны"

        cover_image = media.get("coverImage", {}).get("large", "")

        return {
            "photo_url": cover_image,
            "title": title,
            "description": description,
            "genres": genres,
            "score": score
        }

    return {"text": "❌ Не удалось найти случайное аниме после нескольких попыток."}


def send_anime_by_name(title_name, max_attempts=3):
    query = """
    query GetAnimeByTitle($search: String) {
        Page(page: 1, perPage: 1) {
            media(search: $search, type: ANIME) {
                id
                title {
                    romaji
                    english
                    native
                }
                genres
                description(asHtml: false)
                averageScore
                episodes
                coverImage {
                    large
                }
            }
        }
    }
    """
    url = 'https://graphql.anilist.co'
    variables = {'search': title_name}

    for attempt in range(max_attempts):
        response = requests.post(url, json={'query': query, 'variables': variables})

        if response.status_code != 200:
            continue

        data = response.json()
        if "errors" in data:
            continue

        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            return {"text": "❌ Аниме не найдено."}

        media = media_list[0]

        title_data = media.get("title", {})
        title = (
            title_data.get("romaji")
            or title_data.get("english")
            or title_data.get("native")
            or "Без названия"
        )

        description = media.get("description", "")
        if description:
            description = re.sub(r'<br\s*/?>', ' ', description)
            description = re.sub(r'<[^>]+>', '', description)
            description = (description[:500] + "...") if len(description) > 500 else description
        else:
            description = "Нет описания."

        return {
            "photo_url": media.get("coverImage", {}).get("large", ""),
            "title": title,
            "description": description,
            "genres": ", ".join(media.get("genres", [])) or "Жанры не указаны",
            "score": media.get("averageScore", "?")
        }

    return {"text": "❌ Не удалось получить данные после нескольких попыток."}


logger.info("[AnilistApi] - Зарегистрирован успешно")