import discord
from discord.ui import View, button
from config import DEBT_LOG_CHANNEL_ID
from utils.check_utils import is_recruiter, is_economy_controller, is_admin, is_bot_developer

class DebtView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.checks = [
            is_recruiter,
            is_economy_controller,
            is_admin,
            is_bot_developer
        ]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Якщо хоча б одна перевірка пройшла → дозволено
        for check in self.checks:
            if check(interaction.user):
                return True

        # Якщо жодна не пройшла
        await interaction.response.send_message(
            "⛔ У вас немає прав використовувати цю дію.",
            ephemeral=True
        )
        return False

    @discord.ui.button(label="Виплачено", style=discord.ButtonStyle.success, emoji="✅", custom_id="debt_paid_button")
    async def paid(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(DEBT_LOG_CHANNEL_ID)

        # Копіюємо embed
        original_embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if original_embed and log_channel:
            embed_copy = original_embed.copy()
            embed_copy.set_footer(
                text=f"{original_embed.footer.text or ''} • Виплатив: {interaction.user.display_name}"
            )
            await log_channel.send(embed=embed_copy)

        await interaction.message.delete()