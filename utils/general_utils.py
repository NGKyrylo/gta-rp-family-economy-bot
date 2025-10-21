import discord
from discord import Embed
from datetime import datetime, timedelta
from config import TIMEZONE, SHEET_URL, FAMILY_ROLE_ID

def parse_report_date(date_str=None):
    today = datetime.now(TIMEZONE)
    year = today.year

    """Парсить дату звіту з формату dd.mm"""
    if date_str:
        try:
            day, month = map(int, date_str.split("."))
            _ = datetime(year, month, day, tzinfo=TIMEZONE)
            # year = datetime.today().year
            return f"{day}.{month}.{year}"
        except ValueError:
            return None
    # return f"{datetime.today().day}.{datetime.today().month}.{datetime.today().year}"
    return today.strftime("%d.%m.%Y")

def get_points_word(points: float) -> str:
    """Helper to get correct word form for points"""
    if points == 1:
        return "поінт"
    if 1 < points < 5:
        return "поінти"
    return "поінтів"

async def send_week_summary(channel: discord.TextChannel, guild: discord.Guild, rewards_data: dict):
    """
    Відправляє підсумки минулого тижня у канал у сучасному Embed-оформленні.
    """

    top_players = rewards_data.get("top_players", [])

    # 🏅 Визначаємо структуру для зберігання переможців по місцях
    places = {1: [], 2: [], 3: []}
    for entry in top_players:
        place = entry.get("place")
        member = guild.get_member(entry["user_id"])
        if member and place in places:
            places[place].append(member.mention)

    # 🥇🥈🥉 Форматуємо місця — завжди показуємо всі
    def format_place(place_num: int, members: list[str]) -> str:
        emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        prizes = {1: "150 000", 2: "100 000", 3: "50 000"}

        if members:
            members_text = " ".join(members)
            return f"{emojis[place_num]} **{place_num} місце** — {members_text} (`+{prizes[place_num]}💰`)"
        else:
            return f"{emojis[place_num]} **{place_num} місце** — *Ніхто цього тижня не потрапив 😅*"

    # 🧾 Основний опис Embed
    description = (
        "За результатами участі в квестах минулого тижня оголошено наступних переможців:\n\n"
        f"{format_place(1, places[1])}\n"
        f"{format_place(2, places[2])}\n"
        f"{format_place(3, places[3])}\n\n"
        "🎉 Переможців вітаємо!\n"
        "Решта — не засмучуйтесь, цього тижня ви можете відігратись 💪🫡"
    )

    # 📊 Embed
    embed = discord.Embed(
        title="📊 Підсумки квестового тижня 🐅",
        description=description,
        color=discord.Color.gold()
    )

    embed.add_field(
        name="📈 Перевірити свої результати",
        value=f"[Відкрити Google Таблицю]({SHEET_URL})",
        inline=False
    )

    embed.set_footer(text="Переможці можуть отримати свій бонус 🎁")

    # 📨 Надсилаємо у канал
    family_role = guild.get_role(FAMILY_ROLE_ID)
    if family_role:
        await channel.send(f"{family_role.mention} 🐅", embed=embed)
    else:
        await channel.send("🐅", embed=embed)
