import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import os
from config import QUESTS, TIMEZONE, QUESTS_CHANNEL, FAMILY_ROLE_ID, QUESTS_CHANNEL_TAGS
from views.quest_view import QuestView, load_status, save_status
from utils.general_utils import find_type

class Quests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def formated_help_embed(self):
        embed = discord.Embed(
            title="📋 Доступні команди сімейних квестів",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🎯 Створення квесту",
            value=(
                "`!квест <квест> <час> <дата>` - створює заклик у форумі\n"
            ),
            inline=False
        )

        embed.add_field(
            name="Можливі варіанти квестів",
            value=(
                "Доступні квести та їх повні назви:\n" +
                "\n".join([f"• `{key}` - {quest['full_name']}" for key, quest in QUESTS.items()])
            ),
            inline=False
        )


        embed.add_field(
            name="📌 Перегляд статусу всіх квестів",
            value="`!квести` - показує, які квести доступні, заплановані, у КД або тривають.",
            inline=False
        )

        embed.set_footer(text="💡 Використовуйте ці команди, щоб керувати сімейними квестами та бачити їх статуси.\nℹ️ Формат часу: гг:хх, формат дати: дд.мм")

        return embed
    
    @commands.command(name="квест")
    # async def create_quest(self, ctx, quest_key: str = None, start_time: str = None, start_date: str = None):
    async def create_quest(self, ctx, *, args_str: str = None):
        """Створює новий квест-заклик у форумі."""

        if not args_str:
            embed = self.formated_help_embed()
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await msg.delete()
            await ctx.message.delete()
            return
        
        words = args_str.split()
        quest_key = None
        start_time = None
        start_date = None

        for i in range(len(words), 0, -1):
            quest_type = " ".join(words[:i])
            found_type = find_type(quest_type, QUESTS)
            if found_type:
                quest_key = found_type
                remaining_args = words[i:]
                if len(remaining_args) >= 2:
                    start_time = remaining_args[0]
                    start_date = remaining_args[1]
                break

        if not quest_key or quest_key not in QUESTS:
            embed = self.formated_help_embed()
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
        # if s:
        #     if s.get("status") == "cooldown":
        #         cd_end = datetime.fromisoformat(s["cooldown_end"])
        #         if now < cd_end:
        #             await ctx.send(f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!", delete_after=5)
        #             await ctx.message.delete()
        #             # return
        #         else:
        #             s["status"] = "available"
        #     elif s.get("status") == "started":
        #         end_time = datetime.fromisoformat(s["end_time"])
        #         if now < end_time:
        #             await ctx.send(f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!", delete_after=5)
        #             await ctx.message.delete()
        #             return
        #         else:
        #             cooldown_end = now + timedelta(hours=quest["cooldown_hours"])
        #             s.update({"status": "cooldown", "cooldown_end": cooldown_end.isoformat()})
        #     elif s.get("status") == "scheduled":
        #         thread_id = s.get("thread_id")
        #         if thread_id:
        #             await ctx.send(f"⚠️ Квест уже заплановано у форумі!", delete_after=5)
        #             await ctx.message.delete()
        #             return

        ####

        can_schedule = False

        # Спроба розпарсити вказану дату/час (формат: "дд.мм" та "гг:хх").
        requested_start = None
        if start_time and start_date:
            try:
                parsed = datetime.strptime(f"{start_date} {start_time}", "%d.%m %H:%M")
                requested_start = parsed.replace(year=now.year, tzinfo=TIMEZONE)
            except Exception:
                requested_start = None

        # Перевірка і оновлення статусу відносно запрошеної дати/часу (якщо вказана) або now
        if s:
            if s.get("status") == "cooldown":
                cd_end = datetime.fromisoformat(s["cooldown_end"])
                # Якщо користувач вказав час планування — порівнюємо з ним
                if requested_start:
                    if requested_start < cd_end:
                        await ctx.send(f"⏳ Квест на кулдауні до {cd_end.strftime('%H:%M %d.%m')}. Оберіть час після цієї дати.", delete_after=7)
                        await ctx.message.delete()
                        return
                    # якщо requested_start >= cd_end — дозволяємо планувати, але НЕ змінюємо cooldown_end
                    can_schedule = True
                else:
                    # без вказаної дати — поведінка як раніше: забороняємо якщо кулдаун ще триває
                    if now < cd_end:
                        await ctx.send(f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!", delete_after=5)
                        await ctx.message.delete()
                        return
                    else:
                        s["status"] = "available"
            elif s.get("status") == "started":
                end_time = datetime.fromisoformat(s["end_time"])
                # при плануванні враховуємо requested_start якщо є
                cmp_time = requested_start or now
                if cmp_time < end_time:
                    await ctx.send(f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!", delete_after=5)
                    await ctx.message.delete()
                    return
                else:
                    cooldown_end = cmp_time + timedelta(hours=quest["cooldown_hours"])
                    s.update({"status": "cooldown", "cooldown_end": cooldown_end.isoformat()})
            elif s.get("status") == "scheduled":
                thread_id = s.get("thread_id")
                if thread_id:
                    await ctx.send(f"⚠️ Квест уже заплановано у форумі!", delete_after=5)
                    await ctx.message.delete()
                    return

        ####

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

        # file = None
        # if quest["image"] and os.path.exists(quest["image"]):
        #     file = discord.File(quest["image"], filename="quest.png")
        #     embed.set_image(url="attachment://quest.png")

        if quest["image"]:
            embed.set_image(url=quest["image"])

        view = QuestView(quest_key, ctx.author.id)

        # if not s or s.get("status") == "available":
        if can_schedule or not s or s.get("status") == "available":
            # створюємо новий пост у форумі
            # if file:
            #     thread = await forum.create_thread(
            #         name=title,
            #         content=f"{ctx.guild.get_role(FAMILY_ROLE_ID).mention}",
            #         embed=embed,
            #         file=file,
            #         view=view
            #     )
            # else:
            #     thread = await forum.create_thread(
            #         name=title,
            #         content=f"{ctx.guild.get_role(FAMILY_ROLE_ID).mention}",
            #         embed=embed,
            #         view=view
            #     )
            recrut_tag_id = QUESTS_CHANNEL_TAGS["recrut"]
            recrut_tag = discord.utils.get(forum.available_tags, id=recrut_tag_id)

            thread = await forum.create_thread(
                name=title,
                content=f"{ctx.guild.get_role(FAMILY_ROLE_ID).mention}",
                embed=embed,
                view=view,
                applied_tags=[recrut_tag] if recrut_tag else None
            )
            
            thread_id = thread.thread.id
            s = s or {}
            # s.update({
            #     "status": "scheduled",
            #     "thread_id": thread_id,
            #     "start_time": None,
            #     "end_time": None,
            #     "cooldown_end": None,
            # })
            # Якщо ми дозволяємо планувати під час КД — залишаємо cooldown_end як є.
            s.update({
                "status": "scheduled",
                "thread_id": thread_id,
                "start_time": requested_start.isoformat() if requested_start else None,
                "end_time": None,
                # не чіпаємо "cooldown_end" щоб зберегти справжній КД
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

        msg = await ctx.send(embed=embed)
        await ctx.message.delete()
        await asyncio.sleep(120)
        await msg.delete()

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