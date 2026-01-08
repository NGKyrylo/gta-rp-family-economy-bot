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
        removed_roles = before_roles - after_roles

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

        if FAMILY_ROLE_ID in removed_roles:
            # Оновлюємо статус членства в сім'ї на False
            self.db.update_family_status(after.id, False)
            
            # Опціонально: повідомлення в ДМ
            # try:
            #     await after.send(
            #         f"👋 {after.display_name}, тебе видалено з сімейного реєстру.\n"
            #         f"Твій прогрес збережено на випадок повернення."
            #     )
            # except discord.Forbidden:
            #     pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Відстежує вихід користувача з сервера"""
        # Оновлюємо статус на сервері
        self.db.update_server_status(member.id, False)
        self.db.update_family_status(member.id, False)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Відстежує приєднання користувача до сервера"""
        # Перевіряємо чи є користувач в БД
        users = self.db.get_all_users()
        if str(member.id) in users:
            # Користувач повернувся - оновлюємо статус
            self.db.update_server_status(member.id, True)
            # is_family_member оновиться автоматично через on_member_update коли дадуть роль

# обов’язково експортуємо клас
async def setup(bot):
    await bot.add_cog(MemberEvents(bot))
