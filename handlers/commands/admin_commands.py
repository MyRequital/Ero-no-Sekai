from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from aiogram.types import ChatPermissions, ChatMemberRestricted

from tools.common_utils import delete_message_safe
import asyncio
import datetime
from _configs.log_config import logger
from tools.common_utils import require_access
import re
from _configs.config import get_config
from tools.member_tools import send_dev_log

router = Router()

cfg = get_config()

LIMIT_WARNINGS = cfg.bot_config.limit_warnings

@router.message(Command("set_access"))
@require_access(9)
async def set_access(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для обновления\установки уровня доступа пользователю. По-умолчанию, при вступлении в группу
    всем пользователям устанавливается access_lvl=2.
    Некоторые команды - требуют более высокого уроня.

    Формат: /set_access @user 5

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """

    args = command.args

    if not args:
        await message.reply("❗ Формат: /set_access @user 5")
        return

    parts = args.split()
    if len(parts) != 2:
        await message.reply("⚠️ Неверный формат. Пример: /set_access @user 5")
        return

    username = parts[0].lstrip("@")
    access_lvl_str = parts[1]

    if not access_lvl_str.isdigit():
        await message.reply("⚠️ Уровень доступа должен быть числом.")
        return

    access_lvl = int(access_lvl_str)
    target_user_id = await users_data.get_user_id(username)

    if not target_user_id:
        await message.reply(f"🙅 Пользователь @{username} не найден.")
        return

    if target_user_id == message.from_user.id:
        await message.reply("🤨 Нельзя менять уровень доступа самому себе.")
        return

    await users_data.set_access_lvl(target_user_id, access_lvl)
    await message.reply(f"✅ Уровень доступа пользователя @{username} изменён на {access_lvl}.")


@router.message(or_f(Command("set_chat_nickname"), Command("scn")))
@require_access(8)
async def set_chat_nickname(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для установки чат-ника, который виден в чат-профиле пользователя (/me, /whois @user)
    Формат: /scn @user НовыйНик

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    args = command.args

    if not args:
        await message.reply("❗ Формат команды: /scn @user НовыйНик")
        return

    parts = args.split(maxsplit=1)
    if len(parts) != 2:
        await message.reply("⚠️ Неверный формат. Пример: /scn @user НовыйНик")
        return

    username = parts[0].lstrip("@")
    new_nickname = parts[1].strip()

    target_user_id = await users_data.get_user_id(username)

    if not target_user_id:
        await message.reply(f"🙅 Пользователь @{username} не найден.")
        return

    if not new_nickname:
        await message.reply("⚠️ Никнейм не может быть пустым.")
        return

    await users_data.set_display_name_mod(target_user_id, new_nickname)
    await message.reply(f"✅ Пользователю @{username} установлен никнейм: <b>{new_nickname}</b>")


@router.message(Command("rw"))
@require_access(7)
async def reset_warnings(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для снятия ограничений с пользователя. Включая бан, мут, предупреждения.
    Формат команды: /rw @username

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        if not command.args:
            reply = await message.reply('❌ Формат команды: /rw @username')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        username = command.args.strip().lstrip('@')
        user_id = await users_data.get_user_id(username)

        if not user_id:
            reply = await message.reply('❌ Пользователь не найден')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        try:
            member = await message.bot.get_chat_member(message.chat.id, user_id)

            if member.status == 'restricted' and isinstance(member, ChatMemberRestricted):
                permissions = ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=False
                )
                await message.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=user_id,
                    permissions=permissions
                )

        except Exception as e:
            logger.error(f"[ResetWarnings] Ошибка при снятии ограничений: user_id={user_id}, username=@{username}, error={e}")
            reply = await message.reply(
                f'❌ <b>Ошибка при снятии ограничений</b> у @{username}.\n'
                f'<i>Предупреждения не сброшены.</i>'
            )
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        await users_data.set_warnings(user_id, 0)

        reply = await message.reply(
            f'✅ <b>@{username}</b> — <b>предупреждения обнулены</b> и <b>ограничения сняты</b>.\n'
            f'<i>Теперь пользователь может снова отправлять сообщения.</i>'
        )
        _ = asyncio.create_task(delete_message_safe(reply, 60))

    except Exception as e:
        logger.error(f"[ResetWarnings] Общая ошибка в /rw: {e}")
        reply = await message.reply('❌ Ошибка при сбросе предупреждений.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(Command("w"))
@require_access(7)
async def add_warning(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для добавления предупреждений пользователю.
    Формат: /w @username [количество=1]
    По-умолчанию, количество добавляемых пунктов предупреждения, установлено на 1.

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        args = command.args.split() if command.args else []
        if not args:
            reply = await message.reply('❌ Формат: /w @username [количество=1]')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        username = args[0].lstrip('@')
        try:
            points = int(args[1]) if len(args) > 1 else 1
            if points <= 0:
                raise ValueError
        except ValueError:
            reply = await message.reply('❌ Количество должно быть целым числом > 0')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        user_id = await users_data.get_user_id(username)
        if not user_id:
            reply = await message.reply('❌ Пользователь не найден')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        user_id = int(user_id)
        total_warnings, should_ban = await users_data.add_warning_to_user(user_id, points)

        if should_ban:
            until_date = datetime.datetime.now() + datetime.timedelta(days=3)
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            reply = await message.reply(
                f'⛔ <b>@{username}</b> получил(-а) <b>бан на 3 дня</b>!\n'
                f'(Предупреждения: <b>{total_warnings}/{LIMIT_WARNINGS}</b>)'
            )
        else:
            reply = await message.reply(
                f'⚠️ <b>@{username}</b> получил(-а) <b>{points}</b> предупреждение(ий).\n'
                f'Всего предупреждений: <b>{total_warnings}/{LIMIT_WARNINGS}</b>'
            )

        _ = asyncio.create_task(delete_message_safe(reply, 60))

    except Exception as e:
        logger.error(f"[AddWarning] ⚠️ Ошибка команде /w: {e}")
        reply = await message.reply('❌ Ошибка при добавлении предупреждения')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(or_f(Command("admin_menu"), Command("am")))
@require_access(7)
async def send_admin_menu(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда отсылающая 'админ меню'.
    Админ меню - перечень команд, для быстрого копирования оных.

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        admin_menu_text = (
            "<b>📋 Меню модерации</b>\n\n"

            "🛑 <code>/ban @username [время_в_минутах]</code>\n"
            "└─ Забанить пользователя на указанное время\n"

            "🟢 <code>/unban @username</code>\n"
            "└─ Разбан пользователя\n"

            "🔄 <code>/rw @username</code>\n"
            "└─ Сбросить все ограничения (включая мут)\n"

            "⚠️ <code>/w @username [кол-во=1]</code>\n"
            "└─ Выдать предупреждение (по умолчанию 1)\n\n"

            "💬 <code>/set_chat_nickname @username [ник]</code>\n"
            "💬 <code>/scn @username [ник]</code>\n"
            "└─ Установить чат-ник пользователю\n"

            "📝 <code>/set_admin_note @username [заметка]</code>\n"
            "📝 <code>/san @username [заметка]</code>\n"
            "└─ Добавить или изменить модераторскую заметку\n"

            "🔐 <code>/set_access [1-9]</code>\n"
            "└─ Изменить уровень доступа пользователя\n"
            
            "⚙ <code>/config_list</code>\n"
            "⚙ <code>/cfgl</code>\n"
            "└─ Список конфигов. Только личный чат с ботом\n"
            
            "⚙ <code>/set_config [путь] [значение]</code>\n"
            "❗  <code> Параметр путь копируется при нажатии на параметр в /config_list ( = значение) стереть\n"
            "└─ Установка конфигов\n"

            f"<i>⚖️ При {LIMIT_WARNINGS}+ предупреждениях — автоматический бан на 3 дня</i>"
        )

        reply = await message.reply(admin_menu_text, parse_mode="HTML")
        _ = asyncio.create_task(delete_message_safe(reply, 300))

    except Exception as e:
        logger.error(f"[SendAdminMenu] - {e}")
        reply = await message.reply('❌ Ошибка при отображении меню')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(or_f(Command("profile_menu"), Command("pm")))
@require_access(7)
async def send_profile_menu(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда отсылающая 'меню работы с профилем'.
    Профиль меню - перечень команд, для быстрого копирования оных.

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        admin_menu_text = (
            "<b>📋 Меню работы с профилем пользователя</b>\n\n"

            "🛑 /me\n"
            "└─ Собственный профиль\n\n"

            "🟢 <code>/whois @username</code>\n"
            "└─ Профиль указанного пользователя\n\n"

            "💬 <code>/set_chat_nickname @username [ник]</code>\n"
            "💬 <code>/scn @username [ник]</code>\n"
            "└─ Установить чат-ник пользователю (8+)\n\n"

            "📝 <code>/set_admin_note @username [заметка]</code>\n"
            "📝 <code>/san @username [заметка]</code>\n"
            "└─ Добавить или изменить модераторскую заметку (8+ лвл)\n\n"

            "⚠️ <code>/spi - /set_profile_icon</code>\n"
            "└─ Установка аватарки чат-профиля (7+)\n"
            "└─ ❗ Для установки оного, смело обращайтесь к модерации или администрации\n\n"
            
            f"🛠 Актуальный список администрации и модерации можно увидеть по команде /staff"
        )

        reply = await message.reply(admin_menu_text, parse_mode="HTML")
        _ = asyncio.create_task(delete_message_safe(reply, 300))

    except Exception as e:
        logger.error(f"[SendAdminMenu] - {e}")
        reply = await message.reply('❌ Ошибка при отображении меню')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(F.text.regexp(r'игорь\s+разбань\s+@(\w+)', flags=re.IGNORECASE))
@require_access(8)
async def unban_user_custom(message: types.Message, users_data, **kwargs):
    """
    Текстовая команда для разблокировки пользователя.
    Формат: Игорь разбань @username

    :param message:
    :param users_data:
    :param kwargs:
    :return:
    """

    _ = asyncio.create_task(delete_message_safe(message, 60))
    match = re.search(r'игорь\s+разбань\s+@(\w+)', message.text, re.IGNORECASE)
    if not match:
        return

    username = match.group(1)
    user_id = await users_data.get_user_id(username)
    if not user_id:
        reply = await message.reply('❌ Не удалось найти пользователя.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))
        return

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=False,
            can_send_other_messages=True,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_to_group=False,
            can_pin_messages=False
        )
        await message.bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        reply = await message.reply(f'✅ Пользователь @{username} успешно разбанен.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))
    except Exception as e:
        logger.error(f"[UnbanUserCustom] - ❌ Ошибка при разбане: {e}")
        reply = await message.reply('❌ Ошибка при разбане.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(Command("unban"))
@require_access(8)
async def unban_user_command(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для разблокировки пользователя.
    Формат: /unban @username

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        if not command.args:
            reply = await message.reply('❌ Формат: /unban @username')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        username = command.args.strip().lstrip('@')
        user_id = await users_data.get_user_id(username)
        if not user_id:
            reply = await message.reply('❌ Пользователь не найден')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=permissions
        )
        await users_data.set_warnings(user_id, 0)
        reply = await message.reply(f'✅ @{username} разбанен и права восстановлены')
        _ = asyncio.create_task(delete_message_safe(reply, 300))

    except Exception as e:
        logger.error(f"[UnbanUserCommand] - ❌ Ошибка разбана: {e}")
        reply = await message.reply('❌ Ошибка при разбане')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(F.text.regexp(r'игорь\s+забань\s+@(\w+)\s+на\s+(\d+)\s+минут', flags=re.IGNORECASE))
@require_access(8)
async def ban_user_custom(message: types.Message, users_data, **kwargs):
    """
    Текстовая команда для блокировки пользователя на (минут).
    Формат команды: Игорь забань @user на X:int минут

    :param message:
    :param users_data:
    :param kwargs:
    :return:
    """
    _ = asyncio.create_task(delete_message_safe(message, 60))
    match = re.search(r'игорь\s+забань\s+@(\w+)\s+на\s+(\d+)\s+минут', message.text, re.IGNORECASE)
    if not match:
        return

    username = match.group(1)
    ban_time = int(match.group(2))
    user_id = await users_data.get_user_id(username)
    if not user_id:
        reply = await message.reply('❌ Не удалось найти пользователя.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))
        return

    until_date = datetime.datetime.now() + datetime.timedelta(minutes=ban_time)
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        reply = await message.reply(f'✅ Пользователь @{username} забанен на {ban_time} минут.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))
    except Exception as e:
        logger.error(f"[BanUserCustom] - ❌ Ошибка при бане: {e}")
        reply = await message.reply('❌ Ошибка при бане.')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(Command("ban"))
@require_access(8)
async def ban_user_command(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    """
    Команда для бана пользователя на указанное кол-во минут.
    Формат: /ban @username время_в_минутах

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """

    _ = asyncio.create_task(delete_message_safe(message, 60))

    try:
        args = command.args.split() if command.args else []
        if len(args) < 2:
            reply = await message.reply('❌ Формат: /ban @username время_в_минутах')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        username = args[0].lstrip('@')
        try:
            ban_time = int(args[1])
            if ban_time <= 0:
                raise ValueError
        except ValueError:
            reply = await message.reply('❌ Время должно быть числом > 0 (минуты)')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        user_id = await users_data.get_user_id(username)
        if not user_id:
            reply = await message.reply('❌ Пользователь не найден')
            _ = asyncio.create_task(delete_message_safe(reply, 60))
            return

        until_date = datetime.datetime.now() + datetime.timedelta(minutes=ban_time)
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        await users_data.set_warnings(user_id, 3)
        reply = await message.reply(f'✅ @{username} забанен на {ban_time} минут')
        _ = asyncio.create_task(delete_message_safe(reply, 300))

    except Exception as e:
        logger.error(f"[BanUserCommand] - ❌ Ошибка при бане: {e}")
        reply = await message.reply('❌ Ошибка при бане')
        _ = asyncio.create_task(delete_message_safe(reply, 60))


@router.message(or_f(Command("set_admin_note"), Command("san")))
@require_access(8)
async def set_admin_note(message: types.Message, command: Command, users_data, **kwargs):
    """
    Установка 'записи админа', участнику группы

    :param message:
    :param command:
    :param users_data:
    :param kwargs:
    :return:
    """
    args = message.text.split(maxsplit=2)

    if len(args) < 3 or not args[1].startswith("@"):
        await message.reply("❌ Используй формат: /san @username Заметка")
        return

    username = args[1][1:]
    note = args[2].strip()

    user_id = await users_data.get_user_id(username)
    if user_id is None:
        await message.reply("❌ Пользователь не найден.")
        return

    await users_data.set_admin_note(user_id, note)
    await message.reply(f"✅ Заметка обновлена для @{username}")


# ====== UNUSED ======


@router.message(or_f(Command("test_ls_log"), Command("tll")))
@require_access(10)
async def test_ls_log_command(message: types.Message, command: Command, **kwargs):
    await send_dev_log(
        message.bot,
        message=f"Новый участник: {message.from_user.first_name}\n"
                f"(@{message.from_user.username})\n"
                f"[ID: {message.from_user.id}] вступил в группу."
    )