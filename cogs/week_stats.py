import discord
from discord.ext import commands, tasks
from config import GUILD_ID, TIMEZONE, ANNOUNCEMENT_CHANNEL_ID, REQUIRED_WEEKLY_POINTS
from datetime import datetime

from utils.db_utils import Database
from utils.general_utils import send_week_summary
from utils.warns import issue_warns_from_week_summary

class WeekStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.finalize_weekly_stats_task.start()

    def cog_unload(self):
        self.finalize_weekly_stats_task.cancel()

    @tasks.loop(hours=1)
    async def finalize_weekly_stats_task(self):
        now = datetime.now(TIMEZONE)
        print(f"Checking weekly stats at {now.isoformat()}")
        # виконуємо тільки у понеділок о 00:00–00:59
        if now.weekday() == 0 and now.hour == 0:
            guild = self.bot.get_guild(GUILD_ID)
            if guild:
                rewards_data, users = self.db.finalize_weekly_stats(guild)
                channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
                if channel:
                    await send_week_summary(channel, guild, rewards_data)
                await issue_warns_from_week_summary(guild, REQUIRED_WEEKLY_POINTS)

async def setup(bot):
    await bot.add_cog(WeekStats(bot))