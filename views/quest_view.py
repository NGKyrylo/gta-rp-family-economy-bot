import discord
from discord.ui import View, button
from datetime import datetime, timedelta
import json
import os
from config import QUESTS, TIMEZONE

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

    @button(label="✅ Почати", style=discord.ButtonStyle.success, custom_id="quest_start")
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        statuses = load_status()
        quest = QUESTS[self.quest_key]
        s = statuses.get(self.quest_key)
        now = datetime.now(TIMEZONE)

        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return

        # Оновлюємо статус по часу
        if s.get("status") == "cooldown":
            cd_end = datetime.fromisoformat(s["cooldown_end"])
            if now >= cd_end:
                s["status"] = "available"
            else:
                await interaction.response.send_message(f"⏳ Квест ще на кулдауні до {cd_end.strftime('%H:%M %d.%m')}!", ephemeral=True)
                return
        elif s.get("status") == "started":
            end_time = datetime.fromisoformat(s["end_time"])
            if now >= end_time:
                cd_end = now + timedelta(hours=quest["cooldown_hours"])
                s.update({"status": "cooldown", "cooldown_end": cd_end.isoformat()})
            else:
                await interaction.response.send_message(f"⚠️ Квест уже йде до {end_time.strftime('%H:%M %d.%m')}!", ephemeral=True)
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

        await self.update_embed(
            interaction,
            discord.Color.green(),
            f"Статус: 🟢 Розпочато | Завершення: {end_time.strftime('%H:%M %d.%m')}"
        )
        await interaction.response.send_message("🚀 Квест офіційно розпочато!", ephemeral=True)

    @button(label="🛑 Завершити", style=discord.ButtonStyle.danger, custom_id="quest_finish")
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
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

        for child in self.children:
            child.disabled = True

        await self.update_embed(
            interaction,
            discord.Color.red(),
            f"Статус: 🔴 Завершено | КД до {cooldown_end.strftime('%H:%M %d.%m')}"
        )
        await interaction.response.send_message("🏁 Квест завершено, пост закрито!", ephemeral=True)

        # Закриваємо thread у форумі, якщо можливо
        try:
            await interaction.channel.edit(archived=True, locked=False)
        except Exception:
            pass

    @button(label="❌ Скасувати", style=discord.ButtonStyle.grey, custom_id="quest_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        statuses = load_status()
        s = statuses.get(self.quest_key)

        if not s:
            await interaction.response.send_message("❌ Дані про цей квест не знайдено.", ephemeral=True)
            return

        if s.get("status") != "scheduled":
            await interaction.response.send_message("⚠️ Можна скасувати лише заплановані квести.", ephemeral=True)
            return


        # Скасовуємо квест
        s["status"] = "available"
        s.pop("start_time", None)
        s.pop("end_time", None)
        s.pop("cooldown_end", None)
        save_status(statuses)

        for child in self.children:
            child.disabled = True

        await self.update_embed(
            interaction,
            discord.Color.light_grey(),
            "Статус: ⚪ Скасовано"
        )

        try:
            await interaction.channel.edit(archived=True, locked=False)
        except Exception:
            pass
        
        await interaction.response.send_message("❌ Квест скасовано, пост закрито!", ephemeral=True)
