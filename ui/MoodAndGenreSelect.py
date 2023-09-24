import discord
from discord import SelectOption
from discord.ui import Select

from global_variables import data_servers
from command_processing.play_yandex_music_radio import play_yandex_music_radio


class MoodAndGenreSelect(Select):
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        options = []
        interval = data_servers[interaction.guild.name]['mood_and_genre'][data_servers[interaction.guild.name]['mood_and_genre_page_index']]
        for item in interval:
            options.append(SelectOption(
                label=item.split(',')[2],
                value=item
            ))

        super().__init__(placeholder="Выберете жанр...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.interaction.edit_original_response(
            content=f'Загрузка Радио "{self.values[0].split(",")[2]}". Подождите',
            view=None
        )
        data_servers[interaction.guild.name]['radio_check'] = {
            "name": self.values[0].split(",")[2],
            "station": self.values[0].split(",")[0],
            "station_from": self.values[0].split(',')[1]
        }
        data_servers[interaction.guild.name]['stream_by_track_check'] = False
        data_servers[interaction.guild.name]['mood_and_genre'] = []
        await play_yandex_music_radio(
            interaction=interaction,
            station_id=self.values[0].split(',')[0],
            station_from=self.values[0].split(',')[1],
            first_track=True,
            new_task=True
        )
