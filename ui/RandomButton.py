import asyncio
import random

import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers


class RandomButton(Button):
    def __init__(self, interaction: discord.Interaction):
        if data_servers[interaction.guild.name]['radio_check'] or data_servers[interaction.guild.name]['stream_by_track_check']:
            data_servers[interaction.guild.name]['random'] = False
            super().__init__(style=ButtonStyle.primary, label="Случайный порядок", emoji="🔀", row=2, disabled=True)
        else:
            if data_servers[interaction.guild.name]['random']:
                super().__init__(style=ButtonStyle.green, label="Случайный порядок", emoji="🔀", row=2)
            else:
                super().__init__(style=ButtonStyle.primary, label="Случайный порядок", emoji="🔀", row=2)

    async def callback(self, interaction: discord.Interaction):
        data_servers[interaction.guild.name]['can_edit_message'] = False
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            data_servers[interaction.guild.name]['playlist'] = data_servers[interaction.guild.name]['playlist_reserve']
            data_servers[interaction.guild.name]['random'] = False
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            random.shuffle(data_servers[interaction.guild.name]['playlist'])
            data_servers[interaction.guild.name]['random'] = True
        while True:
            try:
                await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
                break
            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
