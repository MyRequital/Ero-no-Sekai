import random
from aiogram import Router, types, F
from aiogram.filters import Command, or_f
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, InlineKeyboardMarkup, InlineKeyboardButton, \
    WebAppInfo

from tools.common_utils import delete_message_safe, async_translate
import asyncio
from data import quotes
from data.shikimori_genres import GENRES
from _configs.log_config import logger
from tools.common_utils import require_access
from _configs.config import get_config
from urllib.parse import urlencode


router = Router()

cfg = get_config()

LIMIT_WARNINGS = cfg.bot_config.limit_warnings
TIMER_REMOVAL = cfg.bot_config.timer_removal
ACTUAL_STAFF_NICK_LIST = cfg.bot_config.actual_staff_nick_list
BASE_URL_APP_COMMANDS = "https://ero-no-sekai.up.railway.app/tg_webapp/"

async def is_admin(chat_id: int, user_id: int, bot) -> bool:
    """Проверяет, является ли пользователь администратором"""
    member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))


@router.message(Command('start'))
async def join_confirmation(message: types.Message, users_data):
    user_id = message.from_user.id
    user_info = await users_data.get_user_base_info(user_id)

    if user_info:
        join_confirm_text = (
            f"👋 <b>Добро пожаловать в</b> <i>Ero no Sekai: Yami no Yokubō</i>!\n\n"
            "✅ Ты уже <b>подтвердил вступление</b> в группу.\n\n"
            "📜 <b>Вступив в группу, ты автоматически подтвердил, что тебе есть 18 лет и ты ознакомился с <a href='https://t.me/EroNoSekai_YamiNoYokubo/1641'>правилами</a>:</b>\n"
            "• /help — гайд по командам\n"
            "• /free_rules — правила для бесплатного доступа\n"
            "• /buy_rules — правила для платного доступа\n\n"
            f"🔐 <b>Твой текущий уровень доступа:</b> <code>{user_info['access_lvl']}</code>\n"
            "ℹ️ Подробнее о себе: /me\n\n"
            "💬 Не стесняйся задавать вопросы, будь вежлив и наслаждайся атмосферой!"
        )
    else:
        user_info = await users_data.add_new_user(
            user_id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            access_lvl=2
        )

        join_confirm_text = (
            "👋 <b>Добро пожаловать в</b> <i>Ero no Sekai: Yami no Yokubō</i>!\n\n"
            "✅ Ты успешно <b>подтвердил вступление</b> в группу.\n\n"
            "📜 <b>Вступая в группу, ты автоматически подтверждаешь, что тебе есть 18 лет и обязуешься ознакомиться с <a href='https://t.me/EroNoSekai_YamiNoYokubo/1641'>правилами</a>:</b>\n"
            "• /help — гайд по командам\n"
            "• /free_rules — правила для бесплатного доступа\n"
            "• /buy_rules — правила для платного доступа\n\n"
            f"🔐 <b>Твой текущий уровень доступа:</b> <code>{user_info[4]}</code>\n"
            "ℹ️ Подробнее о себе: /me\n\n"
            "💬 Не стесняйся задавать вопросы, будь вежлив и наслаждайся атмосферой!"
        )

    markup = markup_link_suffix(
        message,
        f"?{urlencode({'name': message.from_user.first_name})}"
    )

    answ = await message.answer(join_confirm_text, reply_markup=markup)

    if answ:
        _ = asyncio.create_task(delete_message_safe(answ, TIMER_REMOVAL))


@router.message(or_f(Command('help'), Command('h')))
async def send_help(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    help_text = (
        f"<b>🌿 {message.from_user.first_name or message.from_user.username}, вот что я умею:</b>\n\n"

        f"<b>🌳 Основные команды</b>\n"
        f"├─> /start\n"
        f"│  └─> <i>Подтверждение вступления в группу</i>\n"
        f"├─> /anime_quires - /aq\n"
        f"│  └─> <i>Все типы аниме-запросов с примерами</i>\n"
        f"├─> /text_quires - /tq\n"
        f"│  └─> <i>Как работать с текстовыми запросами</i>\n"
        f"├─> /quote - /q\n"
        f"│  └─> <i>Как работать с текстовыми запросами</i>\n"
        f"└─> /help\n"
        f"   └─> <i>Это меню помощи</i>\n\n"

        f"<b>💎 Премиум доступ</b>\n"
        f"├─> /price_list - /pl\n"
        f"│  └─> <i>Тарифы, пакеты и условия</i>\n"
        f"└─> /buy_rules - /br\n"
        f"   └─> <i>Правила VIP-группы</i>\n\n"
        
        f"<b>👤 Аккаунт</b>\n"
        f"├─> /profile_menu | /pm\n"
        f"│  └─> <i>Методы работы с профилем</i>\n"
        f"├─> /me\n"
        f"│  └─> <i>Информация о вашем аккаунте</i>\n"
        f"└─> /whois (@username)\n"
        f"   └─> <i>Информация об аккаунте @username</i>\n\n"

        f"<b>📜 Документы</b>\n"
        f"├─> /free_rules - /fr\n"
        f"│  └─> <i>Правила бесплатного чата</i>\n"
        f"└─> /policy\n"
        f"   └─> <i>Политика конфиденциальности</i>\n\n"

        f"<i>🦊 Просто введите нужную команду</i>"
    )

    markup = markup_link_suffix(message, "help")


    answer = await message.answer(help_text, reply_markup=markup)
    if answer:
        _ = asyncio.create_task(delete_message_safe(answer, TIMER_REMOVAL))


@router.message(or_f(Command('text_quires'), Command('tq')))  # с удалением
async def send_text_help(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    text_help = (
        f"<b>📚 Текстовые запросы ✨</b>\n"
        f"Если ты здесь, значит хочешь узнать больше!\n\n"

        f"<b>🌳 Доступные команды:</b>\n"
        f"├─> <b>Погода</b>\n"
        f"│  └─> <code>Игорь погода {{город}}</code>\n"
        f"│      └─> <i>Пример: Игорь погода Москва</i>\n\n"

        f"├─> <b>Игры</b>\n"
        f"│  └─> <code>Игорь поиграем</code>\n"
        f"│      └─> <i>Вызывает меню игр</i>\n\n"

        f"├─> <b>Идентификация</b>\n"
        f"│  └─> <code>Игорь кто я</code>\n"
        f"│      └─> <i>Ваше место в анимешной пищевой цепи</i>\n\n"

        f"├─> <b>Вероятность события</b>\n"
        f"│  └─> <code>Игорь какова вероятность того что {{запрос}}</code>\n"
        f"│      └─> <i>Вычисляет вероятность события</i>\n\n"

        f"├─> <b>Прощение</b>\n"
        f"│  └─> <code>Игорь {{извинение}}</code>\n"
        f"│      └─> <i>Как говорили Великие люди, 'Пппонять и прррростить'</i>\n\n"

        f"└─> <b>Подтверждение</b>\n"
        f"    └─> <code>Игорь {{вопрос}} ?</code>\n"
        f"        └─> <i>Подтверждает или опровергает вопрос</i>"
    )

    markup = markup_link_suffix(message, "text_quires")

    answer = await message.answer(text_help, reply_markup=markup)
    if answer:
        _ = asyncio.create_task(delete_message_safe(answer, TIMER_REMOVAL))


@router.message(or_f(Command('anime_quires'), Command('aq')))
async def send_anime_quires(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    text_help = (
        "🎌 <b>Аниме-запросы</b> 🎌\n\n"

        "📖 <b>Shikimori</b> (основной сервис):\n"
        "├─ /ssra — <i>Случайное аниме</i> 🎲\n"
        "├─ <code>/ssa {title_name}</code> — <i>Поиск аниме по названию</i> 🔍\n"
        "│   └─ <i>Параметр <b>title_name</b> — название аниме (например: <b>Ту лав ру</b>, <b>Евангелион</b>).</i>\n"
        "├─ <code>/ssag {genre} {rating}</code> — <i>Подборка аниме по жанру и рейтингу</i> 🔍\n"
        "│   ├─ <i>Параметр <b>genre</b> — жанр (например: <b>этти</b>, <b>романтика</b>).</i>\n"
        "│   └─ <i>Параметр <b>rating</b> — рейтинг (по умолчанию 7, можно не указывать).</i>\n"
        "└─ <code>/ssc {character_name}</code> — <i>Подборка персонажей по имени</i> 🔍\n"
        "    └─ <i>Параметр <b>character_name</b> — имя персонажа (например: <b>Сэнко</b>, <b>Нана Девилюк</b>).</i>\n\n"

        "🌐 <b>AniList</b> (иностранный сервис, возможны ошибки):\n"
        "├─ /asra — <i>Случайное аниме</i> 🎲\n"
        "└─ <code>/asa {title_name}</code> — <i>Поиск аниме по названию</i> 🔍\n"
        "   └─ <i>Параметр <b>title_name</b> — название аниме (например: <b>Сэнко</b>, <b>Ту лав ру</b>).</i>\n\n"

        "⚠️ <i>Сообщения автоматически удалятся через 60 секунд.</i>"
    )


    markup = markup_link_suffix(message, "anime_quires")


    answer = await message.answer(text_help, reply_markup=markup)

    if answer:
        _ = asyncio.create_task(delete_message_safe(answer, TIMER_REMOVAL))


@router.message(or_f(Command('free_rules'), Command('fr')))
async def send_free_rules(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    text_free_rules = (
        '<b>📌 Правила бесплатной группы</b>\n\n'
        '<b>Все персонажи, изображённые на артах, являются вымышленными и совершеннолетними (18+).</b>\n'
        'Любые сходства с реальными людьми, событиями или объектами — случайны и не являются намеренными.\n\n'
        '<b>Беспочвенные обвинения в CP</b> при соблюдении вышеуказанных условий рассматриваются как грубое нарушение и ведут к моментальному бану без предупреждений.\n\n'
        '<b>Добро пожаловать!</b>\n'
        'Ниже перечислены правила, созданные для поддержания комфортной и безопасной атмосферы в группе. Пожалуйста, ознакомьтесь с ними и следуйте им.\n\n'
        '<b>🔹 1. Уважение к участникам</b>\n'
        'Оскорбления, угрозы, провокации и намеренное разжигание конфликтов запрещены.\n'
        '🔸 1-е нарушение — предупреждение (0/3)\n'
        '🔸 3 предупреждения — блокировка на 3 дня\n'
        '🔸 Повторная блокировка — возможное удаление из группы, вопрос рассматривается <a href="https://t.me/ZorngeistQual">администрацией</a>\n\n'
        '<b>🔹 2. Запрет на спам и рекламу</b>\n'
        'Нельзя размещать рекламу, ссылки на сторонние ресурсы или навязывать какие-либо продукты/услуги.\n\n'
        '<b>🔹 3. Контент 18+</b>\n'
        'Допустим в разумных пределах. Просим соблюдать меру и уважать границы других участников.\n\n'
        '<b>🔹 4. Флуд и капс</b>\n'
        'Избегайте чрезмерного количества сообщений подряд, а также злоупотребления заглавными буквами и спецсимволами.\n\n'
        '<b>🔹 5. Споры и жалобы</b>\n'
        'Все вопросы по ценам, доступу и другим организационным моментам решаются только через <a href="https://t.me/ZorngeistQual">личные сообщения администратору</a>.\n\n'
        '<b>🔹 6. Достоверность информации</b>\n'
        'Запрещено распространять ложную информацию о проекте. Нам важно поддерживать доверие и честность.\n\n'
        '<b>🔹 7. Запрет на обсуждение сторонних ИИ-проектов и генераторов</b>\n'
        'Группа не предназначена для технических разговоров. Здесь запрещено обсуждать любые внешние ИИ-сервисы, генераторы, алгоритмы, приложения, плагины и прочие инструменты для создания артов.\n\n'
        'Проект предоставляет участникам уникальный визуальный контент.\n'
        'Мы сохраняем фокус на творческой атмосфере, а не на технической кухне.\n\n'
        '<b>❌ Нарушениями считаются:</b>\n'
        '→ Упоминания других нейросетей, сайтов и приложений для генерации изображений\n'
        '→ Советы по использованию стороннего софта\n'
        '→ Попытки выяснить, как создаются арты внутри проекта\n'
        '→ Любые технические обсуждения, не связанные с общением в сообществе\n\n'
        '🔸 1-е нарушение — удаление сообщения\n'
        '🔸 2-е — временный мут\n'
        '🔸 3-е — прощаемся\n\n'
        'Мы используем собственные уникальные решения, и технические детали не разглашаются.\n\n'
        '<b>🔹 8. Попрошайничество и плагиат</b>\n'
        'Постоянные просьбы о бесплатных артах, а также публикация чужих работ без разрешения не допускаются.\n\n'
        '<b>🔹 9. Полномочия администрации и модераторов</b>\n'
        'Администрация (<a href="https://t.me/ZorngeistQual">связаться</a>) оставляет за собой право удалять сообщения или участников без объяснения причин.\n\n'
        '✅ Соблюдение этих правил помогает поддерживать тёплую, творческую и безопасную атмосферу для всех участников.\n'
        'Вступая в группу и просматривая её контент, вы подтверждаете, что вам исполнилось 18 лет.\n'
        'Спасибо, что вы с нами! 🚀'
    )

    markup = markup_link_suffix(message, "free_rules")


    answer = await message.answer(text_free_rules, reply_markup=markup)

    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))


@router.message(or_f(Command('buy_rules'), Command('br')))
async def send_buy_rules(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    text_buy_rules = (
    "Все персонажи, изображённые на артах, являются вымышленными и совершеннолетними (18+).\n"
    "Любые сходства с реальными людьми, событиями или объектами — случайны и не являются намеренными.\n\n"
    "Беспочвенные обвинения в CP при соблюдении вышеуказанных условий рассматриваются как грубое нарушение и ведут к моментальному бану без предупреждений.\n\n"
    "— — —\n\n"
    "<b>1. Правила пользования чатом</b>\n\n"
    "🔹 <b>1.1 Уважительное общение.</b>\n"
    "Запрещены оскорбления, угрозы, разжигание конфликтов и провокации.\n"
    "(0/3 предупреждений → бан на трое суток)\n\n"
    "🔹 <b>1.2 Запрещены спам, реклама и ссылки на сторонние ресурсы.</b>\n\n"
    "🔹 <b>1.3 Контент 18+ разрешён, но в умеренном формате.</b>\n\n"
    "🔹 <b>1.4 Запрещено флудить, злоупотреблять капсом и спецсимволами.</b>\n\n"
    "🔹 <b>1.5 Все спорные вопросы (цены, доступ, жалобы) — только в ЛС администратора:</b> "
    "<a href=\"https://t.me/ZorngeistQual\">https://t.me/ZorngeistQual</a>\n\n"
    "🔹 <b>1.6 Запрещено распространять фейки о проекте или вводить участников в заблуждение.</b>\n\n"
    "🔹 <b>1.7 Попрошайничество и публикация чужих работ без разрешения запрещены.</b>\n\n"
    "🔹 <b>1.8 Администрация оставляет за собой право удалить любое сообщение или участника без объяснения причин.</b>\n\n"
    "— — —\n\n"
    "<b>2. Правила пользования платной группой</b>\n\n"
    "🚨 Важно! Все изображения в группе содержат уникальные невидимые цифровые метки, позволяющие отслеживать источник утечки.\n"
    "Если изображение будет обнаружено в открытом доступе, система автоматически определит нарушителя.\n\n"
    "🔸 <b>2.1 Запрещено публичное распространение, передача или продажа артов третьим лицам.</b>\n\n"
    "🔸 <b>2.2 Категорически запрещено загружать арты на сайты, соцсети и форумы.</b>\n\n"
    "🔸 <b>2.3 Запрещено удалять или изменять метаданные изображений.</b>\n\n"
    "🔸 <b>2.4 Любая попытка обхода платного доступа (раздача, шаринг, слив) = мгновенный бан без возврата средств.</b>\n\n"
    "🔸 <b>2.5 Утечки контента отслеживаются. Нарушители теряют доступ без возврата.</b>\n\n"
    "🔸 <b>2.6 Допустимо частное использование артов — только в закрытых группах, в минимальных объёмах и с обязательной ссылкой на бесплатную группу.</b>\n\n"
    "🔸 <b>2.7 Если вы заметили нарушение — сообщите <a href=\"https://t.me/ZorngeistQual\">администратору</a>:</b> "
    "\n\n"
    "— — —\n\n"
    "✅ Соблюдение этих правил помогает поддерживать тёплую, творческую и безопасную атмосферу для всех участников.\n"
    "Вступая в группу и просматривая её контент, вы подтверждаете, что вам исполнилось 18 лет.\n"
    "Спасибо, что вы с нами! 🚀"
)

    markup = markup_link_suffix(message, "buy_rules")

    answer = await message.answer(text_buy_rules, reply_markup=markup)

    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))


@router.message(or_f(Command('pl'), Command('price_list')))
async def send_price_list(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    price_list = (
        "🎴 <b>Добро пожаловать в Ero no Sekai: Yami no Yokubō</b>\n"
        "Доступ к эксклюзивным артам на ваших условиях\n\n"

        "📜 <b>Варианты доступа:</b>\n"
        "<b>Free Pass</b>\n"
        "— Бесплатный доступ к артам с ватермарками\n\n"

        "<b>Buy Pass</b>\n"
        "— Полная коллекция без ватермарок + арты в 4K\n\n"

        "💰 <b>Тарифы:</b>\n"
        "① Месячная подписка — 379 ₽/мес\n"
        "② Пожизненный VIP — 3 799 ₽ (единоразово)\n\n"

        "🖼 <b>Пакеты артов:</b>\n\n"

        "<b>1. Базовый набор</b>\n"
        "Приобретение готовых артов по конкретному герою:\n"
        "— 100 артов · 249 ₽\n"
        "— 200 артов · 479 ₽\n"
        "— 300 артов · 799 ₽\n"
        "— 400 артов · 1 199 ₽\n\n"

        "▸ Ватермарки удаляются. Арты остаются в общем каталоге.\n\n"

        "<b>2. Эксклюзивный выкуп¹</b>\n"
        "Тот же базовый набор, но:\n"
        "— 100 артов · 749 ₽\n"
        "— 200 артов · 1 349 ₽\n"
        "— 300 артов · 1 949 ₽\n"
        "— 400 артов · 2 399 ₽\n\n"

        "▸ Арты полностью удаляются из каталога. Вы получаете исключительные права.\n\n"

        "<b>3. Создание набора²</b>\n"
        "<b>а) С исключительными правами:</b>\n"
        "— 100 артов · 1 099 ₽\n"
        "— 200 артов · 1 899 ₽\n"
        "— 300 артов · 2 599 ₽\n"
        "— 400 артов · 3 199 ₽\n\n"

        "<b>б) С коммерческим использованием³:</b>\n"
        "— 100 артов · 649 ₽\n"
        "— 200 артов · 1 099 ₽\n"
        "— 300 артов · 1 599 ₽\n"
        "— 400 артов · 1 999 ₽\n\n"

        "▸ <b>Условия для всех вариантов:</b>\n"
        "- Предоплата 30% → предпросмотр с ватермарками\n"
        "- При полной оплате → арты передаются вам\n"
        "- При отказе → арты публикуются в моих группах (аванс не возвращается)\n\n"

        "📌 <b>Сноски:</b>\n"
        "¹ Эксклюзивный выкуп — арты удаляются из общего доступа. Вы — единственный владелец.\n"
        "² Создание набора:\n"
        "        а) ваша эксклюзивная собственность;\n"
        "        б) мы используем арты набора для насыщения групп.\n"
        "³ В коммерческих наборах некоторые арты могут повторяться в разных альбомах (например, кроссоверы персонажей из вселенных).\n\n"

        "📲 <b>Как заказать:</b>\n"
        '→ Напишите <a href="https://t.me/EroNoSekaiBot">боту</a>\n'
        '→ Свяжитесь с <a href="https://t.me/ZorngeistQual">администратором</a>'
    )

    markup = markup_link_suffix(message, "price_list")


    answer = await message.answer(price_list, reply_markup=markup, disable_web_page_preview=True)

    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))

@router.message(Command('policy'))
async def send_policy_message(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    policy_text = (
        "🔐 <b>Ero no Sekai: Yami no Yokubo - Политика конфиденциальности</b>\n\n"
        "<i>Shinigami наблюдает, но не собирает ваши тайны...</i>\n\n"

        "📜 <b>1. Какие данные мы храним</b>\n"
        "• Только необходимый минимум: ваш <code>user_id</code> и <code>username</code>\n"
        "• Никаких личных данных, переписок или медиафайлов\n"
        "• Статистика использования команд (без привязки к личности)\n\n"

        "🛡️ <b>2. Как используем данные</b>\n"
        "• Исключительно для функционала бота\n"
        "• Для модерации и предотвращения злоупотреблений\n"
        "• Никогда не передаём третьим лицам\n\n"

        "⚰️ <b>3. Особенности Shinigami</b>\n"
        "• Бот не сохраняет историю ваших действий\n"
        "• Все временные данные уничтожаются автоматически\n"
        "• Мы не интересуемся вашей настоящей личностью\n\n"

        "🌑 <b>4. Ваши права</b>\n"
        "• Можете отказаться от взаимодействия с ботом в любой момент\n"
        "• Запросить удаление ваших данных через обращение к @ZorngeistQual\n"
        "• Полная анонимность гарантируется\n\n"

        "<i>Shinigami лишь наблюдает за миром теней, не нарушая его гармонии...</i>\n\n"
    )

    markup = markup_link_suffix(message, "policy")


    answer = await message.answer(policy_text, reply_markup=markup)

    if message:
        _ = asyncio.create_task(delete_message_safe(message, TIMER_REMOVAL))


@router.message(or_f(Command('quote'), Command('q')))
async def send_quote(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    message = await message.answer(random.choice(quotes.quotes))

    # if message:
    #     _ = asyncio.create_task(delete_message_safe(message, 60))

@router.message(or_f(Command("staff")))
async def send_staff_list(message: types.Message):
    await message.reply(f"Актуальный список администраторов и модераторов: {str(ACTUAL_STAFF_NICK_LIST)}")

@router.message(or_f(Command('translate'), Command('t')))
async def send_translate(message: types.Message, command: F.CommandObject):

    if not command.args:
        return await message.reply('❌ Укажите текст для перевода')

    try:
        text_to_translate = message.text.split(" ", 1)[1].strip()
        logger.debug(f"Текст для перевода: {text_to_translate}")

        translated = await async_translate(text_to_translate)

        if not translated:
            return await message.reply('⚠️ Не удалось выполнить перевод')

        await message.reply(translated)

    except Exception as e:
        await message.reply(f'🚫 Ошибка: {str(e)}')


@router.message(or_f(Command('ginfo'), Command('ginfo')))
async def send_anime_quires(message: types.Message):
    if message:
        _ = asyncio.create_task(delete_message_safe(message, 60))

    text_info = (
        f'Подробнее о группе и боте можно узнать на <a href="{BASE_URL_APP_COMMANDS}">сайте</a>'
        f" или в мини-приложении"

    )


    markup = markup_link_suffix(message, "")


    answer = await message.answer(text_info, reply_markup=markup)



@router.message(Command('genres'))
async def send_genres(message: types.Message, command: F.CommandObject):
    genre_keys = [key.capitalize() for key in GENRES.keys()]

    genre_str = ', '.join(genre_keys)

    await message.answer(genre_str)


@router.message(or_f(Command('28012003'), Command('28012003')))
@require_access(10)
async def add_me_test_db(message: types.Message, command: F.CommandObject, users_data, **kwargs):
    users_data.add_new_user(message.from_user.id,
                         message.from_user.username,
                         message.from_user.first_name,
                         message.from_user.last_name
                         )
    logger.debug("Успешное создание юзера")


def markup_link_suffix(message, suffix: str):
    if message.chat.type in {"group", "supergroup"}:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📖 Узнать больше", url=BASE_URL_APP_COMMANDS + suffix)]
            ]
        )
        return markup
    else:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="📖 Узнать больше",
                    web_app=WebAppInfo(url=BASE_URL_APP_COMMANDS + suffix)
                )]
            ]
        )
        return markup

logger.info("[Commands] - Зарегистрирован успешно")