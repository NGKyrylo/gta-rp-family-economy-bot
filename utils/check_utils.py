from discord.ext import commands
from config import (
    BOT_DEVELOPER_ID,
    ADMIN_ROLE_IDS,
    ECONOMY_CONTROLLER_ROLE_IDS,
    RECRUITER_ROLE_IDS
)

# ===== БАЗОВА ПЕРЕВІРКА =====
def has_any_role(member, role_ids):
    """Перевіряє, чи має користувач одну з ролей."""
    if not role_ids:
        return True  # якщо список порожній — відкрито всім
    return any(role.id in role_ids for role in member.roles)

# ===== РІВНІ ДОСТУПУ =====
def is_bot_developer(member):
    """Перевірка на розробника."""
    return member.id == BOT_DEVELOPER_ID

def is_admin(member):
    return (
        is_bot_developer(member)
        or has_any_role(member, ADMIN_ROLE_IDS)
    )

def is_economy_controller(member):
    return (
        is_admin(member)
        or has_any_role(member, ECONOMY_CONTROLLER_ROLE_IDS)
    )

def is_recruiter(member):
    return (
        is_economy_controller(member)
        or has_any_role(member, RECRUITER_ROLE_IDS)
    )

# ===== ДЕКОРАТОРИ =====
def is_bot_developer_only():
    async def predicate(ctx):
        if is_bot_developer(ctx.author):
            return True
        raise commands.CheckFailure("⛔ У вас немає прав адміністратора.")
    return commands.check(predicate)

def is_admin_only():
    async def predicate(ctx):
        if is_admin(ctx.author):
            return True
        raise commands.CheckFailure("⛔ У вас немає прав адміністратора.")
    return commands.check(predicate)

def is_economy_controller_only():
    async def predicate(ctx):
        if is_economy_controller(ctx.author):
            return True
        raise commands.CheckFailure("⛔ У вас немає прав контролю економіки.")
    return commands.check(predicate)

def is_recruiter_only():
    async def predicate(ctx):
        if is_recruiter(ctx.author):
            return True
        raise commands.CheckFailure("⛔ У вас немає прав рекрутера.")
    return commands.check(predicate)

