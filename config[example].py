from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Kyiv")

DISCORD_TOKEN = ""      # YOUR DISCORD BOT TOKEN HERE
GUILD_ID = None         # ID OF SERVER
COMMAND_PREFIX = "!"    # PREFIX FOR BOT COMMANDS
SPREADSHEET_ID = ""     # GOOGLE SHEET ID FOR STORING DATA
SHEET_URL = ""          # URL TO GOOGLE SHEET

##############################################################################

# ==========================================================
# 🕓 Legacy Role Variables (kept for potential compatibility)
# ----------------------------------------------------------
# These were used in early versions before the permission
# utility system was implemented. They are likely no longer
# referenced, but remain here temporarily until confirmed safe
# to remove in future updates.
# ==========================================================

ADMIN_ROLE_ID = None             # ROLE ID FOR ADMINS
FAMILY_ROLE_ID = None            # ROLE ID FOR FAMILY MEMBERS
REPORT_INSPECTOR_ROLE_ID = None  # ROLE ID FOR REPORT INSPECTORS

# ==========================================================
# ✅ Current active role lists (used by permission utilities)
# ==========================================================

BOT_DEVELOPER_ID = None             # USER ID OF THE BOT DEVELOPER
ADMIN_ROLE_IDS = []                 # LIST OF ROLE IDS FOR ADMINS
ECONOMY_CONTROLLER_ROLE_IDS = []    # LIST OF ROLE IDS FOR ECONOMY CONTROLLERS
RECRUITER_ROLE_IDS = []             # LIST OF ROLE IDS FOR RECRUITERS

##############################################################################

ANNOUNCEMENT_CHANNEL_ID = None   # CHANNEL ID FOR ANNOUNCEMENTS

FIRST_WARN_ROLE = None         # ROLE ID FOR FIRST WARNING
SECOND_WARN_ROLE = None        # ROLE ID FOR SECOND WARNING
THIRD_WARN_ROLE = None         # ROLE ID FOR THIRD WARNING
WARN_CHANNEL_ID = None         # CHANNEL ID FOR WARN NOTIFICATIONS (FORUM TYPE CHANNEL)

REPORT_CHANNELS = {
    "quest": None,          # CHANNEL ID FOR QUEST REPORTS
    "donation": None        # CHANNEL ID FOR DONATION REPORTS
}

POINT_COST = 50000          # COST IN USD FOR 1 POINT
REQUIRED_WEEKLY_POINTS = 2  # REQUIRED POINTS PER WEEK

REPORT_TYPES = {            # DEFINITION OF REPORT TYPES AND THEIR PROPERTIES FOR COMMANDS
    # Regular activities
        "патруль": {
        "label": "Патруль",
        "category": "quest",
        "is_family_quest": False,
        "requires_hours": True,
        "points_per_hour": 1.0,
        "help": "`!звіт патруль <години> [дата]` - охорона будинку (1 бал за годину)",
        "aliases": ["патрулювання", "охорона", "патруль будинку"]
    },
    
    # Family quests
    "допомога": {
        "label": "Допомога громадянам",
        "category": "quest",
        "is_family_quest": True,
        "variants": {
            "повна": {"points": 1.0, "required_screenshots": 2, "label": ""},
            "хотдог": {"points": 0.5, "required_screenshots": 1, "label": "Хот-доги"},
            "роздача": {"points": 0.5, "required_screenshots": 1, "label": "Роздача"},
            "половина": {"points": 0.5, "required_screenshots": 1, "label": "Половина"}
        },
        "help": "`!звіт допомога <повна/хотдог/роздача/половина> [дата]` - допомога громадянам",
        "aliases": ["допомога громадянам", "допомога людям", "хотдоги"]
    },
    "товарка": {
        "label": "Товарний вибух",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт товарка [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["товарний", "товарний вибух", "тов"]
    },
    "суботник": {
        "label": "Суботник",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт суботник [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["прибирання", "очистка"]
    },
    "рибалка": {
        "label": "Рибний день",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт рибалка [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["риба", "рибний"]
    },
    "гриби": {
        "full_name": "Лісові трофеї",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт гриби [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["лісові трофеї", "гриби", "збір грибів"]
    },
    "ліс": {
        "full_name": "Заклик лісоруба",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт ліс [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["заклик лісоруба", "лісоруб", "дерево"]
    },
    "полювання": {
        "full_name": "Мисливський сезон",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт полювання [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["мисливський сезон", "мисливство", "шкури"]
    },
    "паливо": {
        "full_name": "Паливо прогресу",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт паливо [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["паливо прогресу", "нафта", "качка"]
    },
    "шахта": {
        "full_name": "Шахтарська справа",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт шахта [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["шахтарська справа", "шахтар", "копання"]
    },
    "війна": {
        "full_name": "Влада через кров",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт війна [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["влада через кров", "війна", "перемоги"]
    },
    "захист": {
        "full_name": "Вартові свого",
        "category": "quest",
        "is_family_quest": True,
        "help": "`!звіт захист [дата]` - 1 бал",
        "points": 1.0,
        "aliases": ["вартові свого", "захист", "охорона"]
    },

    
    # Other activities
    "івент": {
        "label": "Сімейний івент",
        "category": "quest",
        "is_family_quest": False,
        "help": "`!звіт івент [дата]` - участь у сімейному івенті (1 бал)"
    },
    "збори": {
        "label": "Сімейні збори",
        "category": "quest",
        "is_family_quest": False,
        "help": "`!звіт збори [дата]` - присутність на зборах (1 бал)"
    },
    
    # Donations
    "внесок": {
        "label": "Внесок",
        "category": "donation",
        "variants": {
            "поінти": {
                "label": "Купівля поінтів",
                "description": f"1 поінт = {POINT_COST}$ (тільки цілі числа)"
            },
            "інше": {
                "label": "Благодійний внесок",
                "description": "На потреби сім'ї"
            }
        },
        "help": [
            "`!звіт внесок <сума> поінти` - купівля поінтів",
            f"(1 поінт = {POINT_COST}$, тільки цілі числа)",
            "`!звіт внесок <сума> <призначення>` - благодійний внесок"
        ],
        "aliases": ["донат", "пожертва", "пожертвування"]
    },
}

QUESTS_CHANNEL = None  # CHANNEL ID FOR ANNOUNCING FAMILY QUESTS (FORUM TYPE CHANNEL)

QUESTS = {             # DEFINITIONS OF FAMILY QUESTS AND THEIR PROPERTIES FOR ANNOUNCEMENTS
    "допомога": {
        "full_name": "Допомога громадянам",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+ місце роздачі' в коментарі.\n\n"
            "🎯 Квест **Допомога громадянам** складається з 2-х частин:\n"
            "1️⃣ Продаж 100 хот-догів від сім'ї 🌭\n"
            "2️⃣ Роздача по 1000$ 50 людям до 6 рівня 💵\n\n"
            "📌 Просимо заздалегідь вказати точку, де ви будете роздавати тисячу новачкам.\n"
            "⚠️ Не залишайте обрану зону, інакше ризикуєте втратити зарплату.\n"
            "👤 Одна точка — одна людина.\n\n"
            "📍 Приклади точок, які можна зайняти:\n"
            "⬆️ Верхній спавн\n"
            "⬅️ Лівий спавн\n"
            "➡️ Правий спавн\n"
            "🛵 Кур’єр Glovo\n"
            "🚗 Автошкола\n"
            "📦 Навантажувач\n"
            "🏥 Лікарня в Лос-Сантосі\n"
            "🏥 Лікарня в Сенді-Шорс\n\n"
            "💡 Ви не обмежені лише цими варіантами!"
        ),
        "image": "https://media.discordapp.net/attachments/652911880465154070/1428955290497187993/dop.png?ex=68f461d1&is=68f31051&hm=73f0152d5c19337df52b7858ab494c93c14b6b3651faaec9230bd8cdcd0bf345&=&format=webp&quality=lossless&width=525&height=350",
        "duration_hours": 12,
        "cooldown_hours": 24,
        "aliases": ["допомога громадянам", "допомога людям", "хотдоги"]
    },

    "товарка": {
        "full_name": "Товарний вибух",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "📦 Збір у гаражі.\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі."
        ),
        "image": "https://media.discordapp.net/attachments/652911880465154070/1428955271262240982/tov.png?ex=68f461cd&is=68f3104d&hm=a32041e8c88a6e6e0825f7b3a6aefaadb1d412f624a63c777eeb86ad760fff8b&=&format=webp&quality=lossless&width=1376&height=917",
        "duration_hours": 6,
        "cooldown_hours": 24,
        "aliases": ["товарний", "товарний вибух", "тов"]
    },

    "суботник": {
        "full_name": "Суботник",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🚮 Збираємось, беремо рукавички й чистимо вулиці штату від сміття (але не поліцейських 😎).\n"
            "💵 1.000.000 ділиться між учасниками у разі виконання.\n"
            "📍 Збір на пляжі біля будинку.\n\n"
            "🦜 Сміття — не тільки госка. Тому не перепутай мішок із поліцейським!"
        ),
        "image": "https://media.discordapp.net/attachments/652911880465154070/1428957742575521903/subot.png?ex=68f4641a&is=68f3129a&hm=7466695608a29f9050132528ef9383c562578f71f0a5460f2efd92f0076415e5&=&format=webp&quality=lossless&width=525&height=350",
        "duration_hours": 6,
        "cooldown_hours": 24,
        "aliases": ["прибирання", "очистка"]
    },

    "рибалка": {
        "full_name": "Рибний день",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Квест **Рибний день** передбачає участь у сімейному рибальському заході. Деталі оголошуються під час запуску.\n"
            "🦞 Не забудь наживку й гарний настрій!"
        ),
        "image": "https://media.discordapp.net/attachments/652911880465154070/1428958297364631583/fish.png?ex=68f4649e&is=68f3131e&hm=1712b5f1be9d2451773a43a01266a8d2a24710f5982821713f34fdc991943c80&=&format=webp&quality=lossless&width=1376&height=917",
        "duration_hours": 6,
        "cooldown_hours": 24,
        "aliases": ["риба", "рибний"]
    },

    "гриби": {
        "full_name": "Лісові трофеї",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "🍄 Зібрати 500 печериць\n"
            "🍄 Зібрати 400 глив\n"
            "💰 Продати 500 печериць скупнику\n"
            "💰 Продати 400 глив скупнику"
        ),
        "image": None,
        "duration_hours": 6,
        "cooldown_hours": 24,
        "aliases": ["лісові трофеї", "гриби", "збір грибів"]
    },

    "ліс": {
        "full_name": "Заклик лісоруба",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "🌲 Видобути 500 соснової колоди\n"
            "🌳 Видобути 400 дубової колоди\n"
            "💰 Продати сосну скупнику\n"
            "💰 Продати дуб скупнику"
        ),
        "image": None,
        "duration_hours": 8,
        "cooldown_hours": 24,
        "aliases": ["заклик лісоруба", "лісоруб", "дерево"]
    },

    "полювання": {
        "full_name": "Мисливський сезон",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "🦌 Продати 250 шкур скупнику"
        ),
        "image": None,
        "duration_hours": 4,
        "cooldown_hours": 24,
        "aliases": ["мисливський сезон", "мисливство", "шкури"]
    },

    "паливо": {
        "full_name": "Паливо прогресу",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "⛽ Видобути 500 разів паливо на нафтокачці"
        ),
        "image": None,
        "duration_hours": 6,
        "cooldown_hours": 24,
        "aliases": ["паливо прогресу", "нафта", "качка"]
    },

    "шахта": {
        "full_name": "Шахтарська справа",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "⛏️ Видобути 500кг заліза\n"
            "⛏️ Видобути 200кг міді\n"
            "⛏️ Видобути 500г срібла"
        ),
        "image": None,
        "duration_hours": 8,
        "cooldown_hours": 24,
        "aliases": ["шахтарська справа", "шахтар", "копання"]
    },

    "війна": {
        "full_name": "Влада через кров",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "⚔️ Здобути 3 перемоги у війні сімей"
        ),
        "image": None,
        "duration_hours": 12,
        "cooldown_hours": 48,
        "aliases": ["влада через кров", "війна", "перемоги"]
    },

    "захист": {
        "full_name": "Вартові свого",
        "description": (
            "🔥 Відкритий набір для виконання сімейного квесту! 🔥\n"
            "💰 Доступно 10 платних слотів.\n"
            "✍️ Для отримання зарплатні — постав '+' в коментарі.\n\n"
            "🎯 Завдання:\n"
            "🛡️ Захистити 2 території у війні сімей"
        ),
        "image": None,
        "duration_hours": 12,
        "cooldown_hours": 48,
        "aliases": ["вартові свого", "захист", "оборона"]
    }
}
