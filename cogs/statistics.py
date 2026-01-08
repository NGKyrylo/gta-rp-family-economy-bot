import asyncio
import discord
from discord.ext import commands
from discord.ui import View, button
from datetime import datetime
from config import TIMEZONE
from utils.db_utils import Database


class StatsView(View):
    def __init__(self, db, user_id, member):
        super().__init__(timeout=120)
        self.db = db
        self.user_id = user_id
        self.member = member

    async def update_embed(self, interaction: discord.Interaction, week_key: str, week_name: str):
        """Оновлює вміст ембеду, не створюючи нових повідомлень"""
        data = self.db.get_user(self.user_id)
        if not data:
            await interaction.response.send_message("❌ Дані не знайдено.", ephemeral=True)
            return

        week_data = data.get(week_key, {})
        week_text = "\n".join(
            f"{day}: {points}" for day, points in week_data.items()
        ) or "Немає даних"

        # Форматуємо дату приєднання
        join_date = data.get("join_date")
        if join_date:
            try:
                join_dt = datetime.fromisoformat(join_date).astimezone(TIMEZONE)
                join_date = join_dt.strftime("%d.%m.%Y")
            except Exception:
                join_date = "невідомо"
        else:
            join_date = "невідомо"

        # Створюємо embed
        embed = discord.Embed(
            title=f"📊 Статистика {self.member.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        embed.add_field(name="🏆 Загальні поінти", value=f"```{data['total_points']}```", inline=True)
        embed.add_field(name="📅 Поінтів за тиждень", value=f"```{data['weekly_points']}```", inline=True)
        embed.add_field(name=f"{'📅' if week_key == 'this_week' else '📆'} {week_name}",
                        value=f"```{week_text}```",
                        inline=False)
        embed.add_field(name="📆 Дата приєднання", value=join_date, inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Цей тиждень", style=discord.ButtonStyle.green)
    async def this_week(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "this_week", "Статистика цього тижня")

    @button(label="Минулого тижня", style=discord.ButtonStyle.blurple)
    async def last_week(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "last_week", "Статистика минулого тижня")


class Statistics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name="статистика")
    async def statistics(self, ctx, member: discord.Member = None):
        """Команда для перегляду власної або чужої статистики"""
        member = member or ctx.author
        user_id = str(member.id)
        user_data = self.db.get_user(user_id)

        if not user_data:
            await ctx.send("❌ Дані користувача не знайдено.")
            return

        # Форматуємо дату
        join_date = user_data.get("join_date")
        if join_date:
            try:
                join_dt = datetime.fromisoformat(join_date).astimezone(TIMEZONE)
                join_date = join_dt.strftime("%d.%m.%Y")
            except Exception:
                join_date = "невідомо"
        else:
            join_date = "невідомо"

        # Базовий Embed (стартова — цей тиждень)
        this_week = user_data.get("this_week", {})
        week_text = "\n".join(f"{d}: {v}" for d, v in this_week.items()) or "Немає даних"

        embed = discord.Embed(
            title=f"📊 Статистика {member.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🏆 Загальні поінти", value=f"```{user_data['total_points']}```", inline=True)
        embed.add_field(name="📅 Поінтів за тиждень", value=f"```{user_data['weekly_points']}```", inline=True)
        embed.add_field(name="📅 Статистика цього тижня", value=f"```{week_text}```", inline=False)
        embed.add_field(name="📆 Дата приєднання", value=join_date, inline=False)

        view = StatsView(self.db, user_id, member)
        msg = await ctx.send(embed=embed, view=view)
        await ctx.message.delete()
        await asyncio.sleep(120)
        await msg.delete()


async def setup(bot):
    await bot.add_cog(Statistics(bot))