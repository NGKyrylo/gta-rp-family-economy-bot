from discord.ext import commands
import discord
from zoneinfo import ZoneInfo
from utils.general_utils import post_debt

class DebtCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="борг")
    async def debt(self, ctx, amount: float, member: discord.Member, *, reason: str):
        """
        Використання: !борг <сума> <@mention> <причина>
        """
        text = f"{member.mention}: {reason}"
        await post_debt(
            bot=self.bot,
            guild=ctx.guild,
            amount=amount,
            reason=text
        )
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(DebtCog(bot))