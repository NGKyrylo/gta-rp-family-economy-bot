import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import discord
from discord.ext import commands
from config import DISCORD_TOKEN, GUILD_ID, COMMAND_PREFIX, REPORT_CHANNELS, ADMIN_ROLE_ID, REPORT_TYPES

from discord.ui import Button, View

from datetime import datetime
import asyncio
from views.report_views import ConfirmReportView
from views.quest_view import QuestView, load_status


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Увійшов як {bot.user}")

    bot.add_view(ConfirmReportView(admin_role_id=ADMIN_ROLE_ID))

    statuses = load_status()
    for quest_key, status in statuses.items():
        if status.get("status") in ["started", "scheduled"]:
            bot.add_view(QuestView(quest_key, author_id=None))

    await bot.load_extension("cogs.reports")
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.statistics")
    await bot.load_extension("cogs.week_stats")
    await bot.load_extension("cogs.quests")

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send("🏓 Pong!")

bot.run(DISCORD_TOKEN)