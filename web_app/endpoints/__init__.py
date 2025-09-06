from web_app.endpoints import (
    about,
    watch,
    index as main_index,
    kodik
)

from web_app.endpoints.bot_commands_endpoints import (
    admin_commands,
    anime_commands,
    main_commands,
    profile_commands,
    index as bot_index
)

from web_app.endpoints.tg_webapp_endpoints import (
    anime_quires,
    buy_rules,
    free_rules,
    help,
    policy,
    price_list,
    staff,
    text_quires,
    index as web_app_index
)

from web_app.endpoints.errors import (
    errors_5xx,
    errors_4xx
)

routers = [
    (about.router, None),
    (watch.router, None),
    (main_index.router, None),
    (kodik.router, None),

    (bot_index.router, "/bot_commands"),
    (main_commands.router, "/bot_commands"),
    (anime_commands.router, "/bot_commands"),
    (profile_commands.router, "/bot_commands"),
    (admin_commands.router, "/bot_commands"),

    (free_rules.router, "/tg_webapp"),
    (buy_rules.router, "/tg_webapp"),
    (help.router, "/tg_webapp"),
    (policy.router, "/tg_webapp"),
    (price_list.router, "/tg_webapp"),
    (staff.router, "/tg_webapp"),
    (anime_quires.router, "/tg_webapp"),
    (text_quires.router, "/tg_webapp"),
    (web_app_index.router, "/tg_webapp"),

    (errors_5xx.router, None),
    (errors_4xx.router, None),
]