from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, or_f
from _configs.config import get_config
from _configs.config_io import save_config_to_file
from _configs.config_utils import list_model_paths, set_config_value
from tools.common_utils import require_access


router = Router()


@router.message(or_f(Command("config_list"), Command("cfgl")))
@require_access(9)
async def cmd_config_list(message: Message, users_data, command: F.CommandObject):
    if message.chat.type != "private":
        await message.answer(
            "ℹ️ Эта команда предназначена для использования только в личных сообщениях с ботом.\n"
            "🔐 Доступ доступен администраторам с уровнем доступа <b>9 и выше</b>."
        )
        return

    cfg = get_config()
    lines = list_model_paths(cfg)

    if not lines:
        await message.answer("<b>Конфигурация пуста.</b>", parse_mode="HTML")
        return

    wrapped_lines = [f"<code>{line}</code>" for line in lines]
    text = "\n".join(wrapped_lines)

    await message.answer(f"<b>Текущая конфигурация:</b>\n{text}")



@router.message(or_f(Command("set_config"), Command("scfg")))
@require_access(9)
async def cmd_set_config(message: Message, users_data, command: F.CommandObject):
    parts = message.text.strip().split()

    if len(parts) < 3:
        await message.answer("⚠️ Использование: /set_config <путь> <значение>")
        return

    command = parts[0]
    value = parts[-1]
    path = parts[1:-1]

    cfg = get_config()
    try:
        set_config_value(cfg, path, value)
        save_config_to_file(cfg)
        await message.answer(
            f"✅ Установлено: <code>{' '.join(path)}</code> = <code>{value}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: <code>{e}</code>\nParams: path={' '.join(path)}, value={value}",
            parse_mode="HTML"
        )