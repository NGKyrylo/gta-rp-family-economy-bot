import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import os
from config import QUESTS, TIMEZONE, QUESTS_CHANNEL, FAMILY_ROLE_ID
from views.quest_view import QuestView, load_status, save_status

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="квест")
    async def create_quest(self, ctx, quest_key: str = None, start_time: str = None, start_date: str = None):
        """Створює новий квест-заклик у форумі."""
        if not quest_key or quest_key not in QUESTS:
            embed = discord.Embed(
                title="📋 Доступні команди сімейних квестів",
                color=discord.Color.gold()
            )

            embed.add_field(
                name="🎯 Створення квесту",
                value=(
                    "`!квест <допомога/товарка/суботник/рибалка> <час> <дата>` - створює заклик у форумі\n"
                ),
                inline=False
            )

            embed.add_field(
                name="📌 Перегляд статусу всіх квестів",
                value="`!квести` - показує, які квести доступні, заплановані, у КД або тривають.",
                inline=False
            )

            embed.set_footer(text="💡 Використовуйте ці команди, щоб керувати сімейними квестами та бачити їх статуси.\nℹ️ Формат часу: гг:хх, формат дати: дд.мм")
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await msg.delete()
            await ctx.message.delete()
            return
    
        quest = QUESTS.get(quest_key)
        if not quest:
            msg = await ctx.send("❌ Невідомий квест. Доступні: " + ", ".join(QUESTS.keys()))
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()
            return

        statuses = load_status()
        s = statuses.get(quest_key)
        now = datetime.now(TIMEZONE)

        # Перевірка і оновлення статусу по реальному часу
        if s:
            if s.get("status") == "cooldown":
                cd_end = datetime.fromisoformat(s["cooldown_end"])
                if now < cd_end:
                    await ctx.send(f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!", delete_after=5)
                    await ctx.message.delete()
                    # return
                else:
                    s["status"] = "available"
            elif s.get("status") == "started":
                end_time = datetime.fromisoformat(s["end_time"])
                if now < end_time:
                    await ctx.send(f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!", delete_after=5)
                    await ctx.message.delete()
                    return
                else:
                    cooldown_end = now + timedelta(hours=quest["cooldown_hours"])
                    s.update({"status": "cooldown", "cooldown_end": cooldown_end.isoformat()})
            elif s.get("status") == "scheduled":
                thread_id = s.get("thread_id")
                if thread_id:
                    await ctx.send(f"⚠️ Квест уже заплановано у форумі!", delete_after=5)
                    await ctx.message.delete()
                    return

        # Якщо вже scheduled, просто беремо thread_id, не створюємо новий пост
        guild = ctx.guild
        forum = guild.get_channel(QUESTS_CHANNEL)
        if not forum or not isinstance(forum, discord.ForumChannel):
            msg = await ctx.send("❌ Канал для квестів не знайдено або він не є форумом.", delete_after=5)
            await ctx.message.delete()
            return

        title = f"{quest['full_name']} {start_time} / {start_date}"
        embed = discord.Embed(
            # title=ctx.guild.get_role(FAMILY_ROLE_ID).mention,
            description=quest["description"],
            color=discord.Color.orange()
        )
        embed.set_footer(text="Статус: 🔵 Заплановано")

        embed.set_image(url=quest["image"])

        view = QuestView(quest_key, ctx.author.id)

        if not s or s.get("status") == "available":
            thread = await forum.create_thread(
                name=title,
                content=f"{ctx.guild.get_role(FAMILY_ROLE_ID).mention}",
                embed=embed,
                view=view
            )
            
            thread_id = thread.thread.id
            s = s or {}
            s.update({
                "status": "scheduled",
                "thread_id": thread_id,
                "start_time": None,
                "end_time": None,
                "cooldown_end": None,
            })
            statuses[quest_key] = s
            save_status(statuses)

            msg = await ctx.send(f"✅ Квест **{quest['full_name']}** створено у форумі {forum.mention}", delete_after=5)
            await ctx.message.delete()

    @commands.command(name="квести")
    async def list_quests(self, ctx):
        """Показує поточний статус усіх квестів красиво оформленими рядками."""
        statuses = load_status()
        now = datetime.now(TIMEZONE)
        lines = []

        # Визначимо emoji для статусів
        STATUS_EMOJI = {
            "available": "🟢",
            "started": "🟡",
            "scheduled": "🔵",
            "cooldown": "🔴"
        }

        embed = discord.Embed(
            title="📋 Статус сімейних квестів",
            description="\n".join(lines),
            color=discord.Color.gold()
        )

        for key, quest in QUESTS.items():
            status = statuses.get(key)
            if not status:
                # Якщо запису немає, створюємо новий
                status = {
                    "thread_id": None,
                    "start_time": None,
                    "end_time": None,
                    "cooldown_end": None,
                    "created_at": now.isoformat(),
                    "status": "available"
                }
                statuses[key] = status
                save_status(statuses)

            # Визначаємо поточний статус та кольоровий emoji
            emoji = STATUS_EMOJI.get(status["status"], "⚪")
            status_text = ""
            
            if status["status"] == "started":
                end = datetime.fromisoformat(status["end_time"])
                status_text = f"триває (до {end.strftime('%H:%M')})"
            elif status["status"] == "scheduled":
                status_text = "заплановано"
            elif status["status"] == "cooldown":
                cd_end = datetime.fromisoformat(status["cooldown_end"])
                if cd_end > now:
                    status_text = f"у КД до {cd_end.strftime('%H:%M %d.%m')}"
                else:
                    # КД вже минув, робимо доступним
                    status_text = "доступний!"
                    status["status"] = "available"
                    save_status(statuses)
                    emoji = STATUS_EMOJI["available"]
            elif status["status"] == "available":
                status_text = "доступний!"

            # Формуємо гарну рядкову картку з вирівнюванням
            embed.add_field(
                name=f"**{quest['full_name']}**",
                value=f"`{emoji}` {status_text}",
                inline=False
            )

        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name="скинути_квест")
    async def reset_quest(self, ctx, quest_key: str):
        """⚠️ Використовувати тільки у критичних випадках"""
        statuses = load_status()
        s = statuses.get(quest_key)
        if not s:
            await ctx.send(f"❌ Квест {quest_key} не знайдено.", ephemeral=True)
            return

        s["status"] = "available"
        s.pop("start_time", None)
        s.pop("end_time", None)
        s.pop("cooldown_end", None)
        save_status(statuses)
        msg = await ctx.send(f"✅ Квест {quest_key} переведено у доступний статус.", ephemeral=True)
        await ctx.message.delete()
        await asyncio.sleep(5)
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Quests(bot))