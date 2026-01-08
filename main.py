import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
from config import DISCORD_TOKEN, GUILD_ID, COMMAND_PREFIX, REPORT_CHANNELS, ADMIN_ROLE_ID, REPORT_TYPES

from discord.ui import Button, View

from datetime import datetime
import asyncio
from views.report_views import ConfirmReportView
from views.quest_view import QuestView, load_status
from views.warn_removal_view import WarnRemovalView
from views.debt_view import DebtView


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Увійшов як {bot.user}")

    bot.add_view(ConfirmReportView(admin_role_id=ADMIN_ROLE_ID))
    bot.add_view(WarnRemovalView())

    statuses = load_status()
    for quest_key, status in statuses.items():
        if status.get("status") in ["started", "scheduled"]:
            bot.add_view(QuestView(quest_key, author_id=None))

    bot.add_view(DebtView())

    # await bot.load_extension("cogs.reports")
    # await bot.load_extension("cogs.admin")
    # await bot.load_extension("cogs.statistics")
    # await bot.load_extension("cogs.week_stats")
    # await bot.load_extension("cogs.quests")
    # await bot.load_extension("cogs.cash")

    # await bot.load_extension("events.member_events")

    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)

    await bot.tree.sync()

@bot.command(name="ping")
async def ping_cmd(ctx):
    await ctx.send("🏓 Pong!")

# bot.run(DISCORD_TOKEN)

async def setup_bot():
    await bot.load_extension("cogs.reports")
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.statistics")
    await bot.load_extension("cogs.week_stats")
    await bot.load_extension("cogs.quests")
    await bot.load_extension("cogs.cash")
    await bot.load_extension("events.member_events")
    await bot.load_extension("cogs.debt")

async def main():
    async with bot:
        await setup_bot()
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())