import asyncio
import discord
from discord.ext import commands
from utils.db_utils import Database
from utils.check_utils import is_worker_only, is_economy_controller_only
from utils.general_utils import format_money
from config import ECONOMY_CHANEL_ID

class Vault(commands.Cog):
    """Обробка сховища общака"""
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @commands.command(name='сейф')
    @is_worker_only()
    async def vault(self, ctx, amount = None, *, reason = None):
        """Перевірка балансу общака або додавання коштів до нього.
        
        Використання:
        !сейф - показати баланс общака
        !сейф <сума> <причина> - додати кошти до общака з вказаною причиною
        """
        
        if amount is None:
            # Показати баланс общака
            vault_data = self.db.get_vault_data()
            family_pot = vault_data.get("family_pot", 0)
            week_income = vault_data.get("week_income", 0)
            embed = discord.Embed(title="💼 Баланс общака", color=discord.Color.gold())
            embed.add_field(name="Загальний баланс общака", value=f"{format_money(int(family_pot))}$", inline=False)
            embed.add_field(name="Доходи за тиждень", value=f"{format_money(int(week_income))}$", inline=False)
            msg = await ctx.send(embed=embed)
            await ctx.message.delete()
            await asyncio.sleep(20)
            await msg.delete()
            return
        else:
            if reason is None:
                msg = await ctx.send("⚠️ Будь ласка, вкажіть причину для додавання запису.")
                await ctx.message.delete()
                await asyncio.sleep(5)
                await msg.delete()
                return
            
            try:
                amount = int(amount)
            except ValueError:
                msg = await ctx.send("❌ Будь ласка, введіть дійсну числову суму.")
                await ctx.message.delete()
                await asyncio.sleep(5)
                await msg.delete()
                return
            
            if amount < 0:
                self.db.update_vault_data(amount, 0)
                color = discord.Color.red()
                title = "📉 Додано запис про витрати"
            if amount > 0:
                self.db.update_vault_data(0, amount)
                color = discord.Color.green()
                title = "💹 Додано запис про надходження"
            if amount == 0:
                msg = await ctx.send("⚠️ Сума не може бути нулем.")
                await ctx.message.delete()
                await asyncio.sleep(5)
                await msg.delete()
                return
            
            embed = discord.Embed(
                title=title,
                color=color,
                timestamp=ctx.message.created_at
            )
            embed.add_field(name="Сума", value=f"{'+' if amount > 0 else ''}{format_money(amount)}$", inline=True)
            embed.add_field(name="Причина", value=f"📝 {reason}", inline=False)
            embed.set_footer(text=f"Запис вніс: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            
            economy_chanel = self.bot.get_channel(ECONOMY_CHANEL_ID)
            await economy_chanel.send(embed=embed)
            await ctx.message.delete()

    @commands.command(name="оновити-сейф")
    @is_economy_controller_only()
    async def update_vault(self, ctx, family_pot=None, week_income=None, *, reason=None):
        """Оновлює дані сейфу (лише для контролерів економіки)."""
    
        # Перевірки
        if family_pot is None or week_income is None or reason is None:
            msg = await ctx.send("⚠️ Формат: `!оновити-сейф <загальний_баланс> <дохід_за_тиждень> <причина>`")
            await ctx.message.delete()
            await asyncio.sleep(6)
            await msg.delete()
            return
        
        # Перевірка чисел
        try:
            family_pot = int(family_pot)
            week_income = int(week_income)
        except ValueError:
            msg = await ctx.send("❌ Суми мають бути числовими значеннями.")
            await ctx.message.delete()
            await asyncio.sleep(5)
            await msg.delete()
            return
        
        # Оновлення бази
        self.db.update_vault_data(family_pot, week_income)

        # Формуємо гарний ембед
        embed = discord.Embed(
            title="💰 Оновлення даних сейфу",
            description=f"📝 **Причина:** {reason}",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        embed.add_field(name="🔸 Зміна Общаку балансу", value=f"{'+' if family_pot > 0 else ''}{format_money(family_pot)}$", inline=False)
        embed.add_field(name="🔹 Зміна доходів за тиждень", value=f"{'+' if week_income > 0 else ''}{format_money(week_income)}$", inline=False)
        embed.set_footer(text=f"Оновив: {ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        economy_chanel = self.bot.get_channel(ECONOMY_CHANEL_ID)
        await economy_chanel.send(embed=embed)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Vault(bot))