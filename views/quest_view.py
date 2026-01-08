# import discord
# from discord.ui import View, button
# from datetime import datetime, timedelta
# import json
# import os
# from config import QUESTS, TIMEZONE

# STATUS_FILE = "data/quests_status.json"

# def load_status():
#     if os.path.exists(STATUS_FILE):
#         with open(STATUS_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return {}

# def save_status(data):
#     os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
#     with open(STATUS_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)

# class QuestView(View):
#     def __init__(self, quest_key, author_id):
#         super().__init__(timeout=None)  # persistent
#         self.quest_key = quest_key
#         self.author_id = author_id

#     async def update_embed(self, interaction, color, footer):
#         embed = interaction.message.embeds[0]
#         embed.color = color
#         embed.set_footer(text=footer)
#         await interaction.message.edit(embed=embed, view=self)

#     @button(label="✅ Почати", style=discord.ButtonStyle.success, custom_id="quest_start")
#     async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
#         statuses = load_status()
#         quest = QUESTS[self.quest_key]
#         s = statuses.get(self.quest_key)
#         now = datetime.now(TIMEZONE)

#         if not s:
#             await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
#             return

#         # Оновлюємо статус по часу
#         if s.get("status") == "cooldown":
#             cd_end = datetime.fromisoformat(s["cooldown_end"])
#             if now >= cd_end:
#                 s["status"] = "available"
#             else:
#                 await interaction.response.send_message(f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!", ephemeral=True)
#                 return
#         elif s.get("status") == "started":
#             end_time = datetime.fromisoformat(s["end_time"])
#             if now >= end_time:
#                 cd_end = now + timedelta(hours=quest["cooldown_hours"])
#                 s.update({"status": "cooldown", "cooldown_end": cd_end.isoformat()})
#             else:
#                 await interaction.response.send_message(f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!", ephemeral=True)
#                 return

#         # Запускаємо квест
#         start_time = now
#         end_time = start_time + timedelta(hours=quest["duration_hours"])
#         s.update({
#             "status": "started",
#             "start_time": start_time.isoformat(),
#             "end_time": end_time.isoformat(),
#         })
#         save_status(statuses)

#         await self.update_embed(
#             interaction,
#             discord.Color.green(),
#             f"Статус: 🟢 Розпочато | Завершення: {end_time.strftime('%H:%M %d.%m')}"
#         )
#         await interaction.response.send_message("🚀 Квест офіційно розпочато!", ephemeral=True)

#     @button(label="🛑 Завершити", style=discord.ButtonStyle.danger, custom_id="quest_finish")
#     async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
#         statuses = load_status()
#         quest = QUESTS[self.quest_key]
#         s = statuses.get(self.quest_key)
#         now = datetime.now(TIMEZONE)

#         if not s or s.get("status") != "started":
#             await interaction.response.send_message("⚠️ Квест не активний.", ephemeral=True)
#             return

#         # Завершуємо квест і ставимо cooldown
#         cooldown_end = now + timedelta(hours=quest["cooldown_hours"])
#         s.update({
#             "status": "cooldown",
#             "cooldown_end": cooldown_end.isoformat(),
#         })
#         save_status(statuses)

#         for child in self.children:
#             child.disabled = True

#         await self.update_embed(
#             interaction,
#             discord.Color.red(),
#             f"Статус: 🔴 Завершено | КД до {cooldown_end.strftime('%H:%M %d.%m')}"
#         )
#         await interaction.response.send_message("🏁 Квест завершено, пост закрито!", ephemeral=True)

#         # Закриваємо thread у форумі, якщо можливо
#         try:
#             await interaction.channel.edit(archived=True, locked=False)
#         except Exception:
#             pass

#     @button(label="❌ Скасувати", style=discord.ButtonStyle.grey, custom_id="quest_cancel")
#     async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
#         statuses = load_status()
#         s = statuses.get(self.quest_key)

#         if not s:
#             await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
#             return

#         if s.get("status") != "scheduled":
#             await interaction.response.send_message("⚠️ Можна скасувати лише заплановані квести.", ephemeral=True)
#             return


#         # Скасовуємо квест
#         # s["status"] = "available"
#         # s.pop("start_time", None)
#         # s.pop("end_time", None)
#         # s.pop("cooldown_end", None)
#         # save_status(statuses)

#         # Скасовуємо квест, але якщо існує активний кулдаун — залишаємо його в записі.
#         now = datetime.now(TIMEZONE)
#         cooldown_iso = s.get("cooldown_end")
#         keep_cd = False
#         if cooldown_iso:
#             try:
#                 cd_end = datetime.fromisoformat(cooldown_iso)
#                 if cd_end > now:
#                     keep_cd = True
#             except Exception:
#                 keep_cd = False

#         # Видаляємо часові поля, залишаємо або призначаємо статус залежно від кулдауну
#         s.pop("start_time", None)
#         s.pop("end_time", None)
#         if keep_cd:
#             s["status"] = "cooldown"
#             # cooldown_end залишається як є
#         else:
#             s["status"] = "available"
#             s.pop("cooldown_end", None)
#         save_status(statuses)

#         for child in self.children:
#             child.disabled = True

#         await self.update_embed(
#             interaction,
#             discord.Color.light_grey(),
#             "Статус: ⚪ Скасовано"
#         )

#         await interaction.response.send_message("❌ Квест скасовано, пост закрито!", ephemeral=True)

#         try:
#             await interaction.channel.edit(archived=True, locked=False)
#         except Exception:
#             pass





import discord
from discord.ui import View, button
from datetime import datetime, timedelta
import json
import os
from config import QUESTS, TIMEZONE, QUESTS_CHANNEL_TAGS

STATUS_FILE = "data/quests_status.json"

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_status(data):
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


class ConfirmView(View):
    """View з кнопками підтвердження"""
    def __init__(self, callback_confirm, callback_cancel=None, timeout=60):
        super().__init__(timeout=timeout)
        self.callback_confirm = callback_confirm
        self.callback_cancel = callback_cancel
    
    @button(label="✅ Так", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Вимикаємо кнопки
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        
        # await interaction.response.edit_message(content="...", view=None)

        # Виконуємо callback
        await self.callback_confirm(interaction)
    
    @button(label="❌ Ні", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Вимикаємо кнопки
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        # await interaction.response.edit_message(content="...", view=None)
        
        # Виконуємо callback скасування або стандартну відповідь
        if self.callback_cancel:
            await self.callback_cancel(interaction)
        else:
            await interaction.followup.send("❌ Дію скасовано.", ephemeral=True)


class QuestView(View):
    def __init__(self, quest_key, author_id):
        super().__init__(timeout=None)  # persistent
        self.quest_key = quest_key
        self.author_id = author_id

    async def update_embed(self, interaction, color, footer):
        embed = interaction.message.embeds[0]
        embed.color = color
        embed.set_footer(text=footer)
        await interaction.message.edit(embed=embed, view=self)
    
    async def apply_tag(self, interaction: discord.Interaction, tag_key: str):
        """Змінює тег треду на вказаний"""

        forum = interaction.channel.parent
        if not isinstance(forum, discord.ForumChannel):
            return

        tag_id = QUESTS_CHANNEL_TAGS.get(tag_key)
        if not tag_id:
            return

        tag = discord.utils.get(forum.available_tags, id=tag_id)
        if not tag:
            return

        try:
            await interaction.channel.edit(applied_tags=[tag])
        except Exception as e:
            print(f"Помилка застосування тегу {tag_key}: {e}")

    @button(label="✅ Почати", style=discord.ButtonStyle.success, custom_id="quest_start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        quest = QUESTS.get(self.quest_key)
        if not quest:
            await interaction.response.send_message("❌ Квест не знайдено.", ephemeral=True)
            return
        
        # Перевіряємо статус перед показом підтвердження
        statuses = load_status()
        s = statuses.get(self.quest_key)
        now = datetime.now(TIMEZONE)
        
        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return
        
        # Перевірка кулдауну
        if s.get("status") == "cooldown":
            cd_end = datetime.fromisoformat(s["cooldown_end"])
            if now >= cd_end:
                s["status"] = "available"
            else:
                await interaction.response.send_message(
                    f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!",
                    ephemeral=True
                )
                return
        
        # Перевірка чи вже стартував
        if s.get("status") == "started":
            end_time = datetime.fromisoformat(s["end_time"])
            if now < end_time:
                await interaction.response.send_message(
                    f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!",
                    ephemeral=True
                )
                return
        
        # Показуємо підтвердження
        view = ConfirmView(callback_confirm=self._execute_start)

        embed = discord.Embed(
            title="⚠️ Підтвердження запуску",
            description=(
                f"Ви впевнені що хочете **розпочати** квест:\n"
                f"**📜 {quest['full_name']}**\n\n"
                f"⏰ Тривалість: **{quest['duration_hours']} год**\n"
                f"🔄 Кулдаун після завершення: **{quest['cooldown_hours']} год**"
            ),
            color=0xF1C40F
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

    async def _execute_start(self, interaction: discord.Interaction):
        """Фактичний запуск квесту після підтвердження"""
        statuses = load_status()
        quest = QUESTS[self.quest_key]
        s = statuses.get(self.quest_key)
        now = datetime.now(TIMEZONE)

        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return

        # Запускаємо квест
        start_time = now
        end_time = start_time + timedelta(hours=quest["duration_hours"])
        s.update({
            "status": "started",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        })
        save_status(statuses)
        await self.apply_tag(interaction, "in-progress")

        # Оновлюємо embed в оригінальному повідомленні
        # Знаходимо оригінальне повідомлення через channel
        try:
            # Шукаємо повідомлення з QuestView
            async for message in interaction.channel.history(limit=50):
                if message.embeds and any(view for view in message.components if isinstance(view, discord.ActionRow)):
                    embed = message.embeds[0]
                    embed.color = discord.Color.green()
                    embed.set_footer(text=f"Статус: 🟢 Розпочато | Завершення: {end_time.strftime('%H:%M %d.%m')}")
                    await message.edit(embed=embed, view=self)
                    break
        except Exception as e:
            print(f"Помилка оновлення embed: {e}")
        
        embed = discord.Embed(
            title=f"🚀 Квест '{quest['full_name']}' офіційно розпочато!",
            description=f"⏰ Завершення: **{end_time.strftime('%H:%M %d.%m')}**",
            color=0x2ECC71
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=False
        )

    @button(label="🛑 Завершити", style=discord.ButtonStyle.danger, custom_id="quest_finish")
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        quest = QUESTS.get(self.quest_key)
        if not quest:
            await interaction.response.send_message("❌ Квест не знайдено.", ephemeral=True)
            return
        
        # Перевіряємо статус
        statuses = load_status()
        s = statuses.get(self.quest_key)
        
        if not s or s.get("status") != "started":
            await interaction.response.send_message("⚠️ Квест не активний.", ephemeral=True)
            return
        
        # Показуємо підтвердження
        view = ConfirmView(callback_confirm=self._execute_finish)

        embed = discord.Embed(
            title="⚠️ Підтвердження завершення",
            description=(
                f"Ви впевнені що хочете **завершити** квест:\n"
                f"**📜 {quest['full_name']}**\n\n"
                f"🔄 Після завершення буде кулдаун **{quest['cooldown_hours']} год**\n"
                f"📋 Пост буде закрито і заархівовано"
            ),
            color=0xE67E22
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

    async def _execute_finish(self, interaction: discord.Interaction):
        """Фактичне завершення квесту після підтвердження"""
        statuses = load_status()
        quest = QUESTS[self.quest_key]
        s = statuses.get(self.quest_key)
        now = datetime.now(TIMEZONE)

        if not s or s.get("status") != "started":
            await interaction.response.send_message("⚠️ Квест не активний.", ephemeral=True)
            return

        # Завершуємо квест і ставимо cooldown
        cooldown_end = now + timedelta(hours=quest["cooldown_hours"])
        s.update({
            "status": "cooldown",
            "cooldown_end": cooldown_end.isoformat(),
        })
        save_status(statuses)
        await self.apply_tag(interaction, "ended")

        # Вимикаємо всі кнопки
        for child in self.children:
            child.disabled = True

        # Оновлюємо embed
        try:
            async for message in interaction.channel.history(limit=50):
                if message.embeds and any(view for view in message.components if isinstance(view, discord.ActionRow)):
                    embed = message.embeds[0]
                    embed.color = discord.Color.red()
                    embed.set_footer(text=f"Статус: 🔴 Завершено | КД до {cooldown_end.strftime('%H:%M %d.%m')}")
                    await message.edit(embed=embed, view=self)
                    break
        except Exception as e:
            print(f"Помилка оновлення embed: {e}")

        embed = discord.Embed(
            title=f"🏁 Квест '{quest['full_name']}' завершено!",
            description=(
                f"⏳ Кулдаун до: **{cooldown_end.strftime('%H:%M %d.%m')}**\n"
                f"📋 Пост закрито."
            ),
            color=0x3498DB
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=False
        )

        # Закриваємо thread у форумі
        try:
            await interaction.channel.edit(archived=True, locked=False)
        except Exception:
            pass

    @button(label="❌ Скасувати", style=discord.ButtonStyle.grey, custom_id="quest_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        quest = QUESTS.get(self.quest_key)
        if not quest:
            await interaction.response.send_message("❌ Квест не знайдено.", ephemeral=True)
            return
        
        # Перевіряємо статус
        statuses = load_status()
        s = statuses.get(self.quest_key)
        
        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return

        if s.get("status") != "scheduled":
            await interaction.response.send_message(
                "⚠️ Можна скасувати лише заплановані квести.",
                ephemeral=True
            )
            return
        
        # Показуємо підтвердження
        view = ConfirmView(callback_confirm=self._execute_cancel)

        embed = discord.Embed(
            title="⚠️ Підтвердження скасування",
            description=(
                f"Ви впевнені що хочете **скасувати набір** на квест:\n"
                f"**📜 {quest['full_name']}**\n\n"
                f"📋 Пост буде закрито і заархівовано\n"
            ),
            color=0xC0392B
        )
        
        await interaction.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

    async def _execute_cancel(self, interaction: discord.Interaction):
        """Фактичне скасування квесту після підтвердження"""
        statuses = load_status()
        s = statuses.get(self.quest_key)

        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return

        # Скасовуємо квест, але якщо існує активний кулдаун — залишаємо його
        now = datetime.now(TIMEZONE)
        cooldown_iso = s.get("cooldown_end")
        keep_cd = False
        if cooldown_iso:
            try:
                cd_end = datetime.fromisoformat(cooldown_iso)
                if cd_end > now:
                    keep_cd = True
            except Exception:
                keep_cd = False

        # Видаляємо часові поля
        s.pop("start_time", None)
        s.pop("end_time", None)
        if keep_cd:
            s["status"] = "cooldown"
        else:
            s["status"] = "available"
            s.pop("cooldown_end", None)
        save_status(statuses)
        await self.apply_tag(interaction, "recrut-canceled")

        # Вимикаємо всі кнопки
        for child in self.children:
            child.disabled = True

        # Оновлюємо embed
        try:
            async for message in interaction.channel.history(limit=50):
                if message.embeds and any(view for view in message.components if isinstance(view, discord.ActionRow)):
                    embed = message.embeds[0]
                    embed.color = discord.Color.light_grey()
                    embed.set_footer(text="Статус: ⚪ Скасовано")
                    await message.edit(embed=embed, view=self)
                    break
        except Exception as e:
            print(f"Помилка оновлення embed: {e}")

        quest = QUESTS.get(self.quest_key)

        embed = discord.Embed(
            title=f"❌ Набір на квест '{quest['full_name']}' скасовано!",
            description="📋 Пост закрито.",
            color=0xE74C3C
        )
                
        await interaction.followup.send(
            embed=embed,
            ephemeral=False
        )

        # Закриваємо thread
        try:
            await interaction.channel.edit(archived=True, locked=False)
        except Exception:
            pass