import discord
from utils.check_utils import is_discipline_controller
from config import FIRST_WARN_ROLE, SECOND_WARN_ROLE, THIRD_WARN_ROLE

class WarnRemovalView(discord.ui.View):
    # def __init__(self, member: discord.Member, warn_roles: list[discord.Role], thread: discord.Thread):
    #     super().__init__(timeout=None)
    #     self.member = member
    #     self.warn_roles = warn_roles
    #     self.thread = thread
    def __init__(self):
        super().__init__(timeout=None)

    async def remove_warns(self, amount: int, interaction: discord.Interaction):
        """Основна логіка кнопок"""

        # 🔒 Перевірка доступу
        if not is_discipline_controller(interaction.user):
            await interaction.response.send_message(
                "⛔ У вас немає прав контролю дисципліни.", ephemeral=True
            )
            return
        
        # отримуємо ID користувача з теми (у форумі)
        thread = interaction.channel
        if not isinstance(thread, discord.Thread):
            return await interaction.response.send_message("❌ Цю кнопку можна натискати тільки в темі WARN.", ephemeral=True)

        # припускаємо, що у назві або в першому повідомленні є mention користувача
        thread = interaction.channel  # це тред
        first_message = await anext(thread.history(limit=1, oldest_first=True))
        mentioned_user = first_message.mentions[0] if first_message.mentions else None

        if not mentioned_user:
            return await interaction.response.send_message("❌ Не вдалося визначити користувача.", ephemeral=True)

        # Знаходимо ролі для видалення
        guild = interaction.guild
        warn_roles_ids = [FIRST_WARN_ROLE, SECOND_WARN_ROLE, THIRD_WARN_ROLE]
        warn_roles = [guild.get_role(rid) for rid in warn_roles_ids]

        roles_to_remove = [r for r in reversed(warn_roles) if r in mentioned_user.roles][:amount]
        if not roles_to_remove:
            await interaction.response.send_message(
                f"⚠️ У {mentioned_user.mention} немає активних варнів.", ephemeral=True
            )
            return

        # Видаляємо ролі
        await mentioned_user.remove_roles(*roles_to_remove, reason=f"Варни зняв {interaction.user}")

        # Відповідь
        await interaction.response.send_message(
            f"✅ {interaction.user.mention} зняв {len(roles_to_remove)} варн(и) у {mentioned_user.mention}.",
            ephemeral=False
        )

        # Вимикаємо всі кнопки
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)

        # Закриваємо тред
        try:
            await interaction.channel.edit(archived=True, locked=True)
        except Exception:
            pass

    # Сірі кнопки (secondary)
    @discord.ui.button(label="Зняти 1 варн", style=discord.ButtonStyle.secondary, custom_id="remove_1_warn")
    async def remove_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_warns(1, interaction)

    @discord.ui.button(label="Зняти 2 варни", style=discord.ButtonStyle.secondary, custom_id="remove_2_warn")
    async def remove_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_warns(2, interaction)

    @discord.ui.button(label="Зняти 3 варни", style=discord.ButtonStyle.secondary, custom_id="remove_3_warn")
    async def remove_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.remove_warns(3, interaction)

    @discord.ui.button(label="Закрити", style=discord.ButtonStyle.grey, custom_id="close_warn_thread")
    async def close_thread(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Закриває тред без зняття варнів"""
        # 🔒 Перевірка доступу
        if not is_discipline_controller(interaction.user):
            await interaction.response.send_message(
                "⛔ У вас немає прав контролю дисципліни.", ephemeral=True
            )
            return

        # Вимикаємо всі кнопки
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)

        # Відповідь
        await interaction.response.send_message("✅ Тред закрито без зняття варнів.", ephemeral=False)

        # Закриваємо тред
        try:
            await interaction.channel.edit(archived=True, locked=True)
        except Exception:
            pass
