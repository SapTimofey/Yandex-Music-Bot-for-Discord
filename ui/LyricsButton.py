import asyncio
import textwrap

import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers, client


class LyricsButton(Button):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(
            style=ButtonStyle.primary,
            label="Текст",
            emoji="🗒️",
            row=2,
            disabled=data_servers[interaction.guild.name]['lyrics'] is None
        )

    async def callback(self, interaction: discord.Interaction):
        data_servers[interaction.guild.name]['can_edit_message'] = False
        await asyncio.sleep(1)
        if self.style == ButtonStyle.success:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            async for message in interaction.channel.history():
                if message.author == client.user and message.content.startswith('Текст'):
                    await message.delete()
        else:
            self.style = ButtonStyle.success  # изменяем стиль кнопки на зеленый
            if len(data_servers[interaction.guild.name]['lyrics']) > 2000:
                parts = textwrap.wrap(
                    data_servers[interaction.guild.name]['lyrics'],
                    width=1800,
                    break_long_words=False,
                    replace_whitespace=False
                )
                await interaction.channel.send(f"Текст трека (часть 1):\n{parts[0]}")
                await interaction.channel.send(f"Текст трека (часть 2):\n{parts[1]}")
            else:
                await interaction.channel.send(f"Текст трека:\n{data_servers[interaction.guild.name]['lyrics']}")
        while True:
            try:
                await interaction.response.edit_message(view=self.view)
                break
            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
