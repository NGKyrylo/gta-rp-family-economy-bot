import re
import discord
from discord import Embed
from datetime import date, datetime, timedelta
from config import TIMEZONE, SHEET_URL, FAMILY_ROLE_ID, REPORT_TYPES, QUESTS

def parse_report_date(date_str=None):
    """
    Parse date string into dd.mm format
    Accepts formats: dd.mm, dd.mm., dd.mm.yyyy, dd.mm.yyyy.
    Returns None if date is invalid
    """
    now = datetime.now(TIMEZONE)

    if not date_str:
        return now.strftime("%d.%m.%Y")
        
    # Remove any trailing dots and whitespace
    date_str = date_str.strip().rstrip('.')
    
    # Match different date formats
    patterns = [
        r'^(\d{1,2})\.(\d{1,2})$',                  # dd.mm
        r'^(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})$'   # dd.mm.yy or dd.mm.yyyy
    ]
    
    for pattern in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                day = int(match.group(1))
                month = int(match.group(2))
                year = now.year

                # If year was provided
                if len(match.groups()) > 2:
                    year_str = match.group(3)
                    if len(year_str) == 2:
                        year = 2000 + int(year_str)
                    else:
                        year = int(year_str)
                
                # Validate date
                date_obj = datetime(year, month, day, tzinfo=TIMEZONE)
                
                # Don't allow future dates
                if date_obj > now:
                    return None
                    
                # Return in standard format
                return f"{day:02d}.{month:02d}.{year}"
                
            except ValueError:
                # Invalid day/month combination
                return None
                
    return None

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

def find_type(user_input: str, config_dict: dict) -> str | None:
    """
    Find the canonical type from user input in given config dictionary
    Args:
        user_input: User input string to search for
        config_dict: Dictionary to search in (REPORT_TYPES or QUESTS)
    Returns:
        str: Canonical type if found
        None: If no match found
    """
    if not user_input:
        return None
        
    user_input = user_input.lower().strip()
    
    # Direct match
    if user_input in config_dict:
        return user_input
        
    # Check aliases
    for type_key, config in config_dict.items():
        if "aliases" in config:
            if user_input in [alias.lower() for alias in config["aliases"]]:
                return type_key
                
    return None
