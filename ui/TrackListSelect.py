import asyncio

import discord
from discord import SelectOption
from discord.ui import Select

from global_variables import data_servers
from command_processing.remove_last_playing_message import remove_last_playing_message


class TrackListSelect(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[
            interaction.guild.name]['track_list'][data_servers[interaction.guild.name]['track_list_page_index']]
        for item in interval:
            options.append(SelectOption(
                label=f"{item[1]} - {item[2]}",
                value=f"{item[0]},{item[1]}",
                description=item[3])
            )

        super().__init__(placeholder="Выберете трек...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content="Загрузка трека. Подождите",
            view=None
        )
        if data_servers[interaction.guild.name]['random']:
            for i in range(len(data_servers[interaction.guild.name]['playlist'])):
                if data_servers[interaction.guild.name]['playlist'][i][1] == int(self.values[0].split(',')[1]):
                    data_servers[interaction.guild.name]['index_play_now'] = i - 1
                    break
        else:
            data_servers[interaction.guild.name]['index_play_now'] = int(self.values[0].split(',')[0]) - 1
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await remove_last_playing_message(interaction)
        while not voice_client.is_playing():
            await asyncio.sleep(0.1)
        await self.interaction.delete_original_response()
