from aiogram.fsm.state import State, StatesGroup

class GameState(StatesGroup):
    in_game = State()  # Состояние, когда игрок участвует в игре