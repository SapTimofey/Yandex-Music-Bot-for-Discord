import asyncio

import discord
from discord import SelectOption
from discord.ui import Select

from global_variables import data_servers


class AlbumListSelect(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[interaction.guild.name]['album_list'][data_servers[interaction.guild.name]['album_list_page_index']]
        for item in interval:
            if item.split(',')[3] == 'single':
                options.append(SelectOption(
                    label=item.split(',')[1],
                    value=item,
                    description=f"Количество треков: {item.split(',')[2]} - сингл"
                ))
            else:
                options.append(SelectOption(
                    label=item.split(',')[1],
                    value=item,
                    description=f"Количество треков: {item.split(',')[2]}"
                ))

        super().__init__(placeholder="Выберете альбом...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        from command_processing.play import play

        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content=f'Загрузка альбома "{self.values[0].split(",")[1]}". Подождите\n',
            view=None
        )
        data_servers[interaction.guild.name]['album_list'] = []
        data_servers[interaction.guild.name]['task'] = \
            asyncio.create_task(play(
                interaction=interaction,
                url_or_trackname_or_filepath=self.values[0].split(',')[0]
            ))
