import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timezone

from utils.general_utils import parse_report_date, find_type
from views.report_views import ConfirmReportView
from utils.db_utils import Database

from config import REPORT_CHANNELS, ADMIN_ROLE_ID, REPORT_TYPES, POINT_COST

class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    def formated_help_embed(self):
        # Create embed
        embed = discord.Embed(
            title="📋 Доступні команди",
            color=discord.Color.gold()
        )

        # Group activities
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

        # Add fields to embed
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

        return embed

    @commands.command(name="звіт")
    async def report(self, ctx, *, args_str: str = None):
        """Команда для звітування про активність"""

        if not args_str:
            embed = self.formated_help_embed()
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await msg.delete()
            await ctx.message.delete()
            return

        # Split into words and find report type
        words = args_str.split()
        report_type = None
        remaining_args = []

        # Try different word combinations from start
        for i in range(len(words), 0, -1):
            test_type = " ".join(words[:i])
            found_type = find_type(test_type, REPORT_TYPES)
            if found_type:
                report_type = found_type
                remaining_args = words[i:]
                break
        
        # Check report type
        if not report_type or report_type not in REPORT_TYPES:
            embed = self.formated_help_embed()
            # Send embed
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await msg.delete()
            await ctx.message.delete()
            return

        r_type = REPORT_TYPES[report_type]
        category = r_type["category"]
        report_channel_id = REPORT_CHANNELS[category]

        # Handle different report types
        if report_type == "внесок":
            if len(remaining_args) < 2:
                msg = await ctx.send("❌ Вкажіть суму та призначення внеску!")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
            
            try:
                amount = float(remaining_args[0])
                purpose = " ".join(remaining_args[1:])

                # Calculate points if purpose is "поінти"
                if purpose.lower() == "поінти":
                    points = int(amount // POINT_COST)
                    if points == 0:
                        msg = await ctx.send(f"❌ Мінімальна сума для отримання балів: {POINT_COST:,}$")
                        await asyncio.sleep(5)
                        await msg.delete()
                        await ctx.message.delete()
                        return
                
                report_date = parse_report_date(None)

                report_text = [
                    f"💵 **Внесок:** {amount:,.2f}$",
                    f"👤 **Користувач:** {ctx.author.mention}",
                    f"📋 **Призначення:** {purpose}"
                ]
                
                if purpose.lower() == "поінти":
                    report_text.append(f"💰 **Поінти:** {points}")
                    remainder = amount % POINT_COST
                    if remainder > 0:
                        report_text.append(f"ℹ️ _Залишок {remainder:,.2f}$ не враховано у бали_")

            except ValueError:
                msg = await ctx.send("❌ Некоректна сума внеску!")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return

        elif report_type == "допомога":
            if not remaining_args or remaining_args[0] not in r_type["variants"]:
                variants = "/".join(r_type["variants"].keys())
                msg = await ctx.send(f"❌ Вкажи тип допомоги: {variants}")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
                
            variant = r_type["variants"][remaining_args[0]]
            date_str = remaining_args[1] if len(remaining_args) > 1 else None
            
            # Check screenshots count
            if len(ctx.message.attachments) < variant["required_screenshots"]:
                msg = await ctx.send(f"❌ Потрібно {variant['required_screenshots']} скріншот{'и' if variant['required_screenshots'] > 1 else ''}!")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
                
            report_date = parse_report_date(date_str)
            if not report_date:
                msg = await ctx.send("❌ Некоректна дата! Формат: дд.мм")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
            
            points = variant["points"]
                
            report_text = [
                f"📝 **Звіт:** {r_type['label']}{' - ' + variant['label'] if variant['label'] != '' else ''} ({report_date})",
                f"👤 **Користувач:** {ctx.author.mention}"
            ]

        elif r_type.get("requires_hours"):
            if not remaining_args or not remaining_args[0].isdigit():
                msg = await ctx.send("❌ Вкажи кількість повних годин патруля!")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
            
            hours = int(remaining_args[0])
            date_str = remaining_args[1] if len(remaining_args) > 1 else None
            report_date = parse_report_date(date_str)
            
            if not report_date:
                msg = await ctx.send("❌ Некоректна дата! Формат: дд.мм")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
            
            points = hours * r_type["points_per_hour"]
                
            report_text = [
                f"📝 **Звіт:** {r_type['label']} ({report_date})",
                f"👤 **Користувач:** {ctx.author.mention}",
                f"⏰ **Годин:** {hours}"
            ]

        else:
            # Regular reports
            date_str = remaining_args[0] if remaining_args else None
            report_date = parse_report_date(date_str)
            
            if not report_date:
                msg = await ctx.send("❌ Некоректна дата! Формат: дд.мм")
                await asyncio.sleep(5)
                await msg.delete()
                await ctx.message.delete()
                return
            
            points = r_type.get("points", 0)
                
            report_text = [
                f"📝 **Звіт:** {r_type['label']} ({report_date})",
                f"👤 **Користувач:** {ctx.author.mention}"
            ]

        # Check for screenshots
        if not ctx.message.attachments:
            msg = await ctx.send("❌ Додай хоча б один скріншот до звіту.")
            await asyncio.sleep(5)
            await msg.delete()
            await ctx.message.delete()
            return

        # Finalize report message
        report_text = "\n".join(report_text)
        report_text += "\n───────────────────────────────"

        # Save report data before sending
        report_data = {
            "user_id": ctx.author.id,
            "type": report_type,
            "points": points if "points" in locals() else 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_date": report_date
        }

        # Send report
        files = [await att.to_file() for att in ctx.message.attachments]
        report_channel = self.bot.get_channel(report_channel_id)
        view = ConfirmReportView(admin_role_id=ADMIN_ROLE_ID)
        report_msg = await report_channel.send(content=report_text, files=files, view=view)

        # Save report with message ID
        self.db.save_report(report_msg.id, report_data)
        
        await ctx.message.delete()
        msg = await ctx.send("✅ Звіт успішно відправлено!")
        await asyncio.sleep(5)
        await msg.delete()

async def setup(bot):
    await bot.add_cog(Reports(bot))