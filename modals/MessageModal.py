import discord
from typing import Optional

# ---------- Message Type Select ----------
class MessageTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Звичайне повідомлення",
                value="normal",
                emoji="💬",
                description="Простий текст без форматування"
            ),
            discord.SelectOption(
                label="Embed повідомлення",
                value="embed",
                emoji="📋",
                description="Форматоване embed повідомлення"
            )
        ]
        super().__init__(
            placeholder="Оберіть тип повідомлення...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        message_type = self.values[0]
        
        if message_type == "normal":
            await interaction.response.send_modal(NormalMessageModal())
        else:
            modal = EmbedMessageModal()
            await interaction.response.send_modal(modal)


class MessageTypeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(MessageTypeSelect())


# ---------- Normal Message Modal ----------
class NormalMessageModal(discord.ui.Modal, title="💬 Звичайне повідомлення"):
    channel_id = discord.ui.TextInput(
        label="ID каналу",
        style=discord.TextStyle.short,
        placeholder="Вставте ID каналу (ПКМ → Копіювати ID)",
        required=True
    )
    
    message = discord.ui.TextInput(
        label="Текст повідомлення",
        style=discord.TextStyle.long,
        placeholder="Введіть текст з форматуванням Discord...",
        required=True,
        max_length=2000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value.strip())
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                await interaction.response.send_message(
                    "❌ Канал не знайдено! Перевірте ID.",
                    ephemeral=True
                )
                return
            
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "❌ Це не текстовий канал!",
                    ephemeral=True
                )
                return
            
            await channel.send(self.message.value)
            await interaction.response.send_message(
                f"✅ Повідомлення успішно відправлено в {channel.mention}",
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Невірний формат ID каналу!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Немає доступу до цього каналу!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Помилка: {str(e)}",
                ephemeral=True
            )


# ---------- Embed Message Modal ----------
class EmbedMessageModal(discord.ui.Modal, title="📋 Embed повідомлення"):
    channel_id = discord.ui.TextInput(
        label="ID каналу",
        style=discord.TextStyle.short,
        placeholder="Вставте ID каналу (ПКМ → Копіювати ID)",
        required=True
    )
    
    embed_title = discord.ui.TextInput(
        label="Заголовок",
        style=discord.TextStyle.short,
        placeholder="Заголовок embed",
        required=True,
        max_length=256
    )
    
    description = discord.ui.TextInput(
        label="Опис",
        style=discord.TextStyle.long,
        placeholder="Основний текст embed",
        required=True,
        max_length=4000
    )
    
    color = discord.ui.TextInput(
        label="Колір (hex)",
        style=discord.TextStyle.short,
        placeholder="Наприклад: #FF5733 або FF5733 (необов'язково)",
        required=False,
        max_length=7
    )
    
    footer = discord.ui.TextInput(
        label="Футер",
        style=discord.TextStyle.short,
        placeholder="Текст внизу embed (необов'язково)",
        required=False,
        max_length=2048
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value.strip())
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                await interaction.response.send_message(
                    "❌ Канал не знайдено! Перевірте ID.",
                    ephemeral=True
                )
                return
            
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "❌ Це не текстовий канал!",
                    ephemeral=True
                )
                return
            
            # Створення embed
            embed = discord.Embed(
                title=self.embed_title.value,
                description=self.description.value
            )
            
            # Додавання кольору
            if self.color.value and self.color.value.strip():
                color_hex = self.color.value.strip().replace('#', '')
                try:
                    embed.color = discord.Color(int(color_hex, 16))
                except ValueError:
                    embed.color = discord.Color.gold()  # Колір за замовчуванням при помилці
            else:
                embed.color = discord.Color.gold()  # Колір за замовчуванням
            
            # Додавання футера
            if self.footer.value and self.footer.value.strip():
                embed.set_footer(text=self.footer.value)
            
            # Додавання timestamp
            embed.timestamp = discord.utils.utcnow()
            
            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ Embed успішно відправлено в {channel.mention}",
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Невірний формат ID каналу!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Немає доступу до цього каналу!",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Помилка: {str(e)}",
                ephemeral=True
            )

# ---------- Universal Message Modal ----------
class UniversalMessageModal(discord.ui.Modal, title="📨 Створити повідомлення"):
    channel_id = discord.ui.TextInput(
        label="ID каналу",
        style=discord.TextStyle.short,
        placeholder="Вставте ID каналу (ПКМ → Копіювати ID)",
        required=True
    )
    
    normal_text = discord.ui.TextInput(
        label="Звичайний текст (необов'язково)",
        style=discord.TextStyle.long,
        placeholder="Текст повідомлення перед embed або просто повідомлення",
        required=False,
        max_length=2000
    )
    
    embed_title = discord.ui.TextInput(
        label="Заголовок Embed (необов'язково)",
        style=discord.TextStyle.short,
        placeholder="Якщо заповнити - створить embed",
        required=False,
        max_length=256
    )
    
    embed_description = discord.ui.TextInput(
        label="Опис Embed (необов'язково)",
        style=discord.TextStyle.long,
        placeholder="Основний текст embed",
        required=False,
        max_length=4000
    )
    
    # embed_color = discord.ui.TextInput(
    #     label="Колір Embed (необов'язково)",
    #     style=discord.TextStyle.short,
    #     placeholder="hex код: #FF5733 або gold, red, blue",
    #     required=False,
    #     max_length=20
    # )

    thread_or_color = discord.ui.TextInput(
        label="Назва поста (форум) або Колір (канал)",
        style=discord.TextStyle.short,
        placeholder="Для форуму - назва поста, для каналу - gold/#FF5733",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Отримання каналу
            channel_id = int(self.channel_id.value.strip())
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                channel = interaction.guild.get_thread(channel_id)

            if not channel:
                await interaction.response.send_message(
                    "❌ Канал не знайдено! Перевірте ID.",
                    ephemeral=True
                )
                return
            
            if not isinstance(channel, (discord.TextChannel, discord.ForumChannel, discord.Thread)):
                await interaction.response.send_message(
                    "❌ Це не текстовий канал!",
                    ephemeral=True
                )
                return
            
            # Перевірка, що заповнено
            has_normal_text = self.normal_text.value and self.normal_text.value.strip()
            has_embed_title = self.embed_title.value and self.embed_title.value.strip()
            has_embed_desc = self.embed_description.value and self.embed_description.value.strip()
            
            # Якщо нічого не заповнено
            if not has_normal_text and not has_embed_title and not has_embed_desc:
                await interaction.response.send_message(
                    "❌ Заповніть хоча б одне поле з текстом!",
                    ephemeral=True
                )
                return
            
            # Визначаємо, що це: назва поста чи колір
            is_forum = isinstance(channel, discord.ForumChannel)
            thread_or_color_value = self.thread_or_color.value.strip() if self.thread_or_color.value else ""
            
            # Створення embed якщо є заголовок або опис
            embed = None
            if has_embed_title or has_embed_desc:
                embed = discord.Embed()
                
                if has_embed_title:
                    embed.title = self.embed_title.value
                
                if has_embed_desc:
                    embed.description = self.embed_description.value
                
                # Обробка кольору
                # color_value = self.embed_color.value.strip() if self.embed_color.value else ""
                # embed.color = self._parse_color(color_value)
                if is_forum:
                    embed.color = discord.Color.gold()
                else:
                    embed.color = self._parse_color(thread_or_color_value)
                
                # Timestamp
                # embed.timestamp = discord.utils.utcnow()
            
            # Відправка повідомлення
            content = self.normal_text.value if has_normal_text else None
            target_mention = None

            # await channel.send(content=content, embed=embed)\

            # ForumChannel -> створити пост (forum thread)
            if isinstance(channel, discord.ForumChannel):
                post_name = thread_or_color_value if thread_or_color_value else (
                    self.embed_title.value if has_embed_title else "Нове повідомлення"
                )

                # create_thread для ForumChannel повертає tuple (thread, message)
                thread, message = await channel.create_thread(
                    name=post_name,
                    content=content,
                    embed=embed
                )
                target_mention = thread.mention

                # try:
                #     post = await channel.create_post(name=post_name, content=content, embed=embed)
                #     # create_post повертає Message або ForumPost — намагаймось отримати mention
                #     target_mention = post.thread.mention
                # except AttributeError:
                #     # Якщо create_post відсутній у версії бібліотеки — fallback на звичайну відправку
                #     msg = await channel.send(content=content, embed=embed)
                #     target_mention = msg.channel.mention

            # TextChannel -> або створити новий тред всередині каналу, або просто відправити
            elif isinstance(channel, discord.TextChannel):
                await channel.send(content=content, embed=embed)
                target_mention = channel.mention

            # Thread -> просто відправити в існуючий тред
            elif isinstance(channel, discord.Thread):
                await channel.send(content=content, embed=embed)
                target_mention = channel.mention
            
            # Повідомлення про успіх
            msg_type = []
            if has_normal_text:
                msg_type.append("текст")
            if embed:
                msg_type.append("embed")
            
            await interaction.response.send_message(
                f"✅ Повідомлення ({' + '.join(msg_type)}) успішно відправлено в {target_mention}",
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Невірний формат ID каналу!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Немає доступу до цього каналу!",
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
        
        # Якщо це назва кольору
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
            return discord.Color.gold()  # За замовчуванням