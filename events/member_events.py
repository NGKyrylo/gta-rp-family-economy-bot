import discord
from discord.ext import commands
from utils.db_utils import Database
from config import FAMILY_ROLE_ID

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()


    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # перевірка — чи з’явилася роль сім’ї
        before_roles = {r.id for r in before.roles}
        after_roles = {r.id for r in after.roles}

        added_roles = after_roles - before_roles
        if FAMILY_ROLE_ID in added_roles:
            # додаємо користувача до БД
            self.db.add_user(after.id)

            # пробуємо надіслати повідомлення в ДМ
            try:
                await after.send(
                    f"👋 {after.display_name}, тебе додано до сімейного реєстру!\n"
                    f"Тепер ти можеш користуватись командою `!звіт`, брати участь у квестах і заробляти поінти 💰"
                )
            except discord.Forbidden:
                pass  # не вдалося надіслати ДМ

# обов’язково експортуємо клас
async def setup(bot):
    await bot.add_cog(MemberEvents(bot))
