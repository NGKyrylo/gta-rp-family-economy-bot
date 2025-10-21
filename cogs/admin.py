import discord
from discord.ext import commands
from utils.db_utils import Database
from datetime import datetime
import os
import asyncio
from config import ADMIN_ROLE_ID, TIMEZONE, REQUIRED_WEEKLY_POINTS, ANNOUNCEMENT_CHANNEL_ID, REQUIRED_WEEKLY_POINTS, COMMAND_PREFIX, REPORT_TYPES
from utils.general_utils import send_week_summary
from utils.warns import issue_warns_from_week_summary
from utils.check_utils import is_admin_only, is_bot_developer_only, is_economy_controller_only, is_recruiter_only

def get_points_word(points: float) -> str:
    """Helper to get correct word form for points"""
    if points == 1:
        return "поінт"
    if 1 < points < 5:
        return "поінти"
    return "поінтів"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    # async def cog_check(self, ctx):
    #     # Allow commands to execute but hide from general help
    #     return False
    
    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            # Silently ignore permission errors
            return
        await ctx.send(f"❌ Помилка: {str(error)}")

    @commands.command(name="helpadmin", hidden=True)
    @commands.has_role(ADMIN_ROLE_ID)
    async def help_admin(self, ctx):
        """Показати список адмін-команд"""
        embed = discord.Embed(
            title="🛠️ Адмін-команди",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👥 Управління користувачами",
            value=(
                "`!adduser <@користувач>` - Додати користувача в систему\n"
                "`!resetweek` - Скинути тижневу статистику всіх користувачів"
                "`!endweek` - Примусово завершити тиждень і опублікувати підсумки (всі данні поточного тижня будуть переписані в минулий не залежно від дат)"
            ),
            inline=False
        )

        embed.add_field(
            name="💰 Управління поінтами",
            value=(
                "`!addpoints <@користувач> <кількість>` - Додати поінти\n"
                "`!removepoints <@користувач> <кількість>` - Відняти поінти"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Управління імунітетом",
            value=(
                "`!addimmunity <@користувач|@роль>` - Додати привілейований імунітет\n"
                "`!removeimmunity <@користувач|@роль>` - Видалити привілейований імунітет\n"
                "`!setimmunitychannel <#канал> <@роль> <@користувач>` - Встановити канал для повідомлення про імунітет"
            ),
            inline=False
        )

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="adduser")
    @is_recruiter_only()
    async def add_user(self, ctx, member: discord.Member):
        """Додати користувача в систему"""
        try:
            self.db.add_user(member.id)
            await ctx.send(f"✅ Користувача {member.mention} додано до системи")
        except Exception as e:
            await ctx.send(f"❌ Помилка при додаванні користувача: {str(e)}")

    @commands.command(name="resetweek", hidden=True)
    @is_bot_developer_only()
    async def reset_week(self, ctx):
        """Скинути тижневу статистику"""
        try:
            self.db.reset_weekly_stats()
            await ctx.send("✅ Тижневу статистику скинуто")
        except Exception as e:
            await ctx.send(f"❌ Помилка при скиданні статистики: {str(e)}")

    # Error handling
    @add_user.error
    @reset_week.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            # Silently ignore permission errors
            return
        await ctx.send(f"❌ Помилка: {str(error)}")


    @commands.command(name="addpoints")
    @is_economy_controller_only()
    async def add_points(self, ctx, member: discord.Member, points: float):
        """Додати бали користувачу"""
        try:
            self.db.add_points(member.id, points)
            await ctx.send(
                f"✅ Додано {points} {get_points_word(points)} "
                f"користувачу {member.mention}"
            )
        except Exception as e:
            await ctx.send(f"❌ Помилка при додаванні балів: {str(e)}")

    @commands.command(name="removepoints")
    @is_economy_controller_only()
    async def remove_points(self, ctx, member: discord.Member, points: float):
        """Відняти бали у користувача"""
        try:
            self.db.add_points(member.id, -points)  # Using negative points
            await ctx.send(
                f"✅ Віднято {points} {get_points_word(points)} "
                f"у користувача {member.mention}"
            )
        except Exception as e:
            await ctx.send(f"❌ Помилка при відніманні балів: {str(e)}")

    # Add error handlers for new commands
    @add_points.error
    @remove_points.error
    async def points_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Використання: !addpoints/@removepoints <@користувач> <кількість>")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Неправильний формат аргументів. Приклад: !addpoints @user 1.5")
        else:
            await ctx.send(f"❌ Помилка: {str(error)}")

    @commands.command(name="setjoindate", hidden=True)
    @is_bot_developer_only()
    async def set_join_date(self, ctx, member: discord.Member, date_str: str):
        """Встановити дату приєднання користувача (формат: дд.мм.рррр)"""
        try:
            join_date = datetime.strptime(date_str, "%d.%m.%Y")
            self.db.set_join_date(member.id, join_date)
            msg = await ctx.send(f"✅ Дату приєднання {member.mention} встановлено на {date_str}")
            await ctx.message.delete()
            await asyncio.sleep(5)
            await msg.delete()
        except ValueError:
            msg = await ctx.send("❌ Неправильний формат дати. Використовуйте дд.мм.рррр")
            await ctx.message.delete()
            await asyncio.sleep(5)
            await msg.delete()
        except Exception as e:
            msg = await ctx.send(f"❌ Помилка при встановленні дати: {str(e)}")
            await ctx.message.delete()
            await asyncio.sleep(5)
            await msg.delete()




    async def update_immunity_message(self, guild: discord.Guild):
        # сюди вставляєш код функції
        privileged = self.db._load_json(self.db.privileged_file)
        channel_id = privileged.get("immunity_channel_id")
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        permanent_mentions = [f"<@{uid}>" for uid in privileged.get("users", [])]
        role_mentions = [f"<@&{rid}>" for rid in privileged.get("roles", [])]
        
        # message_text = (
        #     f"{guild.get_role(privileged.get('family_role_id')).mention}\n"
        #     "Імунітет звільняє ТІЛЬКИ від виконання квестів. "
        #     "Порушення інших правил тягне за собою покарання. "
        #     f"Постійний імунітет видається особисто {guild.get_member(privileged.get('permanent_user_id')).mention}. "
        #     "Набутий видається тимчасово для окремих посад та ролей.\n\n"
        #     "📌 **Постійний імунітет:**\n"
        #     + "\n".join(f"- {mention}" for mention in permanent_mentions) + "\n\n"
        #     "📌 **Набутий імунітет:**\n"
        #     + "\n".join(f"- {mention}" for mention in role_mentions)
        # )

        message_text = (f"{guild.get_role(privileged.get('family_role_id')).mention}\n")

        embed = discord.Embed(
            title="🛡️ Привілейований імунітет",
            description="Імунітет звільняє ТІЛЬКИ від виконання квестів. "
                        f"Постійний імунітет видається особисто {guild.get_member(privileged.get('permanent_user_id')).mention}. "
                        "Набутий видається тимчасово для окремих посад та ролей.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="✨ Постійний імунітет",
            value="\n".join(f"- {mention}" for mention in permanent_mentions) or "Немає",
            inline=False
        )

        embed.add_field(
            name="⚡ Набутий імунітет",
            value="\n".join(f"- {mention}" for mention in role_mentions) or "Немає",
            inline=False
        )

        old_msg_id = privileged.get("immunity_message_id")
        try:
            if old_msg_id:
                old_msg = await channel.fetch_message(old_msg_id)
                # await old_msg.edit(content=message_text)
                await old_msg.edit(content=message_text, embed=embed)
            else:
                # msg = await channel.send(message_text)
                msg = await channel.send(content=message_text, embed=embed)
                privileged["immunity_message_id"] = msg.id
        except discord.NotFound:
            # msg = await channel.send(message_text)
            msg = await channel.send(content=message_text, embed=embed)
            privileged["immunity_message_id"] = msg.id

        self.db._save_json(self.db.privileged_file, privileged)

    @commands.command(name="addimmunity")
    @is_admin_only()
    async def add_immunity(self, ctx, mention: str):
        """Додає імунітет користувачу або ролі"""
        privileged = self.db._load_json(self.db.privileged_file)

        privileged = self.db._load_json(self.db.privileged_file)
        if "users" not in privileged:
            privileged["users"] = []
        if "roles" not in privileged:
            privileged["roles"] = []

        # Перевірка користувача
        if mention.startswith("<@") and mention.endswith(">") and not mention.startswith("<@&"):
            try:
                user_id = int(mention.strip("<@!>"))
                member = ctx.guild.get_member(user_id)
                if not member:
                    await ctx.send(f"❌ Користувача {mention} не знайдено на сервері.")
                    return
                user_id_str = str(member.id)
                if user_id_str in privileged["users"]:
                    await ctx.send(f"❌ Користувач {member.mention} вже має імунітет.")
                    return
                privileged["users"].append(user_id_str)
                self.db._save_json(self.db.privileged_file, privileged)
                await ctx.send(f"✅ Імунітет додано користувачу {member.mention}")
                await self.update_immunity_message(ctx.guild)
                return
            except ValueError:
                await ctx.send(f"❌ Некоректний формат користувача: {mention}")
                return

        # Перевірка ролі
        if mention.startswith("<@&") and mention.endswith(">"):
            try:
                role_id = int(mention[3:-1])  # видаляємо <@& і >
                guild_role = ctx.guild.get_role(role_id)
                if not guild_role:
                    await ctx.send(f"❌ Роль {mention} не знайдено на сервері.")
                    return
                if role_id in privileged["roles"]:
                    await ctx.send(f"❌ Роль {guild_role.name} вже має імунітет.")
                    return
                privileged["roles"].append(role_id)
                self.db._save_json(self.db.privileged_file, privileged)
                await ctx.send(f"✅ Імунітет додано ролі {guild_role.name}")
                await self.update_immunity_message(ctx.guild)
                return
            except ValueError:
                await ctx.send(f"❌ Некоректний формат ролі: {mention}")
                return

        # Якщо рядок не підпадає під mention
        await ctx.send("❌ Некоректний формат mention. Використовуйте @користувач або @роль")

    @commands.command(name="removeimmunity")
    @is_admin_only()
    async def remove_immunity(self, ctx, mention: str):
        """Видаляє імунітет користувачу або ролі"""
        privileged = self.db._load_json(self.db.privileged_file)

        if "users" not in privileged:
            privileged["users"] = []
        if "roles" not in privileged:
            privileged["roles"] = []

        # Користувач
        if mention.startswith("<@") and mention.endswith(">") and not mention.startswith("<@&"):
            try:
                user_id = int(mention.strip("<@!>"))
                member = ctx.guild.get_member(user_id)
                if not member:
                    await ctx.send(f"❌ Користувача {mention} не знайдено на сервері.")
                    return
                user_id_str = str(member.id)
                if user_id_str not in privileged["users"]:
                    await ctx.send(f"❌ Користувач {member.mention} не має імунітету.")
                    return
                privileged["users"].remove(user_id_str)
                self.db._save_json(self.db.privileged_file, privileged)
                await ctx.send(f"✅ Імунітет видалено користувачу {member.mention}")
                await self.update_immunity_message(ctx.guild)
                return
            except ValueError:
                await ctx.send(f"❌ Некоректний формат користувача: {mention}")
                return

        # Роль
        if mention.startswith("<@&") and mention.endswith(">"):
            try:
                role_id = int(mention[3:-1])
                guild_role = ctx.guild.get_role(role_id)
                if not guild_role:
                    await ctx.send(f"❌ Роль {mention} не знайдено на сервері.")
                    return
                if role_id not in privileged["roles"]:
                    await ctx.send(f"❌ Роль {guild_role.name} не має імунітету.")
                    return
                privileged["roles"].remove(role_id)
                self.db._save_json(self.db.privileged_file, privileged)
                await ctx.send(f"✅ Імунітет видалено ролі {guild_role.name}")
                await self.update_immunity_message(ctx.guild)
                return
            except ValueError:
                await ctx.send(f"❌ Некоректний формат ролі: {mention}")
                return

        # Якщо не підходить формат
        await ctx.send("❌ Некоректний формат mention. Використовуйте @користувач або @роль")
    
    @commands.command(name="setimmunitychannel")
    @is_admin_only()
    async def set_immunity_channel(self, ctx, channel: discord.TextChannel, family_role: discord.Role, permanent_user: discord.Member):
        """
        Встановлює канал для повідомлення про імунітет.
        """
        privileged = self.db._load_json(self.db.privileged_file)
        old_channel_id = privileged.get("immunity_channel_id")
        old_message_id = privileged.get("immunity_message_id")

        # Видаляємо старе повідомлення, якщо канал змінився
        if old_channel_id and old_message_id and old_channel_id != channel.id:
            old_channel = ctx.guild.get_channel(old_channel_id)
            if old_channel:
                try:
                    old_message = await old_channel.fetch_message(old_message_id)
                    await old_message.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass  # повідомлення вже видалене або немає доступу

        
        privileged["immunity_channel_id"] = channel.id
        privileged["family_role_id"] = family_role.id
        privileged["permanent_user_id"] = permanent_user.id
        if old_channel_id != channel.id:
            # видалити старе повідомлення
            privileged["immunity_message_id"] = None

        self.db._save_json(self.db.privileged_file, privileged)

        await ctx.send(f"✅ Канал для повідомлень про імунітети встановлено: {channel.mention}\n"
                   f"Постійна роль: {family_role.mention}\n"
                   f"Постійний користувач: {permanent_user.mention}")
        await self.update_immunity_message(ctx.guild)

    @set_immunity_channel.error
    async def set_immunity_channel_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "❌ Ви пропустили обов'язковий аргумент!\n"
                "Правильний синтаксис: `!setimmunitychannel <#канал> <@роль> <@користувач>`"
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Некоректний тип аргументу. Переконайтесь, що вказали канал, роль і користувача.")
        else:
            await ctx.send(f"❌ Сталася помилка: {error}")

    @commands.command(name="endweek", hidden=True)
    @is_bot_developer_only()
    async def end_week(self, ctx):
        """Адмін-команда для примусового завершення тижня"""
        guild = ctx.guild
        rewards_data, users = self.db.finalize_weekly_stats(guild)
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        await send_week_summary(channel, guild, rewards_data)
        await issue_warns_from_week_summary(guild, REQUIRED_WEEKLY_POINTS)
        msg = await ctx.send("✅ Тиждень завершено вручну та підсумки опубліковані.")
        await ctx.message.delete()
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command(name="devhello", hidden=True)
    @is_bot_developer_only()
    async def dev_hello(self, ctx):
        """Відправити привітальне повідомлення в канал оголошень"""
        channel = ctx.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            await ctx.send("❌ Канал оголошень не знайдено!")
            return

        # Основний опис бота
        greeting = (
            "🤖 **Привіт! Я El Contador Guerrero** — ваш помічник у контролі сімейних активностей та звітів.\n"
            "Я слідкую за квестами, підраховую поінти, допомагаю керувати внесками і відслідковую статистику.\n"
            "Все, що вам потрібно — скористатися командами нижче, а я потурбуюсь, щоб система була під контролем картелю."
        )

        embed = discord.Embed(
            description=greeting,
            color=discord.Color.gold()
        )

        # embed.set_image(url="https://media.discordapp.net/attachments/652911880465154070/1429522475867181257/greet.png?ex=68f6720d&is=68f5208d&hm=fb2499f4cdc7763ac0fd330271cb3762f84f2e97c28504bd989fba39b923ef29&=&format=webp&quality=lossless&width=1376&height=917")

        # Сімейні квести
        family_quests = []
        activities = []
        
        for cmd, info in REPORT_TYPES.items():
            if cmd == "внесок":
                donation_help = "\n".join(info["help"])
                continue
                
            if info.get("is_family_quest"):
                family_quests.append(info["help"])
            else:
                activities.append(info["help"])

        embed.add_field(
            name="🎯 Сімейні квести",
            value="\n".join(family_quests) or "Немає доступних квестів",
            inline=False
        )

        # Активності
        embed.add_field(
            name="📝 Активності",
            value="\n".join(activities) or "Немає доступних активностей",
            inline=False
        )

        # Внески
        embed.add_field(
            name="💰 Внески",
            value=donation_help,
            inline=False
        )

        # Квести
        embed.add_field(
            name="⚔️ Квести",
            value=(
                "`!квест` - показати інформацію про квести\n"
                "`!квест <тип> <час> <дата>` - створити квест\n"
                "`!квести` - переглянути статус усіх квестів\n\n"
            ),
            inline=False
        )

        # Квести
        embed.add_field(
            name="📊 Статистика",
            value=(
                "`!статистика` - переглянути власну статистику\n"
                "`!статистика @користувач` - переглянути статистику користувача\n"
            ),
            inline=False
        )

        # Важлива інформація
        embed.add_field(
            name="ℹ️ Важливо знати",
            value=(
                f"• Мінімум {REQUIRED_WEEKLY_POINTS} поінти на тиждень\n"
                "• До кожного звіту потрібен скріншот\n"
                "• Тиждень закінчується в неділю о 23:59\n"
            ),
            inline=False
        )

        embed.set_footer(text=f"`!help` - показати всі доступні команди")

        with open("img/greet.png", "rb") as img:
            file = discord.File(img, filename="greet.png")
            await channel.send(file=file, embed=embed)
        # await channel.send(embed=embed)
        await ctx.message.add_reaction("✅")
        
async def setup(bot):
    await bot.add_cog(Admin(bot))