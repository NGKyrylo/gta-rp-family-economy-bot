import discord
from discord.ui import View
from utils.db_utils import Database
from datetime import datetime

from utils.check_utils import is_economy_controller

from config import REPORT_TYPES
from config import TIMEZONE

class ConfirmReportView(View):
    def __init__(self, admin_role_id):
        super().__init__(timeout=None)
        self.admin_role_id = admin_role_id
        self.db = Database()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_economy_controller(interaction.user):
            await interaction.response.send_message(
                "⛔ У вас немає прав використовувати цю дію.",
                ephemeral=True
            )
            return False

        return True


    @discord.ui.button(
        label="✅ Підтвердити",
        style=discord.ButtonStyle.green,
        custom_id="report_confirm"
    )
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        report_data = self.db.get_report(interaction.message.id)

        if not report_data:
            await interaction.response.send_message(
                "❌ Помилка: дані звіту не знайдено",
                ephemeral=True
            )
            return
        
        if report_data:
            # self.db.add_points(
            #     report_data["user_id"],
            #     report_data["points"],
            #     REPORT_TYPES.get(report_data["type"], {}).get("is_family_quest", False)
            # )
            # # report_date = datetime.fromisoformat(report_data["report_date"])
            report_date = datetime.strptime(report_data["report_date"], "%d.%m.%Y")
            report_date = report_date.replace(tzinfo=TIMEZONE)
            self.db.add_points_for_date(
                report_data["user_id"],
                report_data["points"],
                report_date,
                REPORT_TYPES.get(report_data["type"], {}).get("is_family_quest", False)
            )

        if report_data.get("amount") is not None:
            if report_data.get("purpose") == "поінти":
                self.db.update_vault_data(0, report_data["amount"])
            else:
                self.db.update_vault_data(report_data["amount"], 0)

        self.db.remove_report(interaction.message.id)

        # points = report_data["points"]

        # Create status embed
        status_embed = discord.Embed(
            color=discord.Color.green(),
            description=f"✅ Підтверджено | {interaction.user.mention}"

            # description=(
            #     f"✅ Підтверджено | {interaction.user.mention}\n"
            #     f"➕ Нараховано {points} {'бал' if points == 1 else 'бали' if 1 < points < 5 else 'балів'}"
            # )
        )
        
        # Remove buttons and add embed
        await interaction.message.edit(
            content=interaction.message.content,
            attachments=interaction.message.attachments,
            embeds=[status_embed],
            view=None
        )
        await interaction.response.defer()

    @discord.ui.button(
        label="❌ Відхилити",
        style=discord.ButtonStyle.red,
        custom_id="report_reject"
    )
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.db.remove_report(interaction.message.id)

        status_embed = discord.Embed(
            color=discord.Color.red(),
            description=f"❌ Відхилено | {interaction.user.mention}"
        )
        
        await interaction.message.edit(
            content=interaction.message.content,
            attachments=interaction.message.attachments,
            embeds=[status_embed],
            view=None
        )
        await interaction.response.defer()