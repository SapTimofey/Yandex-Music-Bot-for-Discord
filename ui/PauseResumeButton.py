import asyncio

import discord
from discord import ButtonStyle
from discord.ui import Button

from global_variables import data_servers


class PauseResumeButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.primary, label="Пауза/Продолжить", emoji="⏯️", row=1)

    async def callback(self, interaction: discord.Interaction):
        data_servers[interaction.guild.name]['can_edit_message'] = False
        voice_client = interaction.guild.voice_client
        if self.style == ButtonStyle.green:
            self.style = ButtonStyle.primary  # изменяем стиль кнопки на primary
            voice_client.resume()
        else:
            self.style = ButtonStyle.green  # изменяем стиль кнопки на зеленый
            voice_client.pause()
        while True:
            try:
                await interaction.response.edit_message(view=self.view)  # обновляем стиль кнопки
                break
            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                await asyncio.sleep(0.1)
        data_servers[interaction.guild.name]['can_edit_message'] = True
