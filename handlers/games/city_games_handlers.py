from aiogram import Router, types, F
from tools.common_utils import get_last_valid_letter, is_valid_city, get_next_city, delete_message_safe
from aiogram.fsm.context import FSMContext
from states.game_state import GameState
from aiogram.fsm.storage.memory import StorageKey
from aiogram.filters import Command, or_f
import asyncio
from handlers.commands.commands import is_admin
from _configs.log_config import logger


router = Router()
active_city_games = {}


@router.message(GameState.in_game)
async def handle_city(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id
    city = " ".join(message.text.strip().lower().split())
    print(city)

    if "ласт" in message.text.lower() or "last" in message.text.lower():
        game = active_city_games.get(chat_id)
        if game:
            bot_city = game.get("bot_last_city")
            if bot_city:
                await message.answer(f"Последний город, выбранный ботом: {bot_city}")
            else:
                await message.answer("Ещё не было сыграно ни одного города ботом.")
        return

    if city == "/out_game":
        if chat_id in active_city_games and user_id in active_city_games[chat_id]["players"]:
            active_city_games[chat_id]["players"].remove(user_id)

        await state.clear()
        await message.answer("Ты вышел из игры\\.")
        return

    if chat_id not in active_city_games or user_id not in active_city_games[chat_id]["players"]:
        await message.answer("Ты не в игре! Нажми /to_play, чтобы вступить.")
        return

    game = active_city_games[chat_id]

    if game["waiting_for_reply"]:
        await message.answer("Поздно! Ждём ответа на предыдущий город.")
        return

    if not is_valid_city(city):
        await message.answer(f"Город {city} не найден! Попробуй другой.")
        return

    if city in game["used_cities"]:
        await message.answer(f"Город `{city}` уже использовали! Попробуй другой.")
        return

    last_city = game.get("bot_last_city", game["last_city"])
    if last_city:
        last_letter = get_last_valid_letter(last_city)
        if city[0] != last_letter:
            await message.answer(f"А вот и нет – город {city} не подходит! Должен начинаться на {last_letter}. ")
            return

    game["last_city"] = city
    game["used_cities"].add(city)
    game["waiting_for_reply"] = True

    bot_city = get_next_city(get_last_valid_letter(city), game["used_cities"])
    print(bot_city)

    if bot_city:
        game["used_cities"].add(bot_city)
        game["bot_last_city"] = bot_city
        await message.answer(f"{bot_city}! Твой ход, следующий город на {get_last_valid_letter(bot_city)}.")
    else:
        await message.answer("Я не могу найти подходящий город... Вы победили...")

        # Проверяем наличие игроков в игре
        if "players" in game and game["players"]:  # Если есть игроки
            for current_player_id in game["players"]:  # Используем current_player_id для ясности
                try:
                    player_state = FSMContext(
                        storage=state.storage,
                        key=StorageKey(chat_id=chat_id, user_id=current_player_id)
                    )
                    if await player_state.get_state():
                        await player_state.clear()
                except Exception as e:
                    print(f"Ошибка при очистке состояния для игрока {current_player_id}: {e}")

        # Удаляем игру из active_games в любом случае
        if chat_id in active_city_games:
            del active_city_games[chat_id]

    game["waiting_for_reply"] = False


@router.message(Command('play_city'))
async def enter_game(message: types.Message, state: FSMContext):
    """Игрок входит в игру."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id not in active_city_games:
        active_city_games[chat_id] = {
            "players": set(),
            "used_cities": set(),
            "last_city": None,
            "waiting_for_reply": False
        }

    active_city_games[chat_id]["players"].add(user_id)
    await state.set_state(GameState.in_game)
    message = await message.answer("Ты теперь в игре!"
                         "\nЕсли ты не следил за игрой, "
                         "можешь узнать последний город написав ласт или last")

    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))


@router.message(or_f(Command('out_city'), Command('end_city')))
async def out_game(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id in active_city_games and user_id in active_city_games[chat_id]["players"]:
        active_city_games[chat_id]["players"].remove(user_id)
        await state.clear()
        msg = await message.answer("Ты вышел из игры!")
    else:
        msg = await message.answer("Ты еще не в игре!")

    if msg:
        await asyncio.create_task(delete_message_safe(msg, 60))


@router.message(or_f(Command('reset_city_game'), Command('rcg')))
async def reset_game(message: types.Message, command: F.CommandObject, state: FSMContext):
    try:
        if message:
            _ = asyncio.create_task(delete_message_safe(message, 60))

        if not await is_admin(message.chat.id, message.from_user.id, message.bot):
            reply = await message.reply('❌ У тебя недостаточно прав для обнуления.')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        cleared_players = 0
        for chat_id, game in list(active_city_games.items()):
            for player_id in game.get("players", []):
                try:
                    player_state = FSMContext(
                        storage=state.storage,
                        key=StorageKey(
                            bot_id=message.bot.id,
                            chat_id=chat_id,
                            user_id=player_id
                        )
                    )
                    if await player_state.get_state():
                        await player_state.clear()
                        cleared_players += 1
                except Exception as e:
                    print(f"Ошибка очистки состояния для {player_id}: {e}")

        active_city_games.clear()

        report = (
            "✅ Игра полностью сброшена!\n"
        )
        await message.answer(report)

    except Exception as e:
        print(f"Критическая ошибка в reset_game: {e}")
        await message.answer("⚠️ При сбросе игры произошла ошибка")


logger.info("[CitiGames] - Зарегистрирован успешно")