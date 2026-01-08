import discord
from config import FIRST_WARN_ROLE, SECOND_WARN_ROLE, THIRD_WARN_ROLE, WARN_CHANNEL_ID, HEAD_OF_DISCIPLINE_ID, DISCIPLINE_CHANNEL_ID
import json
import os
from views.warn_removal_view import WarnRemovalView

WEEK_SUMMARY_FILE = os.path.join("data", "week_summary.json")


async def issue_warn(guild: discord.Guild, member: discord.Member, reason: str, cost: int, is_quest_related: bool):
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

    if warn_given is None:
        return 'max_warns_reached'

    # формуємо текст ембед
    description = (
        f"**Кому:** {member.mention}\n"
        f"**Причина:** {reason}\n\n"
        f"**Для закриття варну потрібно:**\n"
    )

    formatted_cost = f"{cost:,}".replace(",", " ")

    if is_quest_related:
        description += (
            f"- Надіслати скріни з **2-х квестів**, або\n"
            f"- Оплатити недонабрані поінти через сейф ({formatted_cost}$ за 1 поінт).\n\n"
        )
    else:
        description += "- Оплатити **{formatted_cost}$** у сейф.\n\n"

    description += (
        f"💡 **Увага:** скріни виконання або підтвердження оплати потрібно надсилати під цим постом.\n\n"
        f"_⚠️ На рахунок деталей та апеляції — пишіть у приват {guild.get_member(HEAD_OF_DISCIPLINE_ID).mention}._"
    )

    embed = discord.Embed(
        description=description,
        color=discord.Color.gold()
    )

    # if warn_given is None:
        # embed.set_footer(text=f"⚠️ На рахунок деталей та апеляції — пишіть у приват {guild.get_member(HEAD_OF_DISCIPLINE_ID).mention}.")
    # else:
    #     embed.set_footer(text=f"Видано WARN: {warn_given.name}")

    view = WarnRemovalView()

    warn_channel = guild.get_channel(WARN_CHANNEL_ID)
    if warn_channel and isinstance(warn_channel, discord.ForumChannel):
        thread = await warn_channel.create_thread(
            name="⚠️ WARN",
            content=f"{member.mention}",
            embed=embed,
            view=view
        )

        if warn_given == warn_roles[-1]:
            await thread.thread.send(
                f"{member.mention} ⚠️ У вас є **24 години** на оплату всіх 3-х варнів, "
                f"після чого буде подана заявка на кік."
            )

    return "warn_issued"


async def send_warn_users_from_week_summary(guild: discord.Guild, min_points: float):
    """Беремо non_quota_users з week_summary.json та створюємо список "лодирів"."""
    if not os.path.exists(WEEK_SUMMARY_FILE):
        print("❌ week_summary.json не знайдено")
        return

    with open(WEEK_SUMMARY_FILE, "r", encoding="utf-8") as f:
        week_data = json.load(f)

    non_quota_users = week_data.get("non_quota_users", [])

    description_lines = [
        f"- {guild.get_member(int(user['user_id'])).display_name} — {user['points']} поінтів"
        for user in non_quota_users
    ]

    embed = discord.Embed(
        title="⚠️ Користувачі, які не досягли мінімуму поінтів за тиждень (іммунітетні користувачі не враховані)",
        description = "\n".join(description_lines) if description_lines else "Всі користувачі досягли мінімуму поінтів за тиждень.",
        color=discord.Color.gold()
    )

    discipline_chanel = guild.get_channel(DISCIPLINE_CHANNEL_ID)
    if discipline_chanel:
        await discipline_chanel.send(embed=embed)
