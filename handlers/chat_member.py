from aiogram import Router, Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from _configs.config import get_config
from _configs.log_config import logger
from data.welcome_messages import send_welcome_message
from tools.member_tools import send_dev_log

router = Router()

cfg = get_config()

GROUP_ID = cfg.bot_config.group_id

@router.chat_member()
async def handle_chat_member_update(update: ChatMemberUpdated, bot: Bot, users_data):
    logger.info(f"[handle_chat_member_update] - Обработка обновления участника")

    if update.chat.id != GROUP_ID:
        return

    if update.new_chat_member.status not in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED}:
        logger.info(f"[handle_chat_member_update] - Игнорируем статус: {update.new_chat_member.status}")
        return

    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status
    user = update.new_chat_member.user

    user_id = user.id
    username = user.username or None
    first_name = user.first_name or "***"
    last_name = user.last_name or "***"

    await users_data.add_new_user(user_id, username, first_name, last_name)
    anime_name = await users_data.set_anime_name(user_id)


    logger.violet(f"[handle_chat_member_update] - Обработка пользователя:\n"
                  f"Юзернейм - {username}(id:{user_id}), OLD: {old_status}, NEW: {new_status}, Имя - {first_name}")


    if not username and user_id != int(1285675689): # Игнорирование id Даниила
        try:
            await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
        except Exception as e:
            logger.error(f"[handle_chat_member_update] - Ошибка при удалении пользователя без username: {e}")

        try:
            await bot.send_message(
                user_id,
                "Привет, я Shinigami, я страж группы Ero no Sekai: Yami no Yokubo!\n"
                "К сожалению, мне пришлось удалить тебя!\n\n"
                "В нашей группе пользователь обязан иметь @username. "
                "Пожалуйста, установи его в настройках Telegram и попробуй снова."
            )
        except Exception as e:
            logger.warning(
                f"[handle_chat_member_update] - Не удалось отправить сообщение пользователю без username: {e}")

        await send_dev_log(
            bot,
            message=f"Участник: {first_name} {last_name} (@{username}) [ID: {user_id}] был удален из группы за отсутствие @username."
        )

        logger.info(f"[handle_chat_member_update] - Успешное удаление пользователя без username")

        return

    # Вступление
    if old_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED} and new_status in {
        ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED
    }:

        if not username and user_id != 1285675689:
            try:
                await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            except Exception as e:
                logger.error(f"[handle_chat_member_update] - Ошибка при удалении нового участника без username: {e}")

        send_message = send_welcome_message(user, anime_name)

        await bot.send_message(
            GROUP_ID,
            send_message,
            message_thread_id=2
        )

        await send_dev_log(
            bot,
            message=f"Новый участник: {first_name} {last_name} (@{username}) [ID: {user_id}] вступил в группу."
        )

        logger.info(f"[handle_chat_member_update] - Успешная регистрация нового участника")

    # Выход
    elif old_status in {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED} and new_status in {
        ChatMemberStatus.LEFT, ChatMemberStatus.KICKED
    }:
        await send_dev_log(
            bot,
            message=f"Участник: {first_name} {last_name} (@{username}) [ID: {user_id}] покинул группу."
        )

        logger.info(f"[handle_chat_member_update] - Участник покинул/удалён из группы")

    else:
        logger.info(f"[handle_chat_member_update] - Игнорируемое изменение статуса: {old_status} → {new_status}")




logger.info("[ChatMember] - Зарегистрирован успешно")