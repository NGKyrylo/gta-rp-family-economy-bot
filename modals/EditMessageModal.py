import discord
from typing import Optional

class EditMessageModal(discord.ui.Modal, title="✏️ Редагувати повідомлення"):
    new_content = discord.ui.TextInput(
        label="Новий текст (необов'язково)",
        style=discord.TextStyle.long,
        placeholder="Новий звичайний текст повідомлення (залиште порожнім, щоб видалити)",
        required=False,
        max_length=2000
    )
    
    embed_title = discord.ui.TextInput(
        label="Заголовок Embed (необов'язково)",
        style=discord.TextStyle.short,
        placeholder="Новий заголовок embed (залиште порожнім, щоб не змінювати)",
        required=False,
        max_length=256
    )
    
    embed_description = discord.ui.TextInput(
        label="Опис Embed (необов'язково)",
        style=discord.TextStyle.long,
        placeholder="Новий опис embed (залиште порожнім, щоб не змінювати)",
        required=False,
        max_length=4000
    )
    
    embed_color = discord.ui.TextInput(
        label="Колір Embed (необов'язково)",
        style=discord.TextStyle.short,
        placeholder="hex код: #FF5733 або назва: gold, red, blue",
        required=False,
        max_length=20
    )

    def __init__(self, message: discord.Message):
        super().__init__()
        self.message = message
        
        # Попереднє заповнення полів поточними значеннями
        if message.content:
            self.new_content.default = message.content
        
        if message.embeds:
            embed = message.embeds[0]
            if embed.title:
                self.embed_title.default = embed.title
            if embed.description:
                self.embed_description.default = embed.description

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Отримуємо нові значення
            new_text = self.new_content.value.strip() if self.new_content.value else None
            new_embed_title = self.embed_title.value.strip() if self.embed_title.value else None
            new_embed_desc = self.embed_description.value.strip() if self.embed_description.value else None
            color_value = self.embed_color.value.strip() if self.embed_color.value else None
            
            # Перевірка, чи щось змінено
            if not new_text and not new_embed_title and not new_embed_desc and not color_value:
                await interaction.response.send_message(
                    "❌ Заповніть хоча б одне поле для редагування!",
                    ephemeral=True
                )
                return
            
            # Створення нового embed якщо потрібно
            new_embed = None
            if new_embed_title or new_embed_desc or color_value:
                # Беремо старий embed як основу або створюємо новий
                if self.message.embeds:
                    old_embed = self.message.embeds[0]
                    new_embed = discord.Embed(
                        title=new_embed_title if new_embed_title else old_embed.title,
                        description=new_embed_desc if new_embed_desc else old_embed.description
                    )
                    # Зберігаємо footer та timestamp якщо були
                    if old_embed.footer:
                        new_embed.set_footer(text=old_embed.footer.text, icon_url=old_embed.footer.icon_url)
                    if old_embed.timestamp:
                        new_embed.timestamp = old_embed.timestamp
                else:
                    # Створюємо новий embed
                    new_embed = discord.Embed(
                        title=new_embed_title,
                        description=new_embed_desc
                    )
                
                # Обробка кольору
                if color_value:
                    new_embed.color = self._parse_color(color_value)
                elif self.message.embeds and self.message.embeds[0].color:
                    new_embed.color = self.message.embeds[0].color
                else:
                    new_embed.color = discord.Color.gold()
            elif self.message.embeds:
                # Якщо embed існує, але нові поля не заповнені - залишаємо старий
                new_embed = self.message.embeds[0]
            
            # Редагування повідомлення
            await self.message.edit(content=new_text, embed=new_embed)
            
            await interaction.response.send_message(
                f"✅ Повідомлення успішно відредаговано!\n[Перейти до повідомлення]({self.message.jump_url})",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Немає прав на редагування цього повідомлення!",
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Повідомлення не знайдено!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Помилка: {str(e)}",
                ephemeral=True
            )
    
    def _parse_color(self, color_str: str) -> discord.Color:
        """Парсинг кольору з різних форматів"""
        if not color_str:
            return discord.Color.gold()
        
        color_str = color_str.lower().strip()
        
        # Словник назв кольорів
        color_names = {
            'red': discord.Color.red(),
            'blue': discord.Color.blue(),
            'green': discord.Color.green(),
            'gold': discord.Color.gold(),
            'orange': discord.Color.orange(),
            'purple': discord.Color.purple(),
            'magenta': discord.Color.magenta(),
            'teal': discord.Color.teal(),
            'dark_blue': discord.Color.dark_blue(),
            'dark_green': discord.Color.dark_green(),
            'dark_red': discord.Color.dark_red(),
            'dark_gold': discord.Color.dark_gold(),
        }
        
        if color_str in color_names:
            return color_names[color_str]
        
        # Якщо це hex код
        try:
            hex_color = color_str.replace('#', '')
            return discord.Color(int(hex_color, 16))
        except (ValueError, TypeError):
            return discord.Color.gold()