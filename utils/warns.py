import discord
from config import FIRST_WARN_ROLE, SECOND_WARN_ROLE, THIRD_WARN_ROLE, WARN_CHANNEL_ID
import json
import os

WEEK_SUMMARY_FILE = os.path.join("data", "week_summary.json")


async def issue_warn(guild: discord.Guild, member: discord.Member, current_points: float, min_points: float):
    """Видає WARN користувачу та публікує пост у форумі."""

    warn_roles_ids = [FIRST_WARN_ROLE, SECOND_WARN_ROLE, THIRD_WARN_ROLE]
    warn_roles = [guild.get_role(rid) for rid in warn_roles_ids]

    # визначаємо яку роль можна видати
    warn_given = None
    for role in warn_roles:
        if role not in member.roles:
            await member.add_roles(role)
            warn_given = role
            break

    # формуємо текст ембед
    description = (
        f"**Кому:** {member.mention}\n"
        f"**Причина:** Не набрано мінімальну кількість поінтів за тиждень.\n\n"
        f"**Що потрібно зробити:**\n"
        f"- Надіслати скріни з **2-х квестів**, або\n"
        f"- Оплатити недонабрані поінти через сейф (50.000$ за 1 поінт).\n"
        f"💡 **Увага:** скріни виконання або підтвердження оплати потрібно надсилати під цим постом.\n\n"
        f"**Поточний стан:** Ви набрали {current_points} поінтів за тиждень, мінімум потрібно {min_points} поінтів.\n"
        # f"Для перевірки своїх поінтів скористайтесь каналом ⁠<#{WARN_CHANNEL_ID}>."
    )

    embed = discord.Embed(
        description=description,
        color=discord.Color.gold()
    )

    if warn_given is None:
        embed.set_footer(text="⚠️ У цього члена родини максимальна кількість WARN досягнута. Видати новий WARN було неможливо.")
    # else:
    #     embed.set_footer(text=f"Видано WARN: {warn_given.name}")

    warn_channel = guild.get_channel(WARN_CHANNEL_ID)
    if warn_channel and isinstance(warn_channel, discord.ForumChannel):
        await warn_channel.create_thread(
            name="⚠️ WARN",
            content=f"{member.mention}",
            embed=embed
        )


async def issue_warns_from_week_summary(guild: discord.Guild, min_points: float):
    """Беремо non_quota_users з week_summary.json та видаємо WARN усім."""
    if not os.path.exists(WEEK_SUMMARY_FILE):
        print("❌ week_summary.json не знайдено")
        return

    with open(WEEK_SUMMARY_FILE, "r", encoding="utf-8") as f:
        week_data = json.load(f)

    non_quota_users = week_data.get("non_quota_users", [])

    for data in non_quota_users:
        uid = data.get("user_id")
        points = data.get("points", 0)
        member = guild.get_member(uid)
        if member:
            await issue_warn(guild, member, current_points=points, min_points=min_points)
