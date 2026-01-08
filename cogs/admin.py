import discord
from discord.ext import commands
from utils.db_utils import Database
from datetime import datetime
import os
import asyncio
from config import ADMIN_ROLE_ID, TIMEZONE, REQUIRED_WEEKLY_POINTS, ANNOUNCEMENT_CHANNEL_ID, REQUIRED_WEEKLY_POINTS, COMMAND_PREFIX, REPORT_TYPES, WARN_REASONS, ECONOMY_CHANEL_ID, FAMILY_ROLE_ID
from utils.general_utils import send_week_summary, format_money
from utils.warns import send_warn_users_from_week_summary, issue_warn
from utils.check_utils import is_admin_only, is_bot_developer_only, is_economy_controller_only, is_recruiter_only, is_discipline_controller_only, is_bot_developer_slash
from discord import app_commands
from modals.MessageModal import UniversalMessageModal
from modals.EditMessageModal import EditMessageModal

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
        msg = await ctx.send(f"❌ Помилка: {str(error)}")
        await ctx.message.delete()
        await asyncio.sleep(5)
        await msg.delete()

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
    async def set_immunity_channel_error(self, ctx, error):
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
        rewards_data, users, bonus_data = await self.db.finalize_weekly_stats(guild)
        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        await send_week_summary(bot = self.bot, channel=channel, guild=guild, rewards_data=rewards_data, bonus_data=bonus_data)
        await send_warn_users_from_week_summary(guild, REQUIRED_WEEKLY_POINTS)

        vault_data = self.db.get_vault_data()
        economy_chanel = self.bot.get_channel(ECONOMY_CHANEL_ID)
        embed = discord.Embed(
            title="💰 Економічний звіт тижня",
            description=f"Цього тижня зароблено **{format_money(vault_data["week_income"])}$**",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🏦 У общак відправляється",
            value=f"{format_money(bonus_data["week_profit"])}$",
            inline=False
        )

        await economy_chanel.send(embed=embed)
        self.db.week_income_to_zero()
        self.db.update_vault_data(bonus_data["week_profit"], 0)
        
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

    @commands.command(name="devreporthelp", hidden=True)
    @is_bot_developer_only()
    async def dev_report_help(self, ctx):
        """Пояснення, як користуватись звітами."""
    
        # Привітальне звернення у стилі El Contador
        description = (
            "💼 **¡Buenos días, familia!**\n"
            "Я — **El Contador Guerrero**, твій бухгалтер картелю.\n"
            "Я приймаю звіти, рахую поінти й слідкую, щоб ніхто не халявив.\n\n"
            "Нижче наведено **інструкцію**, як правильно подавати звіти, щоб отримати свої бали 💰"
        )

        embed = discord.Embed(
            title="📋 Інструкція зі звітів",
            description=description,
            color=discord.Color.gold()
        )

        # Додати інформацію про типи звітів
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

        embed.add_field(
            name="📝 Активності",
            value="\n".join(activities) or "Немає доступних активностей",
            inline=False
        )

        embed.add_field(
            name="💰 Внески",
            value=donation_help,
            inline=False
        )

        embed.set_footer(text="❗ До кожного звіту додавайте скріншот")

        await ctx.send(embed=embed)

    @commands.command(name="варн")
    @is_discipline_controller_only()
    async def issue_warn_cmd(self, ctx, member: discord.Member, cost: int, *, reason: str):
        """Видати варн користувачу"""
        try:
            # reason_text = WARN_REASONS.get(reason)
            matched_key = next((key for key in WARN_REASONS if key.lower() == reason.lower()), None)

            if matched_key:
                reason_text = WARN_REASONS[matched_key]
            else:
                reason_text = reason
                matched_key = None
            
            guild = ctx.guild
            
            is_quest_related = False

            if reason in ["поінти"]:
                is_quest_related = True

            warn = await issue_warn(guild, member, reason_text, cost, is_quest_related)
            if warn == "max_warns_reached":
                msg = await ctx.send(f"❌ Користувач {member.mention} вже має максимальну кількість варнів.")
                await ctx.message.delete()
                await asyncio.sleep(5)
                await msg.delete()
                return
            if warn == "warn_issued":
                msg = await ctx.send(f"✅ Варн на {cost}$ видано користувачу {member.mention} з причиною: {matched_key if matched_key else reason_text}")
                await ctx.message.delete()
                await asyncio.sleep(5)
                await msg.delete()
                return
            
        except Exception as e:
            msg = await ctx.send(f"❌ Помилка при видачі варну: {str(e)}")
            await ctx.message.delete()
            await asyncio.sleep(5)
            await msg.delete()

    # @app_commands.command(name="say", description="Створити повідомлення (звичайне або embed)")
    # @is_bot_developer_slash()
    # async def say(self, interaction: discord.Interaction):
    #     """Відправляє view з вибором типу повідомлення"""
    #     await interaction.response.send_message(
    #         "🎨 Оберіть тип повідомлення:",
    #         view=MessageTypeView(),
    #         ephemeral=True
    #     )

    # @say.error
    # async def say_error(self, interaction: discord.Interaction, error):
    #     if isinstance(error, app_commands.errors.MissingRole):
    #         await interaction.response.send_message(
    #             "❌ У вас немає доступу до цієї команди.", 
    #             ephemeral=True
    #         )


    # @app_commands.command(name="say", description="Створити повідомлення (текст/embed/текст+embed)")
    # @is_bot_developer_slash()
    # async def say(self, interaction: discord.Interaction):
    #     """Універсальна модалка для створення повідомлень"""
    #     await interaction.response.send_modal(UniversalMessageModal())

    @app_commands.command(name="say", description="Створити повідомлення (текст/embed/текст+embed)")
    @is_bot_developer_slash()
    async def say(self, interaction: discord.Interaction):
        """Універсальна модалка для створення повідомлень"""
        try:
            modal = UniversalMessageModal()
            await interaction.response.send_modal(modal)
        except discord.errors.InteractionResponded:
            # Якщо взаємодія вже оброблена
            await interaction.followup.send("❌ Помилка: взаємодія вже оброблена", ephemeral=True)
        except Exception as e:
            # Обробка інших помилок
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Помилка: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Помилка: {str(e)}", ephemeral=True)

    @commands.command(name="emergency_fix", hidden=True)
    @is_bot_developer_only()
    async def emergency_fix(self, ctx, category: discord.CategoryChannel, role: discord.Role):
        """
        Надає ролі всі права на категорію та всі її канали (включно з гілками).
        Використання: !emergency_fix <категорія> <роль>
        """
        # Видаляємо повідомлення з командою
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        
        # Перевірка ієрархії ролей
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(
                f"❌ Роль {role.mention} вище або дорівнює моїй найвищій ролі! Не можу змінити права.",
                delete_after=10
            )
        
        # Створюємо тимчасове повідомлення про процес
        status_msg = await ctx.send(
            f"🔧 Налаштування прав для ролі {role.mention}...\n"
            f"📁 Категорія: **{category.name}**\n"
            f"⏳ Це може зайняти час..."
        )
        
        try:
            # Створюємо overwrite з усіма правами
            overwrite = discord.PermissionOverwrite.from_pair(
                discord.Permissions.all(), 
                discord.Permissions.none()
            )
            
            # Лічильники
            processed_channels = 0
            processed_threads = 0
            failed_channels = 0
            failed_threads = 0
            
            # Права на категорію
            try:
                await category.set_permissions(role, overwrite=overwrite)
                await asyncio.sleep(0.3)  # Затримка для rate limit
            except discord.HTTPException as e:
                await status_msg.edit(
                    content=f"❌ Не вдалося встановити права на категорію: {e}"
                )
                return
            
            # Проходимо всі канали в категорії
            for channel in category.channels:
                try:
                    await channel.set_permissions(role, overwrite=overwrite)
                    processed_channels += 1
                    await asyncio.sleep(0.3)  # Затримка для rate limit
                    
                    # Оновлюємо статус кожні 3 канали
                    if processed_channels % 3 == 0:
                        await status_msg.edit(
                            content=f"🔧 Обробка...\n"
                                    f"📺 Каналів: {processed_channels}\n"
                                    f"🧵 Гілок: {processed_threads}"
                        )
                    
                except discord.HTTPException:
                    failed_channels += 1
                    continue
                
                # Якщо це текстовий канал — обробляємо гілки
                if isinstance(channel, discord.TextChannel):
                    # Активні гілки
                    for thread in channel.threads:
                        try:
                            await thread.set_permissions(role, overwrite=overwrite)
                            processed_threads += 1
                            await asyncio.sleep(0.2)
                        except discord.HTTPException:
                            failed_threads += 1
                    
                    # Архівовані гілки (публічні)
                    try:
                        async for thread in channel.archived_threads(limit=None):
                            try:
                                await thread.set_permissions(role, overwrite=overwrite)
                                processed_threads += 1
                                await asyncio.sleep(0.2)
                            except discord.HTTPException:
                                failed_threads += 1
                    except discord.HTTPException:
                        pass  # Помилка доступу до архіву
                    
                    # Архівовані приватні гілки
                    try:
                        async for thread in channel.archived_threads(private=True, limit=None):
                            try:
                                await thread.set_permissions(role, overwrite=overwrite)
                                processed_threads += 1
                                await asyncio.sleep(0.2)
                            except discord.HTTPException:
                                failed_threads += 1
                    except discord.HTTPException:
                        pass
            
            # Формуємо фінальне повідомлення
            result_message = (
                f"✅ **Налаштування завершено!**\n\n"
                f"📁 **Категорія:** {category.name}\n"
                f"👤 **Роль:** {role.mention}\n\n"
                f"✅ **Успішно оброблено:**\n"
                f"├ 📺 Каналів: **{processed_channels}**\n"
                f"└ 🧵 Гілок: **{processed_threads}**"
            )
            
            if failed_channels > 0 or failed_threads > 0:
                result_message += (
                    f"\n\n⚠️ **Помилки:**\n"
                    f"├ 📺 Каналів: **{failed_channels}**\n"
                    f"└ 🧵 Гілок: **{failed_threads}**"
                )
            
            await status_msg.edit(content=result_message)
            
            # Видаляємо повідомлення через 15 секунд
            await status_msg.delete(delay=10)
            
        except discord.Forbidden:
            await status_msg.edit(
                content=f"❌ **Недостатньо прав!**\n"
                        f"Переконайтеся, що моя роль вище за {role.mention}"
            )
            await status_msg.delete(delay=10)
            
        except discord.HTTPException as e:
            await status_msg.edit(
                content=f"❌ **Помилка Discord API:**\n```{e}```"
            )
            await status_msg.delete(delay=10)
            
        except Exception as e:
            await status_msg.edit(
                content=f"❌ **Непередбачена помилка:**\n```{type(e).__name__}: {e}```"
            )
            await status_msg.delete(delay=10)


    @emergency_fix.error
    async def emergency_fix_error(self, ctx, error):
        """Обробник помилок для команди emergency_fix"""
        
        # Видаляємо команду з помилкою
        try:
            await ctx.message.delete()
        except:
            pass
        
        if isinstance(error, commands.MissingRequiredArgument):
            msg = await ctx.send(
                "❌ **Неправильне використання!**\n"
                "📖 **Формат:** `!emergency_fix <категорія> <роль>`\n\n"
                "**Приклади:**\n"
                "```\n"
                "!emergency_fix \"Мої канали\" @Модератор\n"
                "!emergency_fix 123456789 @Admin\n"
                "```"
            )
            await msg.delete(delay=10)
            
        elif isinstance(error, commands.BadArgument):
            msg = await ctx.send(
                "❌ **Неправильна категорія або роль!**\n\n"
                "💡 **Підказки:**\n"
                "├ Використовуйте ID або згадку категорії\n"
                "├ Використовуйте згадку ролі (@роль)\n"
                "└ Назви з пробілами беріть в лапки"
            )
            await msg.delete(delay=10)
            
        elif isinstance(error, commands.CheckFailure):
            # Тихо ігноруємо, бо команда hidden і тільки для розробників
            print("!!!")
            pass
            
        else:
            # Логуємо несподівані помилки
            print(f"Помилка в emergency_fix: {type(error).__name__}: {error}")

    @app_commands.command(name="edit", description="Редагувати повідомлення надіслане ботом")
    @is_bot_developer_slash()  # Ваш декоратор для перевірки прав
    async def edit(
        self, 
        interaction: discord.Interaction,
        message_link: str = None,
        message_id: str = None,
        channel_id: str = None
    ):
        """
        Редагувати повідомлення бота
        
        Параметри:
        - message_link: Пряме посилання на повідомлення (найпростіший спосіб)
        - message_id: ID повідомлення (потрібен разом з channel_id)
        - channel_id: ID каналу (потрібен разом з message_id)
        """
        try:
            message = None
            
            # Спосіб 1: Через пряме посилання
            if message_link:
                # Парсинг посилання типу: https://discord.com/channels/GUILD_ID/CHANNEL_ID/MESSAGE_ID
                parts = message_link.rstrip('/').split('/')
                if len(parts) >= 3 and parts[-3] == 'channels':
                    try:
                        msg_channel_id = int(parts[-2])
                        msg_id = int(parts[-1])
                        
                        channel = interaction.guild.get_channel(msg_channel_id)
                        if not channel:
                            channel = interaction.guild.get_thread(msg_channel_id)
                        
                        if channel:
                            message = await channel.fetch_message(msg_id)
                    except (ValueError, IndexError):
                        pass
            
            # Спосіб 2: Через ID повідомлення та каналу
            elif message_id and channel_id:
                try:
                    msg_id = int(message_id)
                    ch_id = int(channel_id)
                    
                    channel = interaction.guild.get_channel(ch_id)
                    if not channel:
                        channel = interaction.guild.get_thread(ch_id)
                    
                    if channel:
                        message = await channel.fetch_message(msg_id)
                except ValueError:
                    pass
            
            # Якщо повідомлення не знайдено
            if not message:
                await interaction.response.send_message(
                    "❌ Не вдалося знайти повідомлення!\n\n"
                    "**Використання команди:**\n"
                    "1. `/edit message_link: [посилання]` - вставте посилання на повідомлення (ПКМ → Копіювати посилання)\n"
                    "2. `/edit message_id: [ID] channel_id: [ID]` - вкажіть ID повідомлення та каналу\n\n"
                    "**Увімкніть режим розробника** в налаштуваннях Discord для копіювання ID!",
                    ephemeral=True
                )
                return
            
            # Перевірка, чи це повідомлення від бота
            if message.author.id != interaction.client.user.id:
                await interaction.response.send_message(
                    "❌ Це повідомлення не від мене! Я можу редагувати лише свої власні повідомлення.",
                    ephemeral=True
                )
                return
            
            # Відкриваємо модалку для редагування
            modal = EditMessageModal(message)
            await interaction.response.send_modal(modal)
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Немає доступу до цього каналу або повідомлення!",
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Повідомлення не знайдено! Можливо воно було видалено.",
                ephemeral=True
            )
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Помилка: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Помилка: {str(e)}",
                    ephemeral=True
                )

    @commands.command(name="listusers", hidden=True)
    @is_bot_developer_only()
    async def list_users(self, ctx):
        """Вивести список всіх користувачів з бази даних"""
        try:
            users = self.db.get_all_users()
            
            if not users:
                await ctx.send("❌ База даних порожня")
                return
            
            # Створюємо список користувачів з трьома категоріями
            family_members = []  # На сервері + є в сім'ї
            not_family = []      # На сервері, але не в сім'ї
            left_server = []     # Поза сервером
            
            for user_id, user_data in users.items():
                try:
                    member = await ctx.guild.fetch_member(int(user_id))
                    
                    # Визначаємо статус та емодзі
                    is_on_server = user_data.get('is_on_server', True)
                    is_family = user_data.get('is_family_member', True)
                    
                    if is_on_server and is_family:
                        status = "👨‍👩‍👧‍👦"  # Член сім'ї
                        category = family_members
                    elif is_on_server and not is_family:
                        status = "👤"  # На сервері, але не в сім'ї
                        category = not_family
                    else:
                        status = "❌"  # Поза сервером
                        category = left_server
                    
                    join_date = datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y')
                    
                    user_info = {
                        'status': status,
                        'display_name': member.display_name,
                        'username': member.name,
                        'user_id': user_id,
                        'mention': member.mention,
                        'join_date': join_date,
                        'total_points': user_data['total_points'],
                        'is_on_server': is_on_server,
                        'is_family': is_family
                    }
                    
                    category.append(user_info)
                        
                except discord.NotFound:
                    # Користувач не знайдений на сервері
                    join_date = datetime.fromisoformat(user_data['join_date']).strftime('%d.%m.%Y')
                    
                    user_info = {
                        'status': '❌',
                        'display_name': '???',
                        'username': 'Не знайдено',
                        'user_id': user_id,
                        'mention': f'<@{user_id}>',
                        'join_date': join_date,
                        'total_points': user_data['total_points'],
                        'is_on_server': False,
                        'is_family': user_data.get('is_family_member', False)
                    }
                    
                    left_server.append(user_info)
            
            # Сортуємо кожну категорію за поінтами
            family_members.sort(key=lambda x: -x['total_points'])
            not_family.sort(key=lambda x: -x['total_points'])
            left_server.sort(key=lambda x: -x['total_points'])
            
            # Об'єднуємо всі списки в правильному порядку
            all_users = family_members + not_family + left_server
            
            # Формуємо повідомлення
            message_parts = []
            message_parts.append(f"**👥 Список користувачів бази даних**")
            message_parts.append(
                f"Всього: **{len(users)}** "
                f"(👨‍👩‍👧‍👦 {len(family_members)} • 👤 {len(not_family)} • ❌ {len(left_server)})\n"
            )
            message_parts.append(
                "**Легенда:** 👨‍👩‍👧‍👦 = Член сім'ї | 👤 = На сервері | ❌ = Покинув сервер\n"
            )
            
            current_message = "\n".join(message_parts)
            messages_to_send = []
            
            # Додаємо розділи
            current_category = None
            
            for i, user in enumerate(all_users, 1):
                # Додаємо заголовок категорії
                if user['is_on_server'] and user['is_family'] and current_category != 'family':
                    current_message += "\n**👨‍👩‍👧‍👦 ЧЛЕНИ СІМ'Ї:**\n"
                    current_category = 'family'
                elif user['is_on_server'] and not user['is_family'] and current_category != 'not_family':
                    current_message += "\n**👤 НЕ ЧЛЕНИ СІМ'Ї (на сервері):**\n"
                    current_category = 'not_family'
                elif not user['is_on_server'] and current_category != 'left':
                    current_message += "\n**❌ ПОКИНУЛИ СЕРВЕР:**\n"
                    current_category = 'left'
                
                user_line = (
                    f"{user['status']} **{i}.** {user['display_name']} (`{user['username']}`)\n"
                    f"   • ID: `{user['user_id']}`\n"
                    f"   • {user['mention']} • {user['join_date']} • **{user['total_points']}** поінтів\n"
                )
                
                # Перевіряємо, чи не перевищимо ліміт Discord (2000 символів)
                if len(current_message) + len(user_line) > 1900:
                    messages_to_send.append(current_message)
                    current_message = user_line
                else:
                    current_message += user_line
            
            # Додаємо останнє повідомлення
            if current_message:
                messages_to_send.append(current_message)
            
            # Відправляємо всі повідомлення
            for msg in messages_to_send:
                await ctx.send(msg)
            
        except Exception as e:
            await ctx.send(f"❌ Помилка при виведенні списку користувачів: {str(e)}")

    @list_users.error
    async def list_users_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            return
        await ctx.send(f"❌ Помилка: {str(error)}")

    @commands.command(name="fixstatuses", hidden=True)
    @is_bot_developer_only()
    async def fix_statuses(self, ctx):
        """Синхронізувати статуси користувачів БД з реальним станом сервера"""
        try:
            status_msg = await ctx.send("🔄 Починаю синхронізацію статусів...")
            
            users = self.db.get_all_users()
            
            if not users:
                await status_msg.edit(content="❌ База даних порожня")
                return
            
            # Статистика змін
            stats = {
                'checked': 0,
                'fixed_is_on_server': 0,
                'fixed_is_family_member': 0,
                'role_reassigned': 0,
                'not_touched': 0
            }
            
            changes = []
            
            # Отримуємо всіх членів сервера
            all_members = {member.id: member for member in ctx.guild.members}
            
            # Проходимо по всім записам у БД
            for user_id_str, user_data in users.items():
                user_id = int(user_id_str)
                stats['checked'] += 1
                
                # Отримуємо дані з БД
                db_is_on_server = user_data.get('is_on_server', True)
                db_is_family = user_data.get('is_family_member', True)
                
                # Перевіряємо, чи користувач на сервері
                if user_id in all_members:
                    member = all_members[user_id]
                    
                    # Перевіряємо наявність FAMILY_ROLE_ID
                    has_family_role = any(role.id == FAMILY_ROLE_ID for role in member.roles)
                    
                    # Виправляємо is_on_server
                    if not db_is_on_server:
                        self.db.update_server_status(user_id, True)
                        stats['fixed_is_on_server'] += 1
                        changes.append(f"✅ `{user_id}` ({member.display_name}): is_on_server → True")
                    
                    # Виправляємо is_family_member
                    if has_family_role and not db_is_family:
                        self.db.update_family_status(user_id, True)
                        stats['fixed_is_family_member'] += 1
                        changes.append(f"👨‍👩‍👧‍👦 `{user_id}` ({member.display_name}): is_family_member → True")
                    elif not has_family_role and db_is_family:
                        self.db.update_family_status(user_id, False)
                        stats['fixed_is_family_member'] += 1
                        changes.append(f"👤 `{user_id}` ({member.display_name}): is_family_member → False")
                    
                else:
                    # Користувача немає на сервері
                    if db_is_on_server:
                        self.db.update_server_status(user_id, False)
                        stats['fixed_is_on_server'] += 1
                        changes.append(f"❌ `{user_id}`: is_on_server → False (покинув сервер)")
            
            # Перевіряємо користувачів на сервері, яких немає в БД
            await status_msg.edit(content="🔄 Перевіряю користувачів на сервері...")
            
            for member_id, member in all_members.items():
                if str(member_id) not in users:
                    # Користувача немає в БД
                    has_family_role = any(role.id == FAMILY_ROLE_ID for role in member.roles)
                    
                    if has_family_role:
                        # Має роль сім'ї - перевидаємо роль (спрацює on_member_update)
                        try:
                            family_role = ctx.guild.get_role(FAMILY_ROLE_ID)
                            if family_role:
                                await member.remove_roles(family_role)
                                await asyncio.sleep(0.5)
                                await member.add_roles(family_role)
                                stats['role_reassigned'] += 1
                                changes.append(f"🔄 `{member_id}` ({member.display_name}): роль перевидана (додано до БД)")
                        except discord.Forbidden:
                            changes.append(f"⚠️ `{member_id}` ({member.display_name}): немає прав перевидати роль")
                    else:
                        # Немає ролі сім'ї - не чіпаємо
                        stats['not_touched'] += 1
            
            # Формуємо звіт
            embed = discord.Embed(
                title="✅ Синхронізація завершена",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 Статистика",
                value=(
                    f"Перевірено записів у БД: **{stats['checked']}**\n"
                    f"Виправлено is_on_server: **{stats['fixed_is_on_server']}**\n"
                    f"Виправлено is_family_member: **{stats['fixed_is_family_member']}**\n"
                    f"Перевидано ролей: **{stats['role_reassigned']}**\n"
                    f"Не чіпали (без ролі): **{stats['not_touched']}**"
                ),
                inline=False
            )
            
            total_changes = stats['fixed_is_on_server'] + stats['fixed_is_family_member'] + stats['role_reassigned']
            
            if total_changes == 0:
                embed.add_field(
                    name="✅ Результат",
                    value="Всі статуси коректні, змін не потрібно!",
                    inline=False
                )
            else:
                # Показуємо перші 10 змін
                changes_text = "\n".join(changes[:10])
                if len(changes) > 10:
                    changes_text += f"\n... та ще {len(changes) - 10} змін"
                
                embed.add_field(
                    name="🔧 Виконані зміни",
                    value=changes_text if changes_text else "Немає",
                    inline=False
                )
            
            await status_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Помилка при синхронізації статусів: {str(e)}")

    @fix_statuses.error
    async def fix_statuses_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            return
        await ctx.send(f"❌ Помилка: {str(error)}")


async def setup(bot):
    await bot.add_cog(Admin(bot))