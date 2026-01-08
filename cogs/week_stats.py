import discord
from discord.ext import commands, tasks
from config import GUILD_ID, TIMEZONE, ANNOUNCEMENT_CHANNEL_ID, REQUIRED_WEEKLY_POINTS, ECONOMY_CHANEL_ID
from datetime import datetime, timedelta
import sys
import asyncio
from datetime import time, timezone

from utils.db_utils import Database
from utils.general_utils import send_week_summary, format_money
from utils.warns import send_warn_users_from_week_summary

BOT_START_TIME = datetime.now(TIMEZONE)

class WeekStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.finalize_weekly_stats_task.start()
        self.restart_bot.start()

    def cog_unload(self):
        try:
            self.finalize_weekly_stats_task.cancel()
        except Exception:
            pass
        try:
            self.restart_bot.cancel()
        except Exception:
            pass

    # @tasks.loop(hours=1)
    @tasks.loop(time=time(hour=0, minute=0, tzinfo=TIMEZONE))
    async def finalize_weekly_stats_task(self):
        now = datetime.now(TIMEZONE)
        print(f"Checking weekly stats at {now.isoformat()}")
        # виконуємо тільки у понеділок о 00:00–00:59
        # if now.weekday() == 0 and now.hour == 0:
        if now.weekday() == 0:
            guild = self.bot.get_guild(GUILD_ID)
            if guild:
                rewards_data, users, bonus_data = await self.db.finalize_weekly_stats(guild)
                channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
                if channel:
                    await send_week_summary(bot = self.bot, channel=channel, guild=guild, rewards_data=rewards_data, bonus_data=bonus_data)
                await send_warn_users_from_week_summary(guild, REQUIRED_WEEKLY_POINTS)

                vault_data = self.db.get_vault_data()
                economy_chanel = self.bot.get_channel(ECONOMY_CHANEL_ID)

                embed = discord.Embed(
                    title="💰 Економічний звіт тижня",
                    description=f"Цього тижня зароблено **{format_money(vault_data["week_income"])}$**",
                    color=discord.Color.gold(),
                    timestamp=discord.utils.utcnow()
                )

                embed.add_field(
                    name="🏦 У общак відправляється",
                    value=f"{format_money(bonus_data["week_profit"])}$",
                    inline=False
                )

                await economy_chanel.send(embed=embed)
                self.db.week_income_to_zero()
                self.db.update_vault_data(bonus_data["week_profit"], 0)

    @tasks.loop(time=time(hour=4, minute=0, tzinfo=TIMEZONE))
    async def restart_bot(self):
        now = datetime.now(TIMEZONE)
        # if 4 <= now.hour < 5:
        # uptime = datetime.now(TIMEZONE) - BOT_START_TIME
        uptime = now - BOT_START_TIME
        
            
        # Перезапуск тільки якщо бот працює більше 12 годин
        if uptime >= timedelta(hours=3):
            uptime_str = str(uptime).split('.')[0]  # Форматуємо без мілісекунд
            print(f"🔁 Плановий перезапуск бота")
            print(f"   Uptime: {uptime_str}")
            print(f"   Час: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Graceful shutdown
            await asyncio.sleep(3)
            await self.bot.close()
            sys.exit(0)  # PM2 автоматично перезапустить

    @finalize_weekly_stats_task.before_loop
    async def before_finalize_weekly_stats_task(self):
        await self.bot.wait_until_ready()
        print("✅ WeekStats task готовий до роботи")

    @restart_bot.before_loop
    async def before_restart_bot(self):
        await self.bot.wait_until_ready()
        print("✅ Restart task готовий до роботи")

async def setup(bot):
    await bot.add_cog(WeekStats(bot))